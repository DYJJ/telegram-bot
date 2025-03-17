from http.server import BaseHTTPRequestHandler
import json
import os
import sys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # 收集调试信息
        debug_info = {
            "environment": {
                "TELEGRAM_TOKEN": os.environ.get("TELEGRAM_TOKEN", "未设置"),
                "VERCEL_ENV": os.environ.get("VERCEL_ENV", "未设置"),
                "VERCEL_URL": os.environ.get("VERCEL_URL", "未设置"),
                "PYTHON_VERSION": sys.version,
                "PATH": os.environ.get("PATH", "未设置")
            },
            "headers": {
                key: value for key, value in self.headers.items()
            },
            "request": {
                "method": self.command,
                "path": self.path,
                "version": self.request_version,
            }
        }
        
        # 返回调试信息
        self.wfile.write(json.dumps(debug_info, indent=2).encode()) 