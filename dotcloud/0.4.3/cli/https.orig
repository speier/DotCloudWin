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
import socket
import ssl
import httplib


class HTTPSConnection(httplib.HTTPSConnection):

    def check_fqdn(self, cert):
        cert = self.sock.getpeercert()
        if not cert or 'subject' not in cert:
            ValueError('Cannot verify domain')
        fqdn = [v for k, v in [key[0] for key in cert['subject']] if k == 'commonName'].pop(0)
        if self.host == fqdn or '.' in self.host \
                and fqdn == '*.' + self.host.split('.', 1).pop(1):
                    return
        raise ValueError('Host mismatches the certificate domain')

    def connect(self):
        """ Check certificate's FQDN
        subjectAltName not handled
        """
        sock = socket.create_connection((self.host, self.port), self.timeout)
        ca_path = os.path.join(os.path.dirname(__file__), 'root_ca.pem')
        try:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                    cert_reqs=ssl.CERT_REQUIRED,
                    ca_certs=ca_path)
        except ssl.SSLError, e:
            raise ValueError('SSLError: {0}'.format(e))
        self.check_fqdn(self.sock.getpeercert())
