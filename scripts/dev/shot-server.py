"""개발용: 브라우저에서 렌더한 캔버스 이미지를 받아 파일로 저장하는 로컬 서버.

  python3 scripts/dev/shot-server.py        # http://localhost:8899
  fetch('http://localhost:8899/shot?name=foo', { method: 'POST', body: dataURL })
  → assets-src/shots/foo.png|jpg
"""
import base64
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets-src', 'shots')
os.makedirs(OUT, exist_ok=True)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode()
        name = parse_qs(urlparse(self.path).query).get('name', ['shot'])[0]
        head, _, b64 = data.partition(',')
        ext = 'png' if 'image/png' in head else 'jpg'
        with open(os.path.join(OUT, f'{name}.{ext}'), 'wb') as f:
            f.write(base64.b64decode(b64))
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass


HTTPServer(('127.0.0.1', 8899), Handler).serve_forever()
