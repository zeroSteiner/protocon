#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/engine.py
#
#  Copyright 2017 Spencer McIntyre <zeroSteiner@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import ast
import binascii
import collections
import datetime
import os
import re
import sys
import time

import boltons.iterutils
import boltons.urlutils
import crcelk
import termcolor

from . import __version__
from . import connection_driver

def print_hexdump(data, stream=None, encoding='utf-8'):
	if not stream:
		stream = sys.stdout
	if isinstance(data, str):
		data = data.encode(encoding)
	data = bytearray(data)
	l = len(data)
	i = 0
	divider = 8
	chunk_size = 16
	for row, chunk in enumerate(boltons.iterutils.chunked(data, chunk_size, fill=-1)):
		offset_col = "{0:04x}".format(row * chunk_size)
		hex_col = ''
		for pos, byte in enumerate(chunk):
			hex_col += '   ' if byte == -1 else "{0:02x} ".format(byte)
			if pos and pos % divider == 0:
				hex_col += ' '
		hex_col = hex_col[:-1]
		ascii_col = ''
		for byte in chunk:
			if byte == -1:
				ascii_col += ' '
			elif byte < 32 or byte > 126:
				ascii_col += '.'
			else:
				ascii_col += chr(byte)
		stream.write('  '.join((offset_col, hex_col, ascii_col)) + os.linesep)
	stream.flush()

def print_error(message, *args, **kwargs):
	message = termcolor.colored('[-] ', 'red', attrs=('bold',)) + message
	print(message, *args, **kwargs)

def print_good(message, *args, **kwargs):
	message = termcolor.colored('[+] ', 'green', attrs=('bold',)) + message
	print(message, *args, **kwargs)

def print_status(message, *args, **kwargs):
	message = termcolor.colored('[*] ', 'blue', attrs=('bold',)) + message
	print(message, *args, **kwargs)

def _decodestr_repl(match):
	match = match.group(1)
	if match == b'n':
		return b'\n'
	elif match == b'r':
		return b'\r'
	elif match == b't':
		return b'\t'
	elif match[0] == 'x':
		return bytes.fromhex(match[1:3])
	raise ValueError('unknown escape sequence: ' + match)

