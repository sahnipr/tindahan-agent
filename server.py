"""Local HTTP sandbox. Run python3 server.py; bind only to loopback."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from agent import Agent
from tools import Sandbox, ToolError

sandbox = Sandbox()
agent = Agent(sandbox)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError('Body must contain 1–16384 bytes')
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('Expected JSON object')
            if self.path == '/chat':
                result = {'reply': agent.reply(data['owner'], data.get('text', ''), data.get('photos'))}
            elif self.path == '/catalog':
                result = sandbox.catalog()
            elif self.path == '/stock':
                result = sandbox.stock(data['sku'])
            elif self.path == '/quote':
                result = sandbox.quote(data['owner'], data['items'])
            else:
                self.send_error(404)
                return
            status = 200
        except (ValueError, KeyError, TypeError, ToolError) as exc:
            status, result = 400, {'error': str(exc)}
        body = json.dumps(result).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print('Local sandbox: http://127.0.0.1:8000 (Ctrl+C to stop)')
    HTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
