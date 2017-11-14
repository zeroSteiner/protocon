#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/conversion.py
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

import binascii
import re

ENCODINGS = ('base16', 'base64', 'hex', 'utf-8', 'utf-16', 'utf-16be', 'utf-16le', 'utf-32', 'utf-32be', 'utf-32le')

def _decodestr_repl(match):
	match = match.group(1)
	if match == b'n':
		return b'\n'
	elif match == b'r':
		return b'\r'
	elif match == b't':
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
