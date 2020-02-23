#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/plugins/driver_rfcomm.py
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
import time

import protocon.utilities

_inf = float('inf')

class ConnectionDriver(protocon.ConnectionDriver):
	schemes = ('rfcomm',)
	setting_definitions = (
		protocon.ConnectionDriverSetting(name='dst'),
		protocon.ConnectionDriverSetting(name='channel', type=protocon.utilities.literal_type(int)),
	)
	def __init__(self, *args, **kwargs):
		super(ConnectionDriver, self).__init__(*args, **kwargs)
		self._addrinfo = None

	def _recv(self, size, timeout, terminator=None):
		now = time.time()
		expiration = _inf if timeout is None else time.time() + timeout
		data = b''
		while len(data) < size and (self._select(0) or expiration >= now):
			if not self._select(max(expiration - now, 0)):
				break
			chunk = self._connection.recv(1)
			if not chunk:
				self.connected = False
				break
			data += chunk
			if terminator is not None and terminator in data:
				data, terminator, _ = data.partition(terminator)
				data += terminator
				break
			now = time.time()
		return data

	def close(self):
		self._connection.close()
		super(ConnectionDriver, self).close()

	def open(self):
		sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
		sock.connect((self.settings['dst'], self.settings['channel']))
		self._connection = sock
		self.connected = True

	def recv_size(self, size, timeout=None):
		return self._recv(size, timeout)

	def recv_timeout(self, timeout):
		return self._recv(_inf, timeout)

	def recv_until(self, terminator, timeout=None):
		return self._recv(_inf, timeout, terminator=terminator)

	def send(self, data):
		self._connection.send(data)
