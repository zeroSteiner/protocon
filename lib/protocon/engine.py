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

import cmd2
import crcelk

from . import __version__
from . import color
from . import conversion

class Engine(cmd2.Cmd):
	IOHistory = collections.namedtuple('IOHistory', ('rx', 'tx'))
	allow_cli_args = False
	prompt = 'pro > '
	def __init__(self, connection):
		self.connection = connection
		# variables
		self.crc_algorithm = 'CRC_CCITT'
		self.encoding = 'utf-8'
		self.print_rx = True
		self.print_tx = True
		self.settable.update({
			'crc_algorithm': 'The CRC algorithm to use.',
			'encoding': 'The data encoding to use.',
			'print_rx': 'Print received data.',
			'print_tx': 'Print sent data.'
		})

		color.print_good("initialized protocon engine v{0} at {1:%Y-%m-%d %H:%M:%S}".format(__version__, datetime.datetime.now()))
		color.print_good('connected to: ' + connection.url.to_text())
		self.io_history = self.IOHistory(rx=collections.deque(), tx=collections.deque())
		super(Engine, self).__init__(use_ipython=True)

	def _crc_string(self, data):
		algo = getattr(crcelk, self.crc_algorithm)
		return "0x{value:0{width:}x}".format(value=algo.calc_bytes(data), width=algo.width // 4)

	def _process_send(self, data):
		self.io_history.tx.append(data)
		color.print_status("TX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.print_tx:
			return
		color.print_hexdump(data)

	def _process_recv(self, data):
		self.io_history.rx.append(data)
		color.print_status("RX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.print_rx:
			return
		color.print_hexdump(data)

	def do_close(self, arguments):
		self.connection.close()
		color.print_status('the connection has been closed')
		return False

	def do_print_error(self, arguments):
		color.print_error(arguments)
		return False

	def do_print_good(self, arguments):
		color.print_error(arguments)
		return False

	def do_print_status(self, arguments):
		color.print_status(arguments)
		return False

	def do_recv_size(self, arguments):
		size = ast.literal_eval(arguments) if arguments else None
		if not isinstance(size, int):
			color.print_error('command error: recv-size must specify a valid size')
			return False
		self._process_recv(self.connection.recv_size(size))
		return False

	def do_recv_time(self, arguments):
		timeout = ast.literal_eval(arguments) if arguments else None
		if not isinstance(timeout, (float, int)):
			color.print_error('command error: recv-time must specify a valid timeout')
			return False
		self._process_recv(self.connection.recv_timeout(timeout))
		return False

	def do_recv_until(self, arguments):
		terminator = self.decode(arguments)
		if not terminator:
			color.print_error('command error: recv-until must specify a valid terminator')
			return False
		self._process_recv(self.connection.recv_until(terminator))

	def do_send(self, arguments):
		data = self.decode(arguments)
		self.connection.send(data)
		self._process_send(data)
		return False

	def do_sleep(self, arguments):
		duration = ast.literal_eval(arguments) if arguments else None
		if not isinstance(duration, (float, int)):
			color.print_error('command error: sleep must specify a valid duration')
			return False
		time.sleep(duration)
		return False

	def decode(self, data, encoding=None):
		encoding = encoding or self.encoding
		return conversion.decode(data, encoding)
