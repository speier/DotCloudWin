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
import subprocess

import utils
import config
import local

class Remote(object):

    def __init__(self):
        self._verbose = True
        self._ssh_master = None
        self._ssh_options = (
                'ssh', '-t',
                '-i', config.CONFIG_KEY,
                '-o', 'LogLevel=QUIET',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'PasswordAuthentication=no',
                '-o', 'ServerAliveInterval=10'
                )

    def set_url(self, url):
        parts = utils.parse_url(url)
        (self._user, self._host, self._port) = (parts['user'] or 'dotcloud', parts['host'], parts['port'] or '22')
        self._url = url

    def set_verbose(self, flag):
        self._verbose = flag

    def info(self, *args):
        if not self._verbose:
            return
        utils.info(*args)

    def die(self, progname):
        utils.die('Error: "{0}" failed to be executed. Please make sure it is properly installed.'.format(progname))

    def warning_ssh(self):
        utils.warning('Warning: The SSH connection failed')
        utils.warning('Please try again. If the problem persists, send an email to support@dotcloud.com.')
        utils.warning('Also please check that your are allowed to make an SSH connection to a custom port.')

    def _escape(self, s):
        for c in ('`', '$', '"'):
            s = s.replace(c, '\\' + c)
        return s

    def _ssh(self, cmd, **kwargs):
        p_args = self._ssh_options + (
                '-l', self._user,
                '-p', self._port,
                self._host,
                'bash -l -c "{0}"'.format(self._escape(cmd))
                )
        return subprocess.Popen(p_args, **kwargs)

    def _scp(self, src, dest):
        scp = (
                'scp', '-P', self._port, '-r',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'StrictHostKeyChecking=no',
                src, dest
        )
        return subprocess.call(scp, close_fds=True)

    def key(self, data):
        with open(config.CONFIG_KEY, 'w') as f:
            f.write(data)
            if not utils.is_windows():
                os.fchmod(f.fileno(), 0600)

    def sftp(self):
        sftp = (
                'sftp',
                '-o', 'Port={0}'.format(self._port),
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'StrictHostKeyChecking=no',
                '{user}@{host}'.format(user=self._user, host=self._host)
                )
        return subprocess.call(sftp, close_fds=True)

    def push(self, src, dest='.'):
        self.info('# push {0} {1}'.format(src, dest))
        return self._scp(src, '{user}@{host}:{dest}'.format(user=self._user, host=self._host, dest=dest))

    def pull(self, src, dest='.'):
        self.info('# pull {0} {1}'.format(src, dest))
        return self._scp('{user}@{host}:{src}'.format(user=self._user, host=self._host, src=src), dest)

    def run(self, *args):
        cmd = ' '.join(args)
        self.info('# {0}'.format(cmd))
        return self._ssh(cmd).wait()

    def run_script(self, script):
        proc = self._ssh('/bin/bash', stdin=subprocess.PIPE)
        proc.stdin.write(script)
        proc.communicate()

    def rsync(self, local_dir, destination, args):
        self.info('# rsync')
        excludes = args.get('excludes')
        url = utils.parse_url(destination)
        ssh = ' '.join(self._ssh_options)
        ssh += ' -p {0}'.format(url['port'])
        if not os.path.isfile(local_dir) and not local_dir.endswith('/'):
            local_dir += '/'
        ignore_file = os.path.join(local_dir, '.dotcloudignore')
        ignore_opt = ('--exclude-from', ignore_file)
        if not os.path.exists(ignore_file):
            ignore_opt = tuple()
        rsync = ('rsync', '-lpthrvz', '--delete', '--safe-links') + \
                tuple('--exclude={0}'.format(e) for e in excludes) + ignore_opt + \
                ('-e', ssh, local_dir,
                        '{user}@{host}:{dest}/'.format(user=url['user'],
                        host=url['host'], dest=url['path']))
        try:
            ret = subprocess.call(rsync, close_fds=True)
            if ret != 0:
                self.warning_ssh()
            return ret
        except OSError:
            self.die('rsync')

    def hg(self, local_dir, destination, args):
        self.info('# hg')
        with utils.cd(local_dir):
            try:
                ssh = ' '.join(self._ssh_options)
                args = ('hg', 'push', '--ssh', ssh, '-f', destination)
                ret = subprocess.call(args, close_fds=True)
                if ret != 0:
                    self.warning_ssh()
                return ret
            except OSError:
                self.die('hg')

    def git(self, local_dir, destination, args):
        self.info('# git')
        with utils.cd(local_dir):
            try:
                os.environ['GIT_SSH'] = '__dotcloud_git_ssh'
                os.environ['DOTCLOUD_SSH_KEY'] = config.CONFIG_KEY
                ret = subprocess.call(('git', 'push', '-f', '--all',
                    destination), close_fds=True)
                if ret != 0:
                    self.warning_ssh()
                return ret
            except OSError:
                self.die('git')

    def upload_method(self, local_dir):
        if os.path.isdir(os.path.join(local_dir, '.hg')):
            return 'hg'
        if os.path.isdir(os.path.join(local_dir, '.git')):
            return 'git'
        return 'rsync'

    def upload(self, local_dir, destination, args):
        if args.get('check'):
            local_dir = self.check_pushdir(local_dir)
        if args.get('verify_key'):
            self.verify_key(args.get('verify_key'))
        self.info('# upload {0} {1}'.format(local_dir, destination))
        method = args.get('force_method') or self.upload_method(local_dir)
        if method == 'hg':
            return self.hg(local_dir, destination, args.get('hg', {}))
        if method == 'git':
            return self.git(local_dir, destination, args.get('git', {}))
        return self.rsync(local_dir, destination, args.get('rsync', {}))

    def verify_key(self, key):
        f = open(config.CONFIG_KEY).read()
        if not f.replace('\n', '') == key.replace('\n', ''):
            utils.die('Error: you seem to have a stale key file "{0}"\n'
                      'Remove the file or run "dotcloud setup" command again.'.format(config.CONFIG_KEY))

    def check_pushdir(self, local_dir):
        orig = dir = os.path.realpath(local_dir)
        if ':' in orig: # win32?
            return self.check_pushdir_win32(local_dir)
        while True:
            if os.path.isdir(dir) and os.path.exists(os.path.join(dir, 'dotcloud.yml')):
                if dir != orig:
                    utils.info('# Found dotcloud.yml: Using {0} as a base directory'.format(dir))
                return dir
            prev = dir
            dir = os.path.realpath(os.path.join(dir, os.path.pardir))
            if dir == prev:
                local.confirm('Could not find dotcloud.yml file in {0} and parent directories. Proceed?'.format(orig))
                break
        return orig

    def check_pushdir_win32(self, local_dir):
        if not os.path.exists(os.path.join(local_dir, 'dotcloud.yml')):
            local.confirm('Could not find dotcloud.yml file in {0}. Proceed?'.format(local_dir))
        return local_dir
