import gevent.pywsgi
import os
import six
import tempfile

from contextlib import contextmanager
from geventhttpclient.useragent import UserAgent


@contextmanager
def wsgiserver(handler):
    server = gevent.pywsgi.WSGIServer(('127.0.0.1', 54323), handler)
    server.start()
    try:
        yield
    finally:
        server.stop()


def check_upload(body, headers=None):
    def wsgi_handler(env, start_response):
        if headers:
            assert six.viewitems(env) >= six.viewitems(headers)
        assert body == env['wsgi.input'].read()
        start_response('200 OK', [])
        return []
    return wsgi_handler


def check_redirect():
    def wsgi_handler(env, start_response):
        if env.get('PATH_INFO') == "/":
            start_response('301 Moved Permanently', [('Location', 'http://127.0.0.1:54323/redirected')])
            return []
        else:
            assert env.get('PATH_INFO') == "/redirected"
            start_response('200 OK', [])
            return [b"redirected"]
    return wsgi_handler


def test_file_post():
    body = tempfile.NamedTemporaryFile("a+b", delete=False)
    name = body.name
    try:
        body.write(b"123456789")
        body.close()
        headers = {'CONTENT_LENGTH': '9', 'CONTENT_TYPE': 'application/octet-stream'}
        with wsgiserver(check_upload(b"123456789", headers)):
            useragent = UserAgent()
            with open(name, 'rb') as body:
                useragent.urlopen('http://127.0.0.1:54323/', method='POST', payload=body)
    finally:
        os.remove(name)


def test_string_post():
    headers = {'CONTENT_LENGTH': '5', 'CONTENT_TYPE': 'application/octet-stream'}
    with wsgiserver(check_upload(b"12345", headers)):
        useragent = UserAgent()
        useragent.urlopen('http://127.0.0.1:54323/', method='POST', payload="12345")


def test_bytes_post():
    headers = {'CONTENT_LENGTH': '5', 'CONTENT_TYPE': 'application/octet-stream'}
    with wsgiserver(check_upload(b"12345", headers)):
        useragent = UserAgent()
        useragent.urlopen('http://127.0.0.1:54323/', method='POST', payload=b"12345")


def test_redirect():
    with wsgiserver(check_redirect()):
        useragent = UserAgent()
        assert b"redirected" == useragent.urlopen('http://127.0.0.1:54323/').read()
