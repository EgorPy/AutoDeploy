from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from repo_manager import deploy

PORT = 9000


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        l = int(self.headers.get("Content-Length"))
        data = self.rfile.read(l)

        payload = json.loads(data.decode())

        if payload["ref"] == "refs/heads/main":
            deploy()

        self.send_response(200)
        self.end_headers()


HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
