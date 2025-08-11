#!/usr/bin/env python3
import http.server
import logging
import socketserver
import threading
from pathlib import Path
from typing import Tuple

log = logging.getLogger("LiveRota.serve")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info("HTTP %s - %s", self.address_string(), fmt % args)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_http_server(directory: Path, port: int) -> Tuple[http.server.HTTPServer, threading.Thread]:
    directory.mkdir(parents=True, exist_ok=True)
    Handler = lambda *a, **kw: QuietHandler(*a, directory=str(directory), **kw)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    log.info("Serving %s on port %d ...", directory, port)

    t = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.5}, daemon=True)
    t.start()
    return httpd, t


def stop_http_server(httpd: http.server.HTTPServer):
    try:
        httpd.shutdown()
    finally:
        httpd.server_close()
        log.info("HTTP server stopped")
