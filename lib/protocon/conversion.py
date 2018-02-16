#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/conversion.py
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
import re

ENCODINGS = ('base16', 'base64', 'hex', 'utf-8', 'utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le')

def _decodestr_repl(match, encoding='utf-8'):
	match = match.group(1).decode(encoding)
	if match == 'n':
		return b'\n'
	elif match == 'r':
		return b'\r'
	elif match == 't':
		return b'\t'
	elif match[0] == 'x':
		return bytes.fromhex(match[1:3])
	raise ValueError('unknown escape sequence: ' + match)

def decode(data, encoding):
	"""
	Decode data to a byte string using the specified encoding.

	:param str data:
	:param str encoding:
	:return: The decoded data.
	:rtype: bytes
	"""
	encoding = encoding.lower()
	if encoding in ('utf-8', 'utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le'):
		data = data.encode(encoding)
		regex = br'(?<!\\)(?:\\\\)*\\([nrt]|x[0-9a-f][0-9a-f])'
		data = re.sub(regex, _decodestr_repl, data)
	elif encoding == 'base64':
		data = binascii.a2b_base64(data)
	elif encoding in ('base16', 'hex'):
		if len(data) > 2 and re.match(r'^[a-f0-9]{2}[^a-f0-9]', data):
			data = data.replace(data[3], '')
		data = binascii.a2b_hex(data)
	else:
		raise ValueError('unsupported encoding: ' + encoding)
	return data

def eval_token(value):
	if value.lower() == 'false':
		value = False
	elif value.lower() == 'null':
		value = None
	elif value.lower() == 'true':
		value = True
	elif re.match(r'^0b[01]+$', value):
		value = int(value[2:], 2)
	elif re.match(r'^0o[0-7]+$', value):
		value = int(value[2:], 8)
	elif re.match(r'^0x[a-fA-F0-9]+$', value):
		value = int(value[2:], 16)
	elif re.match(r'^[0-9]+\.[0-9]*$', value):
		value = float(value)
	elif re.match(r'^[0-9]+$', value):
		value = int(value, 10)
	elif re.match(r'^("|\').+\1$', value):
		value = value[1:-1]
	return value