class Engine(object):
	comment = '#'
	_History = collections.namedtuple('History', ('command', 'rx', 'tx'))
	def __init__(self, connection):
		self.connection = connection
		self.variables = {
			'crc': 'CRC_CCITT',
			'encoding': 'utf-8',
			'print-recv': True,
			'print-send': True
		}
		print_good("initialized protocon engine v{0} at {1:%Y-%m-%d %H:%M:%S}".format(__version__, datetime.datetime.now()))
		print_good('connected to: ' + connection.url.to_text())
		self.history = self._History(command=collections.deque(), rx=collections.deque(), tx=collections.deque())

	def _cmd_close(self, arguments):
		self.connection.close()
		print_status('the connection has been closed')
		return True

	def _cmd_print_error(self, arguments):
		print_error(arguments)
		return True

	def _cmd_print_good(self, arguments):
		print_error(arguments)
		return True

	def _cmd_print_status(self, arguments):
		print_status(arguments)
		return True

	def _cmd_recv_size(self, arguments):
		size = ast.literal_eval(arguments) if arguments else None
		if not isinstance(size, int):
			print_error('command error: recv-size must specify a valid size')
			return False
		self._process_recv(self.connection.recv_size(size))
		return True

	def _cmd_recv_time(self, arguments):
		timeout = ast.literal_eval(arguments) if arguments else None
		if not isinstance(timeout, (float, int)):
			print_error('command error: recv-time must specify a valid timeout')
			return False
		self._process_recv(self.connection.recv_timeout(timeout))
		return True

	def _cmd_recv_until(self, arguments):
		terminator = self.decode(arguments)
		if not terminator:
			print_error('command error: recv-until must specify a valid terminator')
			return False
		self._process_recv(self.connection.recv_until(terminator))

	def _cmd_send(self, arguments):
		data = self.decode(arguments)
		self.connection.send(data)
		self._process_send(data)
		return True

	def _cmd_set(self, arguments):
		if not arguments:
			print_error('command error: set must specify a valid option to configure')
			return False
		if '=' not in arguments:
			print_error('command error: set must specify a valid option in the format of name=value')
			return False
		name, value = arguments.split('=', 1)
		name = name.strip()
		value = value.strip()
		handler = getattr(self, '_set_' + name.replace('-', '_'), None)
		if handler is None:
			print_error('command error: set must specify a valid option')
			return False

		if value.lower() == 'false':
			value = False
		elif value.lower() == 'null':
			value = None
		elif value.lower() == 'true':
			value = True
		elif re.match(r'^0b[01]+$', value):
			value = int(value[2:], 2)
		elif re.match(r'^0o[0-7]+$', value):
			value = int(value[2:], 8)
		elif re.match(r'^0x[a-fA-F0-9]+$', value):
			value = int(value[2:], 16)
		elif re.match(r'^[0-9]+$', value):
			value = int(value, 10)
		return handler(value)

	def _cmd_sleep(self, arguments):
		duration = ast.literal_eval(arguments) if arguments else None
		if not isinstance(duration, (float, int)):
			print_error('command error: sleep must specify a valid duration')
			return False
		time.sleep(duration)
		return True

	def _crc_string(self, data):
		algo = getattr(crcelk, self.variables['crc'])
		return "0x{value:0{width:}x}".format(value=algo.calc_bytes(data), width=algo.width // 4)

	def _process_send(self, data):
		self.history.tx.append(data)
		print_status("TX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.variables['print-send']:
			return
		print_hexdump(data)

	def _process_recv(self, data):
		self.history.rx.append(data)
		print_status("RX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.variables['print-recv']:
			return
		print_hexdump(data)

	def _set_crc(self, value):
		if not isinstance(value, str):
			print_error('value error: crc must be a string')
			return False
		self.variables['crc'] = value
		return True

	def _set_encoding(self, value):
		if not isinstance(value, str):
			print_error('value error: encoding must be a string')
			return False
		self.variables['encoding'] = value
		return True

	def _set_print_recv(self, value):
		if not isinstance(value, bool):
			print_error('value error: print-recv must be a boolean')
			return False
		self.variables['print-recv'] = value
		return True

	def _set_print_send(self, value):
		if not isinstance(value, bool):
			print_error('value error: print-send must be a boolean')
			return False
		self.variables['print-send'] = value
		return True

	@property
	def commands(self):
		return tuple(sorted(cmd[5:].replace('_', '-') for cmd in dir(self) if cmd.startswith('_cmd_')))

	def decode(self, data, encoding=None):
		encoding = encoding or self.variables['encoding']

		encoding = encoding.lower()
		if encoding in ('utf-8', 'utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le'):
			data = data.encode(encoding)
			regex = br'(?<!\\)(?:\\\\)*\\([nrt]|x[0-9a-f][0-9a-f])'
			data = re.sub(regex, _decodestr_repl, data)
		elif encoding == 'hex':
			if len(data) > 2 and re.match(r'^[a-f0-9]{2}[^a-f0-9]', data):
				data = data.replace(data[3], '')
			data = binascii.a2b_hex(data)
		else:
			raise ValueError('unsupported encoding: ' + encoding)
		return data

	@classmethod
	def from_url(cls, url, *args, **kwargs):
		connection = connection_driver.ConnectionDriver(url)
		return cls(connection, *args, **kwargs)

	def run_command(self, command):
		command = command.strip()
		if command.startswith(self.comment):
			return True
		original_command = command
		command, argument = command.split(':', 1)
		command = command.strip().lower()
		handler = getattr(self, '_cmd_' + command.replace('-', '_'), None)
		if handler is None:
			print_error('unknown command: ' + command)
			return False
		result = handler(argument.strip())
		if result:
			self.history.command.append(original_command)
		return result
