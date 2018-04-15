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
import socket

AddrInfo = collections.namedtuple('AddrInfo', ('family', 'type', 'proto', 'canonname', 'sockaddr'))

def getaddrinfos(host, port=0, family=0, type=0, proto=0, flags=0):
	"""
	Return the results from :py:func:`socket.getaddrinfo` but as a tuple of
	:py:class:`.AddrInfo` objects for easier readability.

	:return: A tuple of :py:class:`.AddrInfo` objects.
	:rtype: tuple
	"""
	return tuple(AddrInfo(*result) for result in socket.getaddrinfo(host, port, family=family, type=type, proto=proto, flags=flags))

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
