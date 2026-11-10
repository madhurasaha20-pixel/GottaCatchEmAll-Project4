import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import pytest
from frontend.api_client import ask_api, APIError

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0'))
        body=json.loads(self.rfile.read(size))
        if self.path=='/bad-json':
            content=b'{not json';code=200
        elif self.path=='/bad-shape':
            content=b'{"kind":"answer"}';code=200
        elif self.path=='/error':
            content=b'{"detail":"error"}';code=503
        else:
            content=json.dumps({'kind':'answer','text':body['question'], 'sources':[{'title':'dex','url':'javascript:alert(1)'}]}).encode();code=200
        self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    def log_message(self, *args): pass

@pytest.fixture(scope='module')
def endpoint():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    try: yield f'http://127.0.0.1:{server.server_port}'
    finally: server.shutdown();server.server_close();worker.join(timeout=3)

@pytest.mark.parametrize('url',['','localhost:8000/ask','ftp://localhost/ask'])
def test_invalid_endpoint_rejected(url):
    with pytest.raises(APIError, match='complete HTTP or HTTPS'): ask_api(url,'hello',4)

def test_real_http_round_trip(endpoint):
    assert ask_api(endpoint+'/ask','Pikachu',4)['text']=='Pikachu'

def test_unsafe_source_url_removed(endpoint):
    assert 'url' not in ask_api(endpoint+'/ask','Pikachu',4)['sources'][0]

def test_invalid_json_rejected(endpoint):
    with pytest.raises(APIError,match='valid JSON'):ask_api(endpoint+'/bad-json','hi',4)

def test_invalid_response_rejected(endpoint):
    with pytest.raises(APIError,match='nonempty'):ask_api(endpoint+'/bad-shape','hi',4)

def test_http_error_rejected(endpoint):
    with pytest.raises(APIError,match='HTTP 503'):ask_api(endpoint+'/error','hi',4)
