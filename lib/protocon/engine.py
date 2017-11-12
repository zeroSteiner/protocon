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
import sys
import time
import traceback

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

		self.io_history = self.IOHistory(rx=collections.deque(), tx=collections.deque())
		super(Engine, self).__init__(use_ipython=True)
		self.pgood("initialized protocon engine v{0} at {1:%Y-%m-%d %H:%M:%S}".format(__version__, datetime.datetime.now()))
		self.pgood('connected to: ' + connection.url.to_text())

	def _crc_string(self, data):
		algo = getattr(crcelk, self.crc_algorithm)
		return "0x{value:0{width:}x}".format(value=algo.calc_bytes(data), width=algo.width // 4)

	def _process_send(self, data):
		self.io_history.tx.append(data)
		self.pstatus("TX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.print_tx:
			return
		color.print_hexdump(data)

	def _process_recv(self, data):
		self.io_history.rx.append(data)
		self.pstatus("RX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if not self.print_rx:
			return
		color.print_hexdump(data)

	def do_close(self, arguments):
		self.connection.close()
		self.pstatus('the connection has been closed')
		return False

	def do_recv_size(self, arguments):
		size = ast.literal_eval(arguments) if arguments else None
		if not isinstance(size, int):
			self.pwarning('command error: recv-size must specify a valid size')
			return False
		self._process_recv(self.connection.recv_size(size))
		return False

	def do_recv_time(self, arguments):
		timeout = ast.literal_eval(arguments) if arguments else None
		if not isinstance(timeout, (float, int)):
			self.pwarning('command error: recv-time must specify a valid timeout')
			return False
		self._process_recv(self.connection.recv_timeout(timeout))
		return False

	def do_recv_until(self, arguments):
		terminator = self.decode(arguments)
		if not terminator:
			self.pwarning('command error: recv-until must specify a valid terminator')
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
			self.pwarning('command error: sleep must specify a valid duration')
			return False
		time.sleep(duration)
		return False

	def decode(self, data, encoding=None):
		encoding = encoding or self.encoding
		return conversion.decode(data, encoding)

	def perror(self, errmsg, exception_type=None, traceback_war=True):
		if self.debug:
			traceback.print_exc()

		if exception_type is None:
			errmsg = 'ERROR: ' + errmsg + '\n'
			if self.colors:
				errmsg = color.PREFIX_ERROR + errmsg
			else:
				errmsg = color.PREFIX_ERROR_RAW + errmsg
			sys.stderr.write(errmsg)
		else:
			errmsg = "EXCEPTION of type '{}' occurred with message: '{}'\n".format(exception_type, errmsg)
			if self.colors:
				errmsg = color.PREFIX_ERROR + errmsg
			else:
				errmsg = color.PREFIX_ERROR_RAW + errmsg
			sys.stderr.write(errmsg)

		if traceback_war:
			warning = 'To enable full traceback, run the following command:  \'set debug true\'\n'
			if self.colors:
				warning = color.PREFIX_WARNING + warning
			else:
				warning = color.PREFIX_WARNING_RAW + warning
			sys.stderr.write(warning)

	def pfeedback(self, msg):
		if self.quiet:
			return
		if self.feedback_to_output:
			msg = (color.PREFIX_STATUS if self.colors else color.PREFIX_STATUS_RAW) + msg
			self.poutput(msg)
		else:
			msg = color.PREFIX_STATUS_RAW + msg
			sys.stderr.write("{}\n".format(msg))

	def pgood(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_GOOD + msg
		else:
			msg = color.PREFIX_GOOD_RAW + msg
		super(Engine, self).poutput(msg, end=end)

	def pstatus(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_STATUS + msg
		else:
			msg = color.PREFIX_STATUS_RAW + msg
		super(Engine, self).poutput(msg, end=end)

	def pwarning(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_WARNING + msg
		else:
			msg = color.PREFIX_WARNING_RAW + msg
		super(Engine, self).poutput(msg, end=end)
