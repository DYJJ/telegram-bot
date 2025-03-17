from http.server import BaseHTTPRequestHandler
import json
import os
import requests

# 从环境变量获取Token
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# 发送消息到Telegram
def send_telegram_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload)
    return response.json()

# 处理搜索命令
def handle_search_command(chat_id, query):
    if not query:
        return send_telegram_message(chat_id, "请输入要搜索的关键词，例如：/search Python 教程")
    
    try:
        from googlesearch import search
        # 获取前5个搜索结果
        search_results = list(search(query, num_results=5))
        
        if search_results:
            response = f"搜索 '{query}' 的结果：\n\n"
            for i, url in enumerate(search_results, 1):
                response += f"{i}. {url}\n"
        else:
            response = f"抱歉，没有找到与 '{query}' 相关的结果。"
        
        return send_telegram_message(chat_id, response)
    except Exception as e:
        error_msg = f"搜索时发生错误: {str(e)}"
        return send_telegram_message(chat_id, error_msg)

# 处理收到的消息
def process_update(update_data):
    # 提取消息数据
    message = update_data.get("message")
    if not message:
        return {"status": "error", "message": "No message in update"}
    
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return {"status": "error", "message": "No chat_id found"}
    
    text = message.get("text", "")
    
    # 处理命令
    if text.startswith("/start"):
        response = "你好，我是你的 Telegram 机器人！\n你可以：\n1. 直接发消息给我\n2. 使用 /search 关键词 来搜索"
        send_telegram_message(chat_id, response)
    elif text.startswith("/search"):
        # 提取搜索词
        query = text.replace("/search", "").strip()
        handle_search_command(chat_id, query)
    else:
        # 回显用户消息
        response = f"你说的是: {text}"
        send_telegram_message(chat_id, response)
    
    return {"status": "success"}

# 设置Webhook
def set_webhook(host):
    webhook_url = f"https://{host}/api/webhook"
    set_webhook_url = f"{API_URL}/setWebhook?url={webhook_url}"
    response = requests.get(set_webhook_url)
    return response.json()

# Vercel Serverless函数
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # 获取当前域名
        host = self.headers.get('host')
        
        # 设置webhook
        result = set_webhook(host)
        
        self.wfile.write(json.dumps({
            "status": "success" if result.get("ok") else "error",
            "message": f"Webhook设置结果: {result}",
            "webhook_url": f"https://{host}/api/webhook"
        }).encode())
    
    def do_POST(self):
        # 获取请求体内容
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # 设置响应头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            # 记录接收到的数据
            print(f"收到Telegram更新: {post_data.decode('utf-8')}")
            
            # 解析JSON数据
            update_data = json.loads(post_data.decode('utf-8'))
            
            # 处理消息
            result = process_update(update_data)
            
            # 返回结果
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            error_message = f"处理Webhook时出错: {str(e)}"
            print(error_message)
            self.wfile.write(json.dumps({
                "status": "error", 
                "message": error_message
            }).encode()) 