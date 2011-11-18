## Copyright (c) 2010 dotCloud Inc.
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
## THE SOFTWARE.

import os
import sys
import re
import platform
from contextlib import contextmanager


def is_windows():
    return platform.system() == 'Windows'

def die(msg):
    print >>sys.stderr, msg
    sys.exit(1)

def warning(msg):
    print >>sys.stderr, '\033[93m{0}\033[0m'.format(msg)

def info(msg):
    print >>sys.stderr, msg

def print_table(rows):
    rows = list(rows)
    width = {}
    for row in rows:
        for (idx, word) in enumerate(map(str, row)):
            width.setdefault(idx, 0)
            width[idx] = max(width[idx], len(word))
    for row in rows:
        for (idx, word) in enumerate(map(str, row)):
            print '{word:{width}}'.format(word=word, width=(1 if idx == (len(row) - 1) else width[idx])),
        print ''

def parse_url(url):
    m = re.match('^(?P<scheme>[^:]+)://((?P<user>[^@]+)@)?(?P<host>[^:/]+)(:(?P<port>\d+))?(?P<path>/.*)?$', url)
    if not m:
        raise ValueError('"{url}" is not a valid url'.format(url=url))
    ret = m.groupdict()
    return ret

def which(binary):
    (path, name) = os.path.split(binary)
    if path:
        return binary if os.access(binary, os.X_OK) else None
    for path in os.environ['PATH'].split(os.pathsep):
        binary = os.path.join(path, name)
        if os.access(binary, os.X_OK):
            return binary

@contextmanager
def cd(path):
    old = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old)
