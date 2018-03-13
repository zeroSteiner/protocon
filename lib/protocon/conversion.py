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
import functools
import re

from . import errors

ENCODINGS = ('base16', 'base64', 'hex', 'utf-8', 'utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le')

def _expandstr_repl(match, variables=None, encoding=None):
	variables = variables or {}
	prefix = ''

	# process leading slashes
	group = match.group('slashes')
	if group:
		prefix = '\\' * (len(group) // 2)
		if len(group) % 2:
			# if the number of slash is odd, we treat this as a literal
			return prefix + (match.group('escape') or match.group('var'))
		# if the number is even we continue with 'prefix'

	# process escape sequences
	group = match.group('escape')
	if group:
		if group == '\\\\':
			return prefix + '\\'
		if group == '\\n':
			return prefix + '\n'
		elif group == '\\r':
			return prefix + '\r'
		elif group == '\\t':
			return prefix + '\t'
		elif group[:2] == '\\x':
			if encoding != 'utf-8':
				raise errors.ProtoconDataExpansionError('can not use \\x escape sequences with encoding: ' + repr(encoding))
			elif len(group) != 4:
				start, end = match.span()
				raise errors.ProtoconDataExpansionError('invalid \\x escape sequence: ' + match.string[start:end + 2])
			return prefix + bytes.fromhex(group[2:]).decode('utf-8', 'surrogateescape')
		# return the character after the backslash, effectively treating it as a literal
		return group[1]

	# process variables
	group = match.group('var')
	if group:
		var_name = group[2:-1]
		var_value = variables.get(var_name)
		if var_value is None:
			raise errors.ProtoconDataExpansionError('undefined variable: ' + var_name)
		return prefix + var_value
	raise errors.ProtoconDataExpansionError('unknown match: ' + repr(match))

def decode(string, encoding='utf-8'):
	"""
	Decode data to a byte string using the specified encoding.

	:param str string:
	:param str encoding:
	:return: The decoded data.
	:rtype: bytes
	"""
	encoding = encoding.lower()
	if encoding == 'utf-8':
		data = string.encode('utf-8', 'surrogateescape')
	elif encoding in ('utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le'):
		data = string.encode(encoding)
	elif encoding == 'base64':
		data = binascii.a2b_base64(string)
	elif encoding in ('base16', 'hex'):
		if len(string) > 2 and re.match(r'^[0-9a-f]{2}([^0-9a-f])(([0-9a-f]{2}(\1)))*[0-9a-f]{2}$', string, re.IGNORECASE):
			string = string.replace(string[2], '')
		if len(string) % 2:
			raise errors.ProtoconDataDecodeError('odd-length hex string')
		if not re.match(r'^([0-9a-f]{2})*$', string, re.IGNORECASE):
			raise errors.ProtoconDataDecodeError('invalid hex character found')
		data = binascii.a2b_hex(string)
	else:
		raise ValueError('unsupported encoding: ' + encoding)
	return data

def expand(string, variables=None, encoding=None):
	regex = r'(?P<slashes>\\*)((?P<escape>\\(x[0-9a-f][0-9a-f]|.))|(?P<var>\$\{[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*\}))'
	return re.sub(regex, functools.partial(_expandstr_repl, variables=variables, encoding=encoding), string)

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
