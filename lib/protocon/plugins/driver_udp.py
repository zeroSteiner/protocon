#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/plugins/driver_tcp.py
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

import socket
import select
import time

import protocon
import protocon.conversion as conversion

class ConnectionDriver(protocon.ConnectionDriver):
	examples = {
		'udp': 'udp://1.2.3.4:123',
		'udp4': 'udp4://1.2.3.4:123'
	}
	schemes = ('udp', 'udp4', 'udp6')
	url_attributes = ('host', 'port',)
	def __init__(self, *args, **kwargs):
		super(ConnectionDriver, self).__init__(*args, **kwargs)
		if self.url.scheme in ('udp', 'udp4'):
			self._connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		elif self.url.scheme == 'udp6':
			self._connection = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
		self.size = conversion.eval_token(self.url.query_params.get('size', '8192'))
		if not isinstance(self.size, int):
			raise TypeError('size must be an integer')
		self.connected = True

	def _recv_size(self, size):
		return self._connection.recvfrom(size)[0]

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
				data += self._recv_size(self.size)
			remaining -= time.time() - start_time
		return data

	def recv_until(self, terminator):
		data = b''
		while not terminator in data:
			data += self._recv_size(self.size)
		return data.split(terminator, 1)[0] + terminator

	def send(self, data):
		self._connection.sendto(data, (self.url.host, self.url.port))
