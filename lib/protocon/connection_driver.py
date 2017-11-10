#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/connection_driver.py
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
import socket
import time

class ConnectionDriver(object):
	def __init__(self, url):
		self.url = url
		if url.scheme in ('tcp', 'tcp4'):
			self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self._connection.connect((url.host, url.port))
		elif url.scheme == 'tcp6':
			self._connection = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
			self._connection.connect((url.host, url.port))
		elif url.scheme in ('udp', 'udp4'):
			self._connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		elif url.scheme == 'udp6':
			self._connection = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

	def _recv_size(self, size):
		if self.url.scheme in ('tcp', 'tcp4', 'tcp6'):
			recv = self._connection.recv
		elif self.url.scheme in ('udp', 'udp4', 'udp6'):
			recv = self._connection.recvfrom
		return recv(size)

	def close(self):
		if self.url.scheme in ('tcp', 'tcp4', 'tcp6'):
			self._connection.close()

	def recv_size(self, size):
		data = b''
		while len(data) < size:
			data += self._recv_size(size - len(data))
		return data

	def recv_timeout(self, timeout):
		if self.url.scheme in ('tcp', 'tcp4', 'tcp6'):
			_select = lambda t: select.select([self._connection], [], [], t)[0]
		elif self.url.scheme in ('udp', 'udp4', 'udp6'):
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
		if self.url.scheme in ('tcp', 'tcp4', 'tcp6'):
			self._connection.send(data)
		elif self.url.scheme in ('udp', 'udp4', 'udp6'):
			self._connection.sendto(data, (self.url.host, self.url.port))
