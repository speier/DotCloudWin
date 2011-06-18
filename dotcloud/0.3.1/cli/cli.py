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
import json
import hmac
import hashlib
import datetime
import socket
import httplib
import urllib
import https

import config
import utils
import remote
import local


VERSION = '0.3.1'


def hook_setup(cmd):
    config.setup()
    sys.exit(0)

def hook_destroy(cmd):
    local.confirm('Please confirm destruction')

def hook___version(cmd):
    print 'DotCloud CLI version {0}'.format(VERSION)
    sys.exit(0)

_export = False
def hook___export(cmd):
    global _export
    cmd.pop(0)
    _export = True

def hook___import(cmd):
    def _import(f):
        data = json.loads(f.read())
        if data['type'] == 'cmd':
            run_remote(data['data'])
    if len(cmd) > 1:
        for d in cmd[1:]:
            with open(d) as f:
                _import(f)
    else:
        _import(sys.stdin)
    sys.exit(0)

def run_remote(cmd):
    r = remote.Remote()
    handlers = {
            'set_url': r.set_url,
            'run': r.run,
            'script': r.run_script,
            'sftp': r.sftp,
            'pull': r.pull,
            'push': r.push,
            'rsync': r.rsync,
            'git': r.git,
            'hg': r.hg,
            'upload': r.upload,
            'confirm': local.confirm,
            'call': lambda x: run_command(x, True),
            'echo': lambda x: sys.stdout.write('{0}\n'.format(x)),
            'echo_error': lambda x: sys.stderr.write('{0}\n'.format(x)),
            'set_verbose': r.set_verbose,
            'key': r.key
            }
    for args in cmd:
        c = args[0]
        if c not in handlers:
            # Ignore unsupported commands
            return
        if len(args) > 1:
            args = tuple(args[1:])
            ret = handlers[c](*args)
        else:
            ret = handlers[c]()
        if isinstance(ret, int):
            if ret != 0:
                utils.die('Abort.')

def sign_request(api_key, method, request):
    (access_key, secret_key) = api_key.split(':')
    date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    s = ':'.join((method, request, date))
    sign = hmac.new(bytes(secret_key), s, hashlib.sha1).hexdigest()
    headers = {
            'X-DotCloud-Access-Key': access_key,
            'X-DotCloud-Auth-Version': '1.0',
            'X-DotCloud-Date': date,
            'X-DotCloud-Authorization': sign
            }
    return headers

_request = None
def run_command(cmd, internal=False):
    global _request
    if internal is False and not os.path.exists(config.CONFIG_KEY):
        run_command('get_key', True)
    data = None
    cfg = config.load_user_config()
    url = utils.parse_url(cfg.url)
    if _request:
        req = _request
    else:
        if url['scheme'].lower() == 'https':
            req = https.HTTPSConnection(url['host'], int(url['port'] or 443))
        else:
            req = httplib.HTTPConnection(url['host'], int(url['port'] or 80))
        _request = req
    cmd = urllib.quote(json.dumps(cmd))
    query = '{0}run?{1}={2}'.format(url['path'], 'c' if internal is True else 'q', cmd)
    headers = sign_request(cfg.apikey, 'GET', query)
    headers.update({
        'User-Agent': 'dotcloud/cli (version: {0})'.format(VERSION),
        'X-DotCloud-Version': VERSION
        })
    try:
        req.request('GET', query, headers=headers)
        resp = req.getresponse()
        info = resp.getheader('X-Dotcloud-Info')
        data = resp.read()
        if _export is True:
            print data
            return
        if info:
            utils.warning(info.replace(';', '\n'))
        data = json.loads(data)
        if data['type'] == 'cmd':
            return run_remote(data['data'])
        if 'data' in data:
            print data['data']
    except socket.error, e:
        utils.die('Cannot reach DotCloud service ("{0}").\nPlease check the connectivity and try again.'.format(str(e)))
    except Exception, e:
        utils.die('DotCloud service unavailable ("{0}").\nPlease try again later. If the problem persists, send an email to support@dotcloud.com.'.format(e))
    finally:
        try:
            req.close()
        except Exception:
            pass
    if internal is True:
        return
    # Return proper exit code to the shell
    if not data:
        sys.exit(1)
    sys.exit(int(data['type'] != 'success'))


def main():
    try:
        cmd = sys.argv
        cmd.pop(0)
        if cmd:
            c = cmd[0].replace('-', '_')
            hook = globals().get('hook_{0}'.format(c))
            if hook and callable(hook):
                hook(cmd)
        run_command(cmd)
    except KeyboardInterrupt:
        pass
