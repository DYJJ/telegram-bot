import os
import json
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from googlesearch import search
from http.server import BaseHTTPRequestHandler

# 从环境变量中获取Token
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA")

# 处理 /start 命令
async def start(update: Update, context: CallbackContext) -> None:
    response = "你好，我是你的 Telegram 机器人！\n你可以：\n1. 直接发消息给我\n2. 使用 /search 关键词 来搜索"
    await update.message.reply_text(response)

# 处理搜索命令
async def search_command(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("请输入要搜索的关键词，例如：/search Python 教程")
        return
    
    query = ' '.join(context.args)
    
    try:
        # 获取前5个搜索结果
        search_results = list(search(query, num_results=5))
        
        if search_results:
            response = f"搜索 '{query}' 的结果：\n\n"
            for i, url in enumerate(search_results, 1):
                response += f"{i}. {url}\n"
        else:
            response = f"抱歉，没有找到与 '{query}' 相关的结果。"
        
        await update.message.reply_text(response)
    except Exception as e:
        error_msg = f"搜索时发生错误: {str(e)}"
        await update.message.reply_text(error_msg)

# 处理所有文本消息
async def echo(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    response = f"你说的是: {text}"
    await update.message.reply_text(response)

# 创建应用
application = Application.builder().token(TOKEN).build()

# 注册命令和消息处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("search", search_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Vercel处理函数
async def handle_update(update_data):
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)

# Serverless函数入口点
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Bot is running!'.encode())
        return

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if self.path == '/api/webhook':
            try:
                update_data = json.loads(post_data.decode('utf-8'))
                asyncio.run(handle_update(update_data))
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
        else:
            self.wfile.write(json.dumps({"status": "error", "message": "Invalid endpoint"}).encode()) 