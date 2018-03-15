#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/color.py
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

def print_hexdump(data, stream=None):
	stream = stream or sys.stdout
	data = bytearray(data)
	divider = 8
	chunk_size = 16
	for row, chunk in enumerate(boltons.iterutils.chunked(data, chunk_size, fill=-1)):
		offset_col = "{0:04x}".format(row * chunk_size)
		ascii_col = ''
		hex_col = ''
		pos = 0
		for pos, byte in enumerate(chunk):
			hex_col += '   ' if byte == -1 else "{0:02x} ".format(byte)
			if divider and pos and (pos + 1) % divider == 0:
				hex_col += ' '

			if byte == -1:
				ascii_col += ' '
			elif byte < 32 or byte > 126:
				ascii_col += '.'
			else:
				ascii_col += chr(byte)
			if divider and pos and (pos + 1) % divider == 0:
				ascii_col += ' '
		hex_col = hex_col[:-2 if pos and (pos + 1) % divider == 0 else -1]
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
