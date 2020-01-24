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
import time

import protocon
import protocon.utilities

from OpenSSL import SSL
from OpenSSL._util import (lib as _lib)

DTLSv1_METHOD = 7
SSL.Context._methods[DTLSv1_METHOD] = getattr(_lib, "DTLSv1_client_method")

_inf = float('inf')

class ConnectionDriver(protocon.ConnectionDriver):
	schemes = ('dtls', 'dtls4', 'dtls6', 'udp', 'udp4', 'udp6')
	url_attributes = ('host', 'port',)
	def __init__(self, *args, **kwargs):
		super(ConnectionDriver, self).__init__(*args, **kwargs)
		self._addrinfo = None

		ConnectionDriverSetting = protocon.ConnectionDriverSetting
		self.set_settings_from_url((
			ConnectionDriverSetting(name='ip6-scope-id'),
			ConnectionDriverSetting(name='size', default_value=0xffff, type=protocon.utilities.literal_type(int)),
		))

	def _recv(self, size, timeout, terminator=None):
		now = time.time()
		expiration = _inf if timeout is None else time.time() + timeout
		data = b''
		while len(data) < size and (self._select(0) or expiration >= now):
			if not self._select(max(expiration - now, 0)):
				break
			data += self._connection.recvfrom(self.settings['size'] if size == _inf else size)[0]
			if terminator is not None and terminator in data:
				data, terminator, _ = data.partition(terminator)
				data += terminator
				break
			now = time.time()
		return data

	def open(self):
		family = {
			'dtls': socket.AF_UNSPEC, 'dtls4': socket.AF_INET, 'dtls6': socket.AF_INET6,
			'udp': socket.AF_UNSPEC, 'udp4': socket.AF_INET, 'udp6': socket.AF_INET6
		}[self.url.scheme]
		addrinfo = protocon.utilities.getaddrinfos(
			self.url.host,
			self.url.port,
			family,
			type=socket.SOCK_DGRAM,
			proto=socket.IPPROTO_UDP
		)
		if not addrinfo:
			raise protocon.ProtoconDriverError('getaddrinfo failed for the specified URL')
		self._addrinfo = addrinfo[0]
		if self._addrinfo.family == socket.AF_INET6 and self.settings['ip6-scope-id'] is not None:
			scope_id = self.settings['ip6-scope-id']
			scope_id = int(scope_id) if scope_id.isdigit() else socket.if_nametoindex(scope_id)
			self._addrinfo = self._addrinfo._replace(sockaddr=self._addrinfo.sockaddr[:3] + (scope_id,))

		self._connection = socket.socket(self._addrinfo.family, self._addrinfo.type)
		if self.url.scheme.startswith('dtls'):
			ctx = SSL.Context(DTLSv1_METHOD)
			self._connection = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
		self.connected = True

	def recv_size(self, size, timeout=None):
		return self._recv(size, timeout)

	def recv_timeout(self, timeout):
		return self._recv(_inf, timeout)

	def recv_until(self, terminator, timeout=None):
		return self._recv(_inf, timeout, terminator=terminator)

	def send(self, data):
		self._connection.sendto(data, self._addrinfo.sockaddr)
