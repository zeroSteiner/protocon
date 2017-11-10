#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/connection_driver.py
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

class ConnectionDriver(object):
	schemes = ()
	url_attributes = ()
	def __init__(self, url):
		self.url = url
		self.connected = False

	def close(self):
		self.connected = False

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
