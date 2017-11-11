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
import collections
import datetime
import time

import crcelk

from . import __version__
from . import color
from . import connection_driver
from . import conversion

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
		color.print_good("initialized protocon engine v{0} at {1:%Y-%m-%d %H:%M:%S}".format(__version__, datetime.datetime.now()))
		color.print_good('connected to: ' + connection.url.to_text())
		self.history = self._History(command=collections.deque(), rx=collections.deque(), tx=collections.deque())

	def _cmd_close(self, arguments):
		self.connection.close()
		color.print_status('the connection has been closed')
		return True

	def _cmd_print_error(self, arguments):
		color.print_error(arguments)
		return True

	def _cmd_print_good(self, arguments):
		color.print_error(arguments)
		return True

	def _cmd_print_status(self, arguments):
		color.print_status(arguments)
		return True

	def _cmd_recv_size(self, arguments):
		size = ast.literal_eval(arguments) if arguments else None
		if not isinstance(size, int):
			color.print_error('command error: recv-size must specify a valid size')
			return False
		self._process_recv(self.connection.recv_size(size))
		return True

	def _cmd_recv_time(self, arguments):
		timeout = ast.literal_eval(arguments) if arguments else None
		if not isinstance(timeout, (float, int)):
			color.print_error('command error: recv-time must specify a valid timeout')
			return False
		self._process_recv(self.connection.recv_timeout(timeout))
		return True

	def _cmd_recv_until(self, arguments):
		terminator = self.decode(arguments)
		if not terminator:
			color.print_error('command error: recv-until must specify a valid terminator')
			return False
		self._process_recv(self.connection.recv_until(terminator))

	def _cmd_send(self, arguments):
		data = self.decode(arguments)
		self.connection.send(data)
		self._process_send(data)
		return True

	def _cmd_set(self, arguments):
		if not arguments:
			color.print_error('command error: set must specify a valid option to configure')
			return False
		if '=' not in arguments:
			color.print_error('command error: set must specify a valid option in the format of name=value')
			return False
		name, value = arguments.split('=', 1)
		name = name.strip()
		value = value.strip()
		handler = getattr(self, '_set_' + name.replace('-', '_'), None)
		if handler is None:
			color.print_error('command error: set must specify a valid option')
			return False

		value = conversion.eval_token(value)
		return handler(value)

	def _cmd_sleep(self, arguments):
		duration = ast.literal_eval(arguments) if arguments else None
		if not isinstance(duration, (float, int)):
			color.print_error('command error: sleep must specify a valid duration')
			return False
		time.sleep(duration)
		return True

	def _crc_string(self, data):
		algo = getattr(crcelk, self.variables['crc'])
		return "0x{value:0{width:}x}".format(value=algo.calc_bytes(data), width=algo.width // 4)

	def _process_send(self, data):
		self.history.tx.append(data)
		color.print_status("TX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.variables['print-send']:
			return
		color.print_hexdump(data)

	def _process_recv(self, data):
		self.history.rx.append(data)
		color.print_status("RX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.variables['print-recv']:
			return
		color.print_hexdump(data)

	def _set_crc(self, value):
		if not isinstance(value, str):
			color.print_error('value error: crc must be a string')
			return False
		self.variables['crc'] = value
		return True

	def _set_encoding(self, value):
		if not isinstance(value, str):
			color.print_error('value error: encoding must be a string')
			return False
		self.variables['encoding'] = value
		return True

	def _set_print_recv(self, value):
		if not isinstance(value, bool):
			color.print_error('value error: print-recv must be a boolean')
			return False
		self.variables['print-recv'] = value
		return True

	def _set_print_send(self, value):
		if not isinstance(value, bool):
			color.print_error('value error: print-send must be a boolean')
			return False
		self.variables['print-send'] = value
		return True

	@property
	def commands(self):
		return tuple(sorted(cmd[5:].replace('_', '-') for cmd in dir(self) if cmd.startswith('_cmd_')))

	def decode(self, data, encoding=None):
		encoding = encoding or self.variables['encoding']
		return conversion.decode(data, encoding)

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
			color.print_error('unknown command: ' + command)
			return False
		result = handler(argument.strip())
		if result:
			self.history.command.append(original_command)
		return result
