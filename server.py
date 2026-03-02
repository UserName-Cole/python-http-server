# Imports
import http.server
import mimetypes
import urllib.parse
import json
import datetime
import logging
import http.cookies
import socketserver
import ssl

logging.basicConfig(filename="server.log", level=logging.INFO, format="%(asctime)s %(message)s")

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

class HandlerClass(http.server.BaseHTTPRequestHandler):

    # Log requests to file instead of terminal
    def log_message(self, format, *args):
        logging.info(format % args)

    # Handle GET requests
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())
        # API endpoint - returns current time as JSON
        elif self.path == "/api/time":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"time": datetime.datetime.now().isoformat()}).encode("utf-8"))
        # API endpoint - returns client info from request headers
        elif self.path == "/api/info":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"User-Agent": self.headers["User-Agent"], "Accept-Language": self.headers["Accept-Language"], "Authorization": self.headers.get("Authorization")}).encode("utf-8"))
        # Set a cookie in the browser
        elif self.path == "/set-cookie":
            self.send_response(200)
            self.send_header("Set-Cookie", "username=cole")
            self.end_headers()
        # Read and return the cookie
        elif self.path == "/get-cookie":
            self.send_response(200)
            cookie = http.cookies.SimpleCookie(self.headers.get("Cookie"))
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"User": cookie["username"].value}).encode("utf-8"))
        # Permanent redirect to homepage
        elif self.path == "/old":
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()
        # Serve static files
        else:
            try:
                file_path = urllib.parse.urlparse(self.path).path
                print(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
                file_name = file_path.strip("/")
                with open(file_name, "rb") as f:
                    content = f.read()
                self.send_response(200)
                file_type = mimetypes.guess_type(self.path)
                self.send_header("Content-type", file_type[0])
                self.end_headers()
                self.wfile.write(content)
            # Return 404 page if file not found
            except FileNotFoundError:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                with open("404.html", "rb") as f:
                    self.wfile.write(f.read())

    # Handle POST requests - reads and logs form data
    def do_POST(self):
        body = (self.rfile.read(int(self.headers["Content-Length"]))).decode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.log_message("%s", urllib.parse.parse_qs(body))
        self.wfile.write(b"Received")

# Start server with SSL
server = ThreadedServer(("localhost", 8080), HandlerClass)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()