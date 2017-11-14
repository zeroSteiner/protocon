#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/plugins/driver_serial.py
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

import select
import time

import serial

import protocon
import protocon.conversion as conversion

BAUDRATES = (
	50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200,
	230400, 460800, 500000, 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000
)

class ConnectionDriver(protocon.ConnectionDriver):
	examples = {
		'serial': 'serial:///dev/ttyUSB0?baudrate=9600&bytesize=8&parity=N&stopbits=1'
	}
	schemes = ('serial',)
	url_attributes = ('path',)
	default_settings = {
		'baudrate': 9600,
		'bytesize': 8,
		'parity': 'N',
		'stopbits': serial.STOPBITS_ONE,
	}
	def __init__(self, *args, **kwargs):
		super(ConnectionDriver, self).__init__(*args, **kwargs)
		self.settings = {}
		self.settings.update(self.default_settings)
		query_params = {}
		query_params.update(self.url.query_params.items())

		setting_values = {
			'baudrate': BAUDRATES,
			'bytesize': (5, 6, 7, 8),
			'parity': serial.PARITY_NAMES.keys(),
			'stopbits': (1, 1.5, 2),
		}

		for setting, possible_values in setting_values.items():
			if not setting in query_params:
				continue
			value = conversion.eval_token(query_params.pop(setting))
			if not value in possible_values:
				raise ValueError("unsupported value for {0}: {1!r}".format(setting, value))
			self.settings[setting] = value
		if query_params:
			raise ValueError("unsupported option: {0}".format(tuple(query_params.keys())[0]))

		self._connection = serial.Serial(self.url.path, **self.settings)
		self._connection.setRTS(True)
		self._connection.setDTR(False)
		self.connected = True

	def _recv_size(self, size):
		return self._connection.read(size)

	def close(self):
		self._connection.close()
		super(ConnectionDriver, self).close()

	def recv_size(self, size):
		data = b''
		while len(data) < size:
			data += self._recv_size(size - len(data))
		return data

	def recv_timeout(self, timeout):
		_select = lambda t: select.select([self._connection], [], [], t)[0]
		remaining = timeout
		data = b''
		while remaining > 0:
			start_time = time.time()
			if _select(remaining):
				data += self._recv_size(1)
			remaining -= time.time() - start_time
		return data

	def send(self, data):
		self._connection.write(data)
