#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/plugins/driver_ether.py
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

import binascii
import fcntl
import os
import re
import socket
import struct
import time

import protocon.errors
import protocon.utilities

_inf = float('inf')

_BROADCAST = b'\xff\xff\xff\xff\xff\xff'
_HEADER_SIZE = 14

def _assert_is_mac(mac):
	if re.match('^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', mac) is None:
		raise protocon.errors.ProtoconDriverError('bad mac address: ' + mac)
	return True

def _get_iface_mac(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15].encode('ascii')))
	return ':'.join(['%02x' % char for char in info[18:24]])

# This driver is a software wrapper on top of L2 sockets to handle ethernet
# headers. Frames sent will have an ethernet header created and added to them
# and frames received will be filtered based on their ethernet header.
class ConnectionDriver(protocon.ConnectionDriver):
	schemes = ('ether',)
	setting_definitions = (
		protocon.ConnectionDriverSetting(name='src'),
		protocon.ConnectionDriverSetting(name='dst', default_value='ff:ff:ff:ff:ff:ff'),
		protocon.ConnectionDriverSetting(name='type', default_value=0x0800, type=protocon.utilities.literal_type(int)),
		protocon.ConnectionDriverSetting(name='size', default_value=0xffff, type=protocon.utilities.literal_type(int)),
	)
	url_attributes = ('host',)
	def __init__(self, *args, **kwargs):
		if os.getuid():
			raise protocon.errors.ProtoconDriverError('this driver requires root privileges')
		super(ConnectionDriver, self).__init__(*args, **kwargs)
		_assert_is_mac(self.settings['dst'])
		if self.settings['src'] is None:
			self.settings['src'] = _get_iface_mac(self.url.host)
		_assert_is_mac(self.settings['src'])

	def _mac(self, which):
		mac = self.settings[which]
		_assert_is_mac(mac)
		return binascii.a2b_hex(mac.replace(':', ''))

	def _recv(self, size, timeout, terminator=None):
		now = time.time()
		expiration = _inf if timeout is None else time.time() + timeout
		data = b''
		while len(data) < size and (self._select(0) or expiration >= now):
			if not self._select(max(expiration - now, 0)):
				break
			packet = self._connection.recv(_HEADER_SIZE + (self.settings['size'] if size == _inf else size))
			if len(packet) < _HEADER_SIZE:
				continue
			dst, src = packet[:6], packet[6:12]
			if dst != self._mac('src') and dst != _BROADCAST:
				continue
			if src != self._mac('dst') and self._mac('dst') != _BROADCAST:
				continue
			data += packet[_HEADER_SIZE:]
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
		self._connection = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.settings['type']))
		self._connection.bind((self.url.host, 0))
		self.connected = True

	def recv_size(self, size, timeout=None):
		return self._recv(size, timeout)

	def recv_timeout(self, timeout):
		return self._recv(_inf, timeout)

	def recv_until(self, terminator, timeout=None):
		return self._recv(_inf, timeout, terminator=terminator)

	def send(self, data):
		ether = self._mac('dst') + self._mac('src') + struct.pack('>H', self.settings['type'])
		self._connection.send(ether + data)
