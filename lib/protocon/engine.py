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

import boltons.iterutils
import boltons.urlutils
import crcelk
import termcolor

from . import __version__
from . import connection_driver

def print_hexdump(data, base=0, stream=None, encoding='utf-8'):
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

class Engine(object):
	comment = '#'
	_History = collections.namedtuple('History', ('command', 'rx', 'tx'))
	def __init__(self, connection):
		self.connection = connection
		self.variables = {
			'crc': 'CRC_CCITT',
			'encoding': 'hex',
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
			return None
		self._process_recv(self.connection.recv_until(terminator))

	def _cmd_send(self, arguments):
		data = self.decode(arguments)
		self.connection.send(data)
		self._process_send(data)
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

	def decode(self, data, encoding=None):
		encoding = encoding or self.variables['encoding']
		encoding = encoding.lower()
		if encoding in ('utf-8', 'utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le'):
			data = data.encode(encoding)
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
