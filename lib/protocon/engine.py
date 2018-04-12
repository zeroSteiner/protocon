#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/engine.py
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the project nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import argparse
import ast
import collections
import datetime
import functools
import sys
import textwrap
import time
import traceback
import weakref

import cmd2
import crcelk
import hyperlink

from . import __version__
from . import color
from . import conversion
from . import errors
from . import plugin_manager

cmd2.set_posix_shlex(True)

# this class includes both cmd2 style p* and generic style print_* methods for
# compatibility with cmd2.Cmd and the ConnectionDriver interface
class Engine(cmd2.Cmd):
	IOHistory = collections.namedtuple('IOHistory', ('rx', 'tx'))
	allow_cli_args = False
	prompt = 'pro > '
	def __init__(self, connection, plugins=None, quiet=False, **kwargs):
		self.exclude_from_help = ['do_eof', 'do_eos', 'do_quit']
		self.connection = connection
		if plugins is None:
			plugins = plugin_manager.PluginManager()
		elif not isinstance(plugins, plugin_manager.PluginManager):
			raise TypeError('plugins must be an instance of PluginManager')
		self.plugins = plugins
		# variables
		self.feedback_to_output = True
		self.crc_algorithm = 'CRC16'
		self.encoding = 'utf-8'
		self.print_rx = True
		self.print_tx = True
		self.settable.update({
			'crc_algorithm': 'The CRC algorithm to use',
			'encoding': 'The data encoding to use',
			'print_rx': 'Print received data',
			'print_tx': 'Print sent data'
		})

		self.io_history = self.IOHistory(rx=collections.deque(), tx=collections.deque())
		self.quiet = quiet

		self._onchange_crc_algorithm = functools.partial(
			self._set_enumeration,
			'crc_algorithm',
			('CRC15', 'CRC16', 'CRC16_USB', 'CRC24', 'CRC32', 'CRC_CCITT', 'CRC_HDLC', 'CRC_XMODEM')
		)
		self._onchange_encoding = functools.partial(self._set_enumeration, 'encoding', conversion.ENCODINGS)

		super(Engine, self).__init__(use_ipython=True, **kwargs)
		self.exclude_from_help.append('do__relative_load')
		self.pgood("Initialized protocon engine v{0} at {1:%Y-%m-%d %H:%M:%S}".format(__version__, datetime.datetime.now()))

		self.connection.print_driver = weakref.proxy(self)
		if not self.connection.connected:
			self.connection.open()
		self.pgood('Successfully opened connection URL: ' + self.connection.url.to_text())

	def _set_enumeration(self, name, choices, old=None, new=None):
		if new in choices:
			setattr(self, name, new)
			return
		setattr(self, name, old)
		self.perror("Invalid value: {0!r} for option: {1}, choose one of:".format(new, name), traceback_war=False)
		prefix = (color.PREFIX_ERROR if self.colors else color.PREFIX_ERROR_RAW) + '       '
		for choice_line in textwrap.wrap(', '.join(choices), 69):
			sys.stderr.write(prefix + choice_line + '\n')

	def _crc_string(self, data):
		algo = getattr(crcelk, self.crc_algorithm)
		return "0x{value:0{width:}x}".format(value=algo.calc_bytes(data), width=algo.width // 4)

	def _post_recv(self, data, opts=None):
		self.io_history.rx.append(data)
		self.pstatus("RX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if self.print_rx:
			color.print_hexdump(data)

		if opts and opts.file:
			with open(opts.file, 'wb') as file_h:
				file_h.write(data)

	def _post_send(self, data):
		self.io_history.tx.append(data)
		self.pstatus("TX: {0: 6} bytes (CRC: {1})".format(len(data), self._crc_string(data)))
		if self.print_tx:
			color.print_hexdump(data)

	def _pre_send(self, data):
		return data

	@classmethod
	def from_url(cls, url, plugins=None, **kwargs):
		if plugins is None:
			plugins = plugin_manager.PluginManager()
		elif not isinstance(plugins, plugin_manager.PluginManager):
			raise TypeError('plugins must be an instance of PluginManager')

		if isinstance(url, str):
			url = hyperlink.URL.from_text(url)
		color.print_status("Loaded {0:,} connection drivers".format(len(plugins.connection_drivers)))
		if plugins.transcoders:
			color.print_status("Loaded {0:,} transcode drivers".format(len(plugins.transcoders)))
		driver = next((driver for driver in plugins.connection_drivers.values() if url.scheme in driver.schemes), None)
		if driver is None:
			raise errors.ProtoconDriverError('no connection driver for scheme: ' + url.scheme)

		driver = driver(url)
		return cls(driver, plugins=plugins, **kwargs)

	def entry(self, scripts=()):
		"""
		Run each of the protocon scripts specified in *scripts* and then enter
		:py:meth:`.cmdloop` unless the engine is set to exit.
		"""
		for script in scripts:
			if self.do_load(script):
				break
		else:
			self.cmdloop()

	def do_close(self, opts):
		"""Close the connection."""
		self.connection.close()
		self.pstatus('The connection has been closed')
		return True

	def do_exit(self, arg):
		"""Exit the protocon engine."""
		return super(Engine, self).do_quit(arg)

	argparser = argparse.ArgumentParser()
	argparser.add_argument('-f', '--file', help='write the received data to the file')
	argparser.add_argument('-t', '--timeout', type=int, help='the timeout for the operation')
	argparser.add_argument('size', help='the number of bytes to receive')
	@cmd2.with_argparser(argparser)
	def do_recv_size(self, opts):
		"""Receive the specified number of bytes from the endpoint."""
		size = conversion.eval_token(opts.size)
		if not isinstance(size, int):
			self.pwarning('Command Error: recv_size must specify a valid size')
			return False
		self._post_recv(self.connection.recv_size(size, timeout=opts.timeout), opts)
		return False

	argparser = argparse.ArgumentParser()
	argparser.add_argument('-f', '--file', help='write the received data to the file')
	argparser.add_argument('time', help='the amount of time in seconds to receive data for')
	@cmd2.with_argparser(argparser)
	def do_recv_time(self, opts):
		"""Receive data for the specified amount of seconds."""
		timeout = conversion.eval_token(opts.time)
		if not isinstance(timeout, (float, int)):
			self.pwarning('Command Error: recv_time must specify a valid timeout')
			return False
		self._post_recv(self.connection.recv_timeout(timeout), opts)
		return False

	argparser = argparse.ArgumentParser()
	argparser.add_argument('-f', '--file', help='write the received data to the file')
	argparser.add_argument('-t', '--timeout', type=int, help='the timeout for the operation')
	argparser.add_argument('terminator', help='the byte sequence to receive data until')
	@cmd2.with_argparser(argparser)
	def do_recv_until(self, opts):
		"""Receive data until the specified terminator is received."""
		terminator = self.decode(opts.terminator)
		if not terminator:
			self.pwarning('Command Error: recv_until must specify a valid terminator')
			return False
		self._post_recv(self.connection.recv_until(terminator, timeout=opts.timeout), opts)
		return False

	argparser = argparse.ArgumentParser()
	argparser.add_argument('data', help='the data to send to the remote end')
	@cmd2.with_argparser(argparser)
	def do_send(self, opts):
		"""Send the specified data."""
		data = self.decode(opts.data)
		data = self._pre_send(data)
		self.connection.send(data)
		self._post_send(data)
		return False

	def do_sleep(self, arguments):
		"""Sleep for the specified duration in seconds.\nUsage:  sleep <time>"""
		duration = ast.literal_eval(arguments) if arguments else None
		if not isinstance(duration, (float, int)):
			self.pwarning('Command Error: sleep must specify a valid duration')
			return False
		time.sleep(duration)
		return False

	def decode(self, string, encoding=None):
		username, _, password = self.connection.url.userinfo.partition(':')
		variables = {
			'url.host': self.connection.url.host,
			'url.password': password,
			'url.port': str(self.connection.url.port or ''),
			'url.scheme': self.connection.url.scheme,
			'url.username': username,
		}
		encoding = encoding or self.encoding
		string = conversion.expand(string, variables=variables, encoding=encoding)
		return conversion.decode(string, encoding=encoding)

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
			errmsg = ["EXCEPTION of type '{}' occurred with message:".format(exception_type), getattr(errmsg, 'message', repr(errmsg))]
			if self.colors:
				errmsg = ''.join((color.PREFIX_ERROR + line + '\n' for line in errmsg))
			else:
				errmsg = ''.join((color.PREFIX_ERROR_RAW + line + '\n' for line in errmsg))
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

	def postcmd(self, stop, line):
		if stop:
			return True
		if not self.connection.connected:
			self.print_error('The remote end has closed the connection')
			return True
		return False

	def print_error(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_ERROR + msg
		else:
			msg = color.PREFIX_ERROR_RAW + msg
		super(Engine, self).poutput(msg, end=end)

	def print_good(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_GOOD + msg
		else:
			msg = color.PREFIX_GOOD_RAW + msg
		super(Engine, self).poutput(msg, end=end)
	pgood = print_good

	def print_status(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_STATUS + msg
		else:
			msg = color.PREFIX_STATUS_RAW + msg
		super(Engine, self).poutput(msg, end=end)
	pstatus = print_status

	def print_warning(self, msg, end='\n'):
		if self.colors:
			msg = color.PREFIX_WARNING + msg
		else:
			msg = color.PREFIX_WARNING_RAW + msg
		super(Engine, self).poutput(msg, end=end)
	pwarning = print_warning
