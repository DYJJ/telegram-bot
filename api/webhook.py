from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# 从环境变量获取Token
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA")

# Vercel Serverless函数
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # 获取当前域名
        host = self.headers.get('host')
        webhook_url = f"https://{host}/api/webhook"
        
        # 直接使用requests设置webhook（更简单可靠）
        set_webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        
        try:
            response = requests.get(set_webhook_url)
            result = {
                "status": "success" if response.status_code == 200 else "error",
                "message": f"Webhook设置结果: {response.text}",
                "webhook_url": webhook_url
            }
        except Exception as e:
            result = {
                "status": "error",
                "message": f"设置Webhook时出错: {str(e)}",
                "webhook_url": webhook_url
            }
        
        self.wfile.write(json.dumps(result).encode()) 