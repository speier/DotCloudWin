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
import platform

import json

from utils import die, info


CONFIG_DIR = os.path.expanduser('~/.dotcloud')
CONFIG_FILE = os.path.basename(os.environ.get('DOTCLOUD_CONFIG_FILE', 'dotcloud.conf'))
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
if 'DOTCLOUD_CONFIG_FILE' in os.environ:
    CONFIG_KEY = CONFIG_PATH + '.key'
else:
    CONFIG_KEY = os.path.join(CONFIG_DIR, 'dotcloud.key')


class Config(dict):

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, dict):
            return self.__class__(value)
        return value

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]

    def __repr__(self):
        return '<Config ' + dict.__repr__(self) + '>'


def load(config_file):
    config = json.load(file(config_file))
    if config is None:
        config = {}
    config = Config(config)
    return config

def load_user_config():
    if not os.path.exists(CONFIG_PATH):
        info('Warning: {0} does not exist.'.format(CONFIG_PATH))
        setup()
    config = load(CONFIG_PATH)
    if 'url' not in config or 'apikey' not in config:
        die('Configuration file not valid. Please run "dotcloud setup" to create it.')
    return config

def move_old_config():
    #FIXME: This function will be removed at the next release.
    old_file = os.path.join(os.path.expanduser('~'), '.' + CONFIG_FILE)
    if not os.path.exists(old_file):
        return False
    with open(old_file) as f:
        data = f.read()
    with open(CONFIG_PATH, 'w') as f:
        if 'DOTCLOUD_CONFIG_FILE' not in os.environ:
            data = data.replace('http://', 'https://')
        f.write(data)
        if (platform.system() != 'Windows'):
          os.fchmod(f.fileno(), 0600)
    info('Migrated from {0}'.format(old_file))
    return True

def setup():
    import re
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR, 0700)
    if move_old_config() is True:
        return
    conf = {'url': 'https://api.dotcloud.com/'}
    apikey = raw_input('Enter your api key (You can find it at http://www.dotcloud.com/account/settings): ')
    if not re.match('\w{20}:\w{40}', apikey):
        die('Not a valid api key.')
    conf['apikey'] = apikey
    with open(CONFIG_PATH, 'w') as f:
        json.dump(conf, f, indent=4)
        if (platform.system() != 'Windows'):
          os.fchmod(f.fileno(), 0600)
