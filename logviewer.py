#!/usr/bin/env python

import time
import SimpleHTTPServer
import os
import posixpath
import urllib
import cgi
import shutil
import mimetypes
import pdb
import re
import sys
from tempfile import NamedTemporaryFile
from StringIO import StringIO

class LogServer(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def server_bind(self):
        BaseHTTPServer.HTTPServer.server_bind(self)
        self.socket.setblocking(0)
        self.run = True

    def do_GET(self):
       f = self.send_head()
       if f:
           self.copyfile(f, self.wfile)
           f.close()
       self.stream()

    def stream(self):
        try:
            self.filepath
            while True:
                f = open(self.filepath, 'r')
                f.seek(self.filesize)
                self.wfile.write(f.read())
                self.filesize = f.tell()
                f.close()
                time.sleep(1)
        except:
            return

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        if ctype.startswith('text/'):
            mode = 'r'
        else:
            mode = 'rb'
        try:
            f = open(path, mode)
            self.filepath = path
        except IOError:
            self.send_error(404, "File not found")
            return None

        # if ?# in request, send only last # lines        
        if mode == 'r':
            self.filesize = os.path.getsize(self.filepath)
            try:
                numLines = int(re.search('^.*\?(\d+)', self.path).groups()[0])
                self.lines = f.readlines()[-numLines:]
                output = NamedTemporaryFile()
                for line in self.lines:
                    output.write(line)
                output.seek(0)
                f = output
            except AttributeError:
                pass

        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("connection", "keep-alive")
        self.end_headers()

        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        try:
            if os.path.isdir(sys.argv[2]):
                path = os.path.abspath(sys.argv[2])
        except IndexError:
            path = os.getcwd()
        for word in words:
            word = word.split('?')[0]
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'text/plain', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        '.log': 'text/plain',
        '.txt': 'text/plain',
        '.sh': 'text/plain',
        '.bin': 'application/octet-stream',
        })

def test(HandlerClass = LogServer, ServerClass = SimpleHTTPServer.BaseHTTPServer.HTTPServer):
    SimpleHTTPServer.test(HandlerClass, ServerClass)

if __name__ == '__main__':
    test()
