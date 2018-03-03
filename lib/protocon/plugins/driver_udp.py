#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/plugins/driver_udp.py
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

import socket
import select
import time

import protocon

class ConnectionDriver(protocon.ConnectionDriver):
	schemes = ('udp', 'udp4', 'udp6')
	url_attributes = ('host', 'port',)
	def __init__(self, *args, **kwargs):
		super(ConnectionDriver, self).__init__(*args, **kwargs)

		ConnectionDriverSetting = protocon.ConnectionDriverSetting
		self.set_settings_from_url((
			ConnectionDriverSetting(name='size', default_value=8192, type=int),
		))

	def _recv_size(self, size):
		return self._connection.recvfrom(size)[0]

	def _select(self, timeout):
		return select.select([self._connection], [], [], timeout)[0]

	def open(self):
		if self.url.scheme in ('udp', 'udp4'):
			self._connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		elif self.url.scheme == 'udp6':
			self._connection = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
		self.connected = True

	def recv_size(self, size):
		data = b''
		while len(data) < size:
			data += self._recv_size(size - len(data))
		return data

	def recv_timeout(self, timeout):
		remaining = timeout
		data = b''
		while (self._select(0) or remaining > 0) and self.connected:
			start_time = time.time()
			if self._select(max(remaining, 0)):
				data += self._recv_size(self.settings['size'])
			remaining -= time.time() - start_time
		return data

	def recv_until(self, terminator):
		data = b''
		while terminator not in data:
			data += self._recv_size(self.settings['size'])
		return data.split(terminator, 1)[0] + terminator

	def send(self, data):
		self._connection.sendto(data, (self.url.host, self.url.port))
