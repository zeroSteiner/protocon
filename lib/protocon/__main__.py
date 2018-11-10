#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  protocon/__main__.py
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

import argparse
import sys

from . import __version__
from . import color
from . import engine
from . import errors

EPILOG = """\
target_url examples:
  null:
  serial:///dev/ttyUSB0?baudrate=9600&bytesize=8&parity=N&stopbits=1
  tcp://1.2.3.4:123
  tcp4://0.0.0.0:123/?type=server
  tcp6://[fe80::800:27ff:fe00:10]:4444/?ip6-scope-id=eth0
  udp://1.2.3.4:123
  udp4://1.2.3.4:123/?size=8192
"""

def main():
	parser = argparse.ArgumentParser(prog='protocon', description='protocon', conflict_handler='resolve', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-q', '--quiet', action='store_true', default=False, help='initialize quiet to True')
	parser.add_argument('-v', '--version', action='version', version='protocon Version: ' + __version__)
	parser.add_argument('target_url', help='the connection URL')
	parser.add_argument('scripts', metavar='script', nargs='*', help='the script to execute')
	parser.epilog = EPILOG
	arguments = parser.parse_args()

	try:
		protocon = engine.Engine.from_url(arguments.target_url)
	except errors.ProtoconDriverError as error:
		color.print_error('Driver error: ' + error.message)
	else:
		protocon.entry(arguments.scripts)
		protocon.connection.close()
	return 0

if __name__ == '__main__':
	sys.exit(main())
