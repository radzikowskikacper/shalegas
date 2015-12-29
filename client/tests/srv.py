## @file srv.py
# @brief Backend server for test purposes, helping script to unit test client. It returns an answer for each GET and POST http query.

import os, sys

if sys.version_info[:1][0] >= 3:
    from http import server as BaseHTTPServer
else:
    import BaseHTTPServer
    from urlparse import urlparse, parse_qs
    
class MainHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        path = str(self.path)
        if 'connEcho' in path:
            self.send_header("Content-type", "text/html; charset=utf-8")
            query_components = parse_qs(urlparse(self.path).query)
            self.end_headers()
            self.wfile.write(query_components['callback'][0] + '("ala")')
        else:
            self.send_header("Content-type", "application/json;")
            self.end_headers()
            #self.wfile.write("<html><body>HELLO %s</body></html>" % str(self.path) )
            self.wfile.write("{\"ala\":\"ala\"}")
        if path == '/exitApp':
            os._exit(0)

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json;")
        self.end_headers()
        #self.wfile.write("<html><body>HELLO %s</body></html>" % str(self.path) )
        self.wfile.write("{\"ala\":\"ala\"}")

server_address = ('127.0.0.1', 50008)
httpd = BaseHTTPServer.HTTPServer(server_address, MainHandler)

sa = httpd.socket.getsockname()
httpd.serve_forever()
