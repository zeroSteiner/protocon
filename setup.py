#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  setup.py
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

import os
import re
import sys

base_directory = os.path.dirname(__file__)

try:
	from setuptools import setup, find_packages
except ImportError:
	print('This project needs setuptools in order to build. Install it using your package')
	print('manager (usually python-setuptools) or via pip (pip install setuptools).')
	sys.exit(1)

try:
	with open(os.path.join(base_directory, 'README.rst')) as file_h:
		long_description = file_h.read()
except OSError:
	sys.stderr.write('README.rst is unavailable, can not generate the long description\n')
	long_description = None

with open(os.path.join(base_directory, 'lib', 'protocon', '__init__.py')) as file_h:
	match = re.search(r'^__version__\s*=\s*([\'"])(?P<version>\d+(\.\d)*)\1$', file_h.read(), flags=re.MULTILINE)
if match is None:
	raise RuntimeError('Unable to find the version information')
version = match.group('version')

DESCRIPTION = """\
Protocon is a socket-centric framework for rapidly prototyping connections \
through simple send and receive transcripts.\
"""

setup(
	name='protocon',
	version=version,
	author='Spencer McIntyre',
	author_email='zeroSteiner@gmail.com',
	maintainer='Spencer McIntyre',
	maintainer_email='zeroSteiner@gmail.com',
	description=DESCRIPTION,
	long_description=long_description,
	url='https://github.com/zeroSteiner/protocon',
	license='BSD',
	# these are duplicated in Pipfile
	install_requires=[
		'boltons>=17.1.0',
		'cmd2==2.4.3',
		'crcelk==1.3',
		'hyperlink>=18.0.0',
		'ipython>=6.2.1',
		'pluginbase>=0.5',
		'pyserial>=3.4',
		'termcolor>=1.1.0',
	],
	package_dir={'': 'lib'},
	packages=find_packages('lib'),
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'Intended Audience :: Information Technology',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3.11',
		'Topic :: Security',
		'Topic :: Software Development :: Libraries :: Python Modules'
	],
	scripts=['protocon']
)
