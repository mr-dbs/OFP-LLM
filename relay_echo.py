"""
relay_echo.py - the simplest possible relay, for testing the engine bridge.

It listens on this machine only (127.0.0.1:8777). Whatever the game sends,
it prints and sends straight back. No model involved yet.

Run:   python relay_echo.py        (leave the window open; Ctrl+C to stop)
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8777


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        text = self.rfile.read(length).decode("utf-8", "replace")
        print("game said:", text)
        reply = ("relay got: " + text).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("relay listening on http://%s:%d/  (Ctrl+C to stop)" % (HOST, PORT))
    try:
        HTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nrelay stopped")
