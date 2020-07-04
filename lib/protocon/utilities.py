#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/utilities.py
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

import ast
import collections
import functools
import ipaddress
import re
import socket

AddrInfo = collections.namedtuple('AddrInfo', ('family', 'type', 'proto', 'canonname', 'sockaddr'))
_SockAddr4 = collections.namedtuple('_SockAddr4', ('address', 'port'))
_SockAddr6 = collections.namedtuple('_SockAddr6', ('address', 'port', 'flow_info', 'socpe_id'))

def getaddrinfos(host, port=0, family=0, type=0, proto=0, flags=0):
	"""
	Return the results from :py:func:`socket.getaddrinfo` but as a tuple of
	:py:class:`.AddrInfo` objects for easier readability.

	:return: A tuple of :py:class:`.AddrInfo` objects.
	:rtype: tuple
	"""
	infos = []
	for result in socket.getaddrinfo(host, port, family=family, type=type, proto=proto, flags=flags):
		family, type, proto, canonname, sockaddr = result
		if family == socket.AF_INET:
			sockaddr = _SockAddr4(*sockaddr)
		elif family == socket.AF_INET6:
			sockaddr = _SockAddr6(*sockaddr)
		infos.append(AddrInfo(family, type, proto, canonname, sockaddr))
	return tuple(infos)

def _literal_type(type_, value):
	try:
		value = ast.literal_eval(str(value))
	except (SyntaxError, ValueError):
		raise TypeError('value is not a ' + type_.__name__) from None
	if not isinstance(value, type_):
		raise TypeError('value is not a ' + type_.__name__)
	return value

def literal_type(type_):
	return functools.partial(_literal_type, type_)

class NetworkLocation(object):
	__slots__ = ('address', 'port')
	def __init__(self, address, port):
		self.address = ipaddress.ip_address(address)
		self.port = port

	def __repr__(self):
		return "{}({!r}, {!r})".format(self.__class__.__name__, self.address, self.port)

	def __str__(self):
		address = self.address
		if self.port:
			if isinstance(address, ipaddress.IPv6Address):
				address = '[' + str(address) + ']'
			address = str(address) + ':' + str(self.port)
		return str(address)

	@classmethod
	def from_string(cls, string, default_port=0):
		ipv4_regex = '(25[0-5]|2[0-4]\d|1\d\d|\d{1,2})(\.(25[0-5]|2[0-4]\d|1\d\d|\d{1,2})){3}'
		ipv6_regex = '[0-9a-f]{0,4}(:[0-9a-f]{0,4}){2,7}'
		regex = r'^(?P<bracket>\[)?'
		regex += '(?P<location>' + '|'.join([ipv4_regex, ipv6_regex]) + ')'
		regex += '(?(bracket)\]:(?=\d)|(:(?=\d)|$))(?P<port>(?<=:)\d+)?$'
		match = re.match(regex, string, flags=re.IGNORECASE)
		if match is None:
			raise ValueError('invalid network location specified')
		port = int(match.group('port')) if match.group('port') else default_port
		return cls(match.group('location'), port)

	def to_address(self):
		return (str(self.address), self.port)