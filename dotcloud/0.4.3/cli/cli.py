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
import time

import config
import utils
import remote
import local


VERSION = '0.4.3'


def hook_setup(cmd):
    if '-h' in cmd: return
    config.setup()
    sys.exit(0)

def hook_destroy(cmd):
    if '-h' in cmd: return
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

_trace = False
def hook___trace(cmd):
    global _trace
    cmd.pop(0)
    _trace = True

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
            'loop': lambda *x: run_loop(*x),
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

def run_loop(cmd, state, interval, timeout=100):
    count = 0
    while True:
        cmd[-1] = state
        more, state = run_command(cmd, True, retval=True, progress=True)
        if more is False:
            break
        if count > timeout:
            sys.stderr.write('\nTimed out\n')
            sys.exit(1)
        if isinstance(state, dict) and 'active' in state:
            count = 0
        else:
            count += 1
        if interval > 0:
            time.sleep(interval)
    return

_request = None
def run_command(cmd, internal=False, retval=False, progress=False):
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
    original_cmd = cmd
    cmd = urllib.quote(json.dumps(cmd))
    query = '{0}run?{1}={2}'.format(url['path'] or '/', 'c' if internal is True else 'q', cmd)
    headers = sign_request(cfg.apikey, 'GET', query)
    headers.update({
        'User-Agent': 'dotcloud/cli (version: {0})'.format(VERSION),
        'X-DotCloud-Version': VERSION
        })
    trace_id = None
    try:
        req.request('GET', query, headers=headers)
        resp = req.getresponse()
        info = resp.getheader('X-Dotcloud-Info')
        trace_id = resp.getheader('X-Dotcloud-TraceID')
        data = resp.read()
        req.close()
        if _export is True:
            print data
            return
        if info:
            utils.warning(info.replace(';', '\n'))
        if _trace and trace_id:
            utils.info('TraceID for "{0}": {1}'.format(
                original_cmd, trace_id))
        data = json.loads(data)
        if data['type'] == 'cmd':
            return run_remote(data['data'])
        if 'data' in data and len(data['data']) > 0:
            if progress:
                sys.stderr.write('\r')
            print data['data']
        elif progress:
            sys.stderr.write('.')
    except socket.error, e:
        utils.die('Cannot reach DotCloud service ("{0}").\n' \
                'Please check the connectivity and try again.'.format(str(e)))
    except Exception, e:
        message = 'DotCloud service unavailable ("{0}").\n' \
                'Data received:\n---\n{1}\n---\n' \
                'Please try again later. ' \
                'If the problem persists, send an email to support@dotcloud.com'.format(
                    e, data)
        if trace_id:
            message += '\nand include the following TraceID: {0}'.format(trace_id)
        else:
            message += '.'
        utils.die(message)
    finally:
        try:
            req.close()
        except Exception:
            pass
    if internal is True:
        if retval is True and 'retval' in data:
            return data['retval']
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
