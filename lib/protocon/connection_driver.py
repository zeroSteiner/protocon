#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/connection_driver.py
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

import select

from . import color
from . import errors

_inf = float('inf')

def _remaining(data, terminator):
	# get the minimum number of bytes that must be read to ensure that data
	# endswith terminator
	original_length = len(terminator)
	while not data.endswith(terminator):
		terminator = terminator[:-1]
	return original_length - len(terminator)

def get_settings_from_url(url, setting_defs):
	settings = {}
	query_params = dict(url.query_params)

	for setting_def in setting_defs:
		value = query_params.pop(setting_def.name, (setting_def.default_value,))
		value = value[-1]
		if value is not None:
			value = setting_def.type(value)
			if setting_def.choices and not value in setting_def.choices:
				raise ValueError("{0!r} is not a valid option for: {1}".format(value, setting_def.name))
		settings[setting_def.name] = value

	query_params = tuple(query_params.keys())
	if len(query_params) > 1:
		raise ValueError('unknown settings: ' + ', '.join(query_params))
	elif len(query_params) == 1:
		raise ValueError('unknown setting: ' + query_params[0])
	return settings

class ConnectionDriver(object):
	schemes = ()
	url_attributes = ()
	def __init__(self, url):
		for attribute in self.url_attributes:
			if not getattr(url, attribute):
				raise errors.ProtoconDriverError('missing required url attribute: ' + attribute)
		self.url = url
		self._connection = None
		self.connected = False
		self.print_driver = None
		self.settings = {}

	def _select(self, timeout):
		if self._connection is None:
			raise RuntimeError('_select can only be used when _connection is not None')
		timeout = None if timeout == _inf else timeout
		return select.select([self._connection], [], [], timeout)[0]

	def close(self):
		self.connected = False

	def set_settings_from_url(self, setting_defs):
		self.settings = get_settings_from_url(self.url, setting_defs)

	def open(self):
		self.connected = True

	def recv_size(self, size):
		raise NotImplementedError()

	def recv_timeout(self, timeout):
		raise NotImplementedError()

	def recv_until(self, terminator):
		data = b''
		while not data.endswith(terminator):
			data += self.recv_size(_remaining(data, terminator))
		return data

	def send(self, data):
		raise NotImplementedError()

	def print_error(self, msg):
		return (self.print_driver or color).print_error(msg)

	def print_good(self, msg):
		return (self.print_driver or color).print_good(msg)

	def print_status(self, msg):
		return (self.print_driver or color).print_status(msg)

	def print_warning(self, msg):
		return (self.print_driver or color).print_warning(msg)

class ConnectionDriverSetting(object):
	__slots__ = ('name', 'default_value', 'type', 'choices')
	def __init__(self, name, default_value=None, type=str, choices=None):
		self.name = name
		self.default_value = default_value
		self.type = type or str
		self.choices = choices

	def __repr__(self):
		return "<{0} name={1!r} default_value={2!r} >".format(self.__class__.__name__, self.name, self.default_value)
