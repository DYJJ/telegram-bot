from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Bot

# 从环境变量获取Token
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA")

# 设置Webhook的处理函数
async def set_webhook(request):
    bot = Bot(token=TOKEN)
    webhook_url = f"https://{request.headers.get('host')}/api/webhook"
    
    success = await bot.set_webhook(url=webhook_url)
    
    if success:
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "success", "message": f"Webhook set to {webhook_url}"})
        }
    else:
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": "Failed to set webhook"})
        }

# Vercel Serverless函数
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        from telegram import Bot
        import asyncio
        
        # 使用asyncio运行协程
        result = asyncio.run(set_webhook(self))
        
        self.wfile.write(result["body"].encode()) 