from repo_manager import deploy

from http.server import BaseHTTPRequestHandler, HTTPServer
import json

PORT = 9000


class Handler(BaseHTTPRequestHandler):

    async def do_POST(self):
        l = int(self.headers.get("Content-Length"))
        data = self.rfile.read(l)

        payload = json.loads(data.decode())

        if payload["ref"] == "refs/heads/main":
            await deploy()

        self.send_response(200)
        self.end_headers()


HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
