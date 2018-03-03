#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/connection_driver.py
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

from . import color

class ConnectionDriver(object):
	examples = {}
	schemes = ()
	url_attributes = ()
	def __init__(self, url):
		self.url = url
		self.connected = False
		self.print_driver = None

	def close(self):
		self.connected = False

	def open(self):
		self.connected = True

	def recv_size(self, size):
		raise NotImplementedError()

	def recv_timeout(self, timeout):
		raise NotImplementedError()

	def recv_until(self, terminator):
		data = self.recv_size(len(terminator))
		while not data.endswith(terminator):
			data += self.recv_size(1)
		return data

	def send(self, data):
		raise NotImplementedError()

	def print_error(self, msg):
		return (self.print_driver or color).print_error(msg)

	def print_good(self, msg):
		return (self.print_driver or color).print_good(msg)

	def print_status(self, msg):
		return (self.print_status or color).print_status(msg)

	def print_warning(self, msg):
		return (self.print_warning or color).print_warning(msg)
