#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/color.py
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

import functools
import os
import sys

import boltons.iterutils
import boltons.urlutils
import termcolor

colored_prefix = functools.partial(termcolor.colored, attrs=('bold',))
PREFIX_ERROR_RAW = '[-] '
PREFIX_ERROR = colored_prefix(PREFIX_ERROR_RAW, 'red')
PREFIX_GOOD_RAW = '[+] '
PREFIX_GOOD = colored_prefix(PREFIX_GOOD_RAW, 'green')
PREFIX_STATUS_RAW = '[*] '
PREFIX_STATUS = colored_prefix(PREFIX_STATUS_RAW, 'blue')
PREFIX_WARNING_RAW = '[!] '
PREFIX_WARNING = colored_prefix(PREFIX_WARNING_RAW, 'yellow')


def print_hexdump(data, stream=None, encoding='utf-8'):
	if not stream:
		stream = sys.stdout
	if isinstance(data, str):
		data = data.encode(encoding)
	data = bytearray(data)
	l = len(data)
	i = 0
	divider = 8
	chunk_size = 16
	for row, chunk in enumerate(boltons.iterutils.chunked(data, chunk_size, fill=-1)):
		offset_col = "{0:04x}".format(row * chunk_size)
		hex_col = ''
		for pos, byte in enumerate(chunk):
			hex_col += '   ' if byte == -1 else "{0:02x} ".format(byte)
			if pos and (pos + 1) % divider == 0:
				hex_col += ' '
		hex_col = hex_col[:-1]
		ascii_col = ''
		for byte in chunk:
			if byte == -1:
				ascii_col += ' '
			elif byte < 32 or byte > 126:
				ascii_col += '.'
			else:
				ascii_col += chr(byte)
		stream.write('  '.join((offset_col, hex_col, ascii_col)) + os.linesep)
	stream.flush()

def print_error(message, *args, **kwargs):
	message = termcolor.colored('[-] ', 'red', attrs=('bold',)) + message
	print(message, *args, **kwargs)

def print_good(message, *args, **kwargs):
	message = termcolor.colored('[+] ', 'green', attrs=('bold',)) + message
	print(message, *args, **kwargs)

def print_status(message, *args, **kwargs):
	message = PREFIX_STATUS + message
	print(message, *args, **kwargs)
