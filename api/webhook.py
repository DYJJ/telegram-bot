from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import re
import urllib.parse
import uuid
import gzip
import subprocess
import tempfile
import io
from telegram import Update
from telegram.ext import CallbackContext

# 从环境变量获取Token
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# 常用资源群组列表 - 作为推荐使用
RESOURCE_GROUPS = {
    "影视": [
        {"name": "TG影视资源群", "link": "https://t.me/TG_Movie_Chatroom", "description": "最新电影电视剧资源分享"},
        {"name": "4K影视资源", "link": "https://t.me/Remux_2160P", "description": "4K高清电影分享"},
        {"name": "蓝光影视", "link": "https://t.me/beyondHD", "description": "蓝光原盘电影资源"}
    ],
    "学习": [
        {"name": "编程学习", "link": "https://t.me/coding_learning", "description": "各类编程语言学习资源"},
        {"name": "英语学习", "link": "https://t.me/english_learning_share", "description": "英语学习资料分享"},
        {"name": "考研交流", "link": "https://t.me/kaoyan_discuss", "description": "考研经验和资料分享"}
    ],
    "软件": [
        {"name": "软件分享", "link": "https://t.me/software_share", "description": "各平台实用软件分享"},
        {"name": "破解软件", "link": "https://t.me/cracked_software", "description": "破解版软件资源"},
        {"name": "MacOS软件", "link": "https://t.me/mac_software", "description": "Mac平台软件分享"}
    ],
    "音乐": [
        {"name": "无损音乐", "link": "https://t.me/flac_music", "description": "FLAC无损音乐资源"},
        {"name": "音乐分享", "link": "https://t.me/music_share_group", "description": "各类音乐资源分享"}
    ],
    "游戏": [
        {"name": "游戏交流", "link": "https://t.me/game_discussion", "description": "游戏资讯与资源分享"},
        {"name": "Steam游戏", "link": "https://t.me/steam_games", "description": "Steam平台游戏资源"}
    ],
    "表情包": [
        {"name": "表情包中心", "link": "https://t.me/stickers_gallery", "description": "各类精选表情包资源"},
        {"name": "动漫表情", "link": "https://t.me/anime_stickers_channel", "description": "动漫角色表情包"},
        {"name": "可爱表情", "link": "https://t.me/cute_stickers_collection", "description": "可爱风格表情包合集"},
        {"name": "meme表情", "link": "https://t.me/meme_stickers_share", "description": "热门meme梗表情包"}
    ]
}

# 热门Telegram群组关键词映射
# 这些关键词会自动引导用户到相关群组
KEYWORD_TO_GROUP = {
    "电影": ["https://t.me/joinchat/AAAAAEhkwtQjOUTLamnjgQ", "https://t.me/hao4k_movie"],
    "剧集": ["https://t.me/tvshows_discuss", "https://t.me/tvb_drama"],
    "音乐": ["https://t.me/musicsharing", "https://t.me/flac_cngroup"],
    "游戏": ["https://t.me/game_center", "https://t.me/steam_games_share"],
    "学习": ["https://t.me/study_online", "https://t.me/languagelearning"],
    "编程": ["https://t.me/codinghelp", "https://t.me/pythonzh"],
    "资源": ["https://t.me/resources_sharing", "https://t.me/all_resources"],
    "苹果": ["https://t.me/apple_cn", "https://t.me/ios_dev"],
    "安卓": ["https://t.me/android_cn", "https://t.me/android_dev"],
    "破解": ["https://t.me/cracked_apps", "https://t.me/vip_software"],
    "书籍": ["https://t.me/ebookz", "https://t.me/book_share_group"],
    "壁纸": ["https://t.me/wallpapers4k", "https://t.me/wallpaper_share"],
    "新闻": ["https://t.me/news_cn", "https://t.me/worldnews_zh"],
    "科技": ["https://t.me/technology_cn", "https://t.me/tech_news_zh"],
    "表情包": ["https://t.me/addbstickers", "https://t.me/stickers", "https://t.me/stickerscn"]
}

# Telegram搜索API列表
TG_SEARCH_APIS = [
    "https://tg-channel-search.vercel.app/api/search",
    "https://tg-web-app.vercel.app/api/search"
]

# 发送消息到Telegram (支持链接格式)
def send_telegram_message(chat_id, text, parse_mode=None):
    url = f"{API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    response = requests.post(url, json=payload)
    return response.json()

# 直接搜索Telegram公共群组
def search_telegram_groups(query, limit=5):
    results = []
    
    # 尝试关键词映射快速匹配
    query_lower = query.lower()
    for keyword, groups in KEYWORD_TO_GROUP.items():
        if keyword in query_lower:
            for group_url in groups:
                # 提取群组用户名
                username = group_url.split('/')[-1]
                results.append({
                    "name": f"{keyword.capitalize()}相关群组",
                    "link": group_url,
                    "description": f"关键词'{keyword}'匹配的Telegram群组",
                    "source": "关键词匹配"
                })
                if len(results) >= limit:
                    return results
    
    # 使用Telegram搜索API
    for api_url in TG_SEARCH_APIS:
        try:
            encoded_query = urllib.parse.quote(query)
            response = requests.get(f"{api_url}?q={encoded_query}&limit={limit}")
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    for item in data["results"]:
                        group_link = f"https://t.me/{item.get('username')}" if item.get('username') else None
                        if group_link and item.get('title'):
                            results.append({
                                "name": item.get('title'),
                                "link": group_link,
                                "description": item.get('description', '公共Telegram群组或频道'),
                                "source": "Telegram搜索"
                            })
                            if len(results) >= limit:
                                return results
        except Exception as e:
            print(f"API搜索错误: {str(e)}")
            continue
    
    # 如果没有找到结果，尝试构建搜索链接
    if not results:
        # 创建通用Telegram搜索链接
        tg_search_link = f"https://t.me/search?query={urllib.parse.quote(query)}"
        results.append({
            "name": f"搜索 '{query}'",
            "link": tg_search_link,
            "description": "在Telegram中搜索这个关键词",
            "source": "直接搜索"
        })
    
    return results

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

# 处理直接跳转命令
def handle_jump_command(chat_id, query):
    if not query:
        return send_telegram_message(chat_id, "请输入要查找的群组名称或关键词，例如：/jump 电影资源")
    
    # 搜索Telegram群组
    telegram_groups = search_telegram_groups(query)
    
    if telegram_groups:
        response = f"找到与 '{query}' 相关的群组：\n\n"
        for i, group in enumerate(telegram_groups, 1):
            response += f"{i}. [{group['name']}]({group['link']})\n   {group['description']}\n\n"
    else:
        response = f"抱歉，没有找到与 '{query}' 相关的群组。"
    
    return send_telegram_message(chat_id, response, parse_mode="Markdown")

# 处理群组搜索命令（原有功能，现在提供预设群组）
def handle_group_command(chat_id, query=""):
    # 如果没有提供查询词，显示所有分类
    if not query:
        categories = list(RESOURCE_GROUPS.keys())
        response = "选择一个资源分类，或输入关键词搜索群组：\n\n"
        for category in categories:
            response += f"• /group {category}\n"
        response += "\n您也可以直接搜索，例如：/group 电影"
        response += "\n\n如需更广泛搜索Telegram群组，请使用：\n/jump [关键词] - 例如：/jump 动漫资源"
        return send_telegram_message(chat_id, response)
    
    # 检查是否是特定分类的请求
    if query in RESOURCE_GROUPS:
        category = query
        groups = RESOURCE_GROUPS[category]
        response = f"【{category}】分类的推荐资源群组：\n\n"
        for group in groups:
            response += f"• [{group['name']}]({group['link']})\n  {group['description']}\n\n"
        response += "如需更多群组，请使用：\n/jump {查询词} - 直接搜索Telegram公共群组"
        return send_telegram_message(chat_id, response, parse_mode="Markdown")
    
    # 关键词搜索所有群组
    results = []
    for category, groups in RESOURCE_GROUPS.items():
        for group in groups:
            # 在名称和描述中搜索关键词
            if (re.search(query, group['name'], re.IGNORECASE) or 
                re.search(query, group['description'], re.IGNORECASE)):
                results.append((category, group))
    
    # 生成搜索结果
    if results:
        response = f"推荐的 '{query}' 相关群组：\n\n"
        for category, group in results:
            response += f"• [{group['name']}]({group['link']}) 【{category}】\n  {group['description']}\n\n"
    else:
        # 如果没有在预设群组中找到，尝试直接搜索Telegram
        telegram_groups = search_telegram_groups(query)
        if telegram_groups:
            response = f"找到与 '{query}' 相关的群组：\n\n"
            for i, group in enumerate(telegram_groups, 1):
                response += f"{i}. [{group['name']}]({group['link']})\n   {group['description']}\n\n"
        else:
            response = f"抱歉，没有找到包含 '{query}' 的资源群组。\n\n请尝试使用 /jump {query} 命令更广泛地搜索。"
    
    return send_telegram_message(chat_id, response, parse_mode="Markdown")

# 处理表情包命令
def handle_sticker_command(chat_id, query=""):
    if not query:
        # 显示表情包分类或热门表情包
        response = """
*表情包搜索*

您可以：
• 输入关键词搜索表情包，例如：/sticker 猫咪
• 浏览我们推荐的表情包资源：/group 表情包
• 直接访问Telegram表情包商店：[Stickers Store](https://t.me/addstickers)

*热门表情包类型*：
• 动漫表情包 - `/sticker 动漫`
• 可爱表情包 - `/sticker 可爱`
• 明星表情包 - `/sticker 明星`
• 综艺梗表情包 - `/sticker 综艺` 
• 表情包制作 - `/sticker 制作`
        """
        return send_telegram_message(chat_id, response, parse_mode="Markdown")
    
    # 搜索相关表情包资源
    results = []
    
    # 先从预设表情包分类中查找
    if "表情包" in RESOURCE_GROUPS:
        for group in RESOURCE_GROUPS["表情包"]:
            if (re.search(query, group['name'], re.IGNORECASE) or 
                re.search(query, group['description'], re.IGNORECASE)):
                results.append(("表情包", group))
    
    # 通过关键词匹配
    if "表情包" in KEYWORD_TO_GROUP and query in ["表情", "贴纸", "sticker", "emoji"]:
        for group_url in KEYWORD_TO_GROUP["表情包"]:
            username = group_url.split('/')[-1]
            results.append(("表情包", {
                "name": f"Telegram表情包资源",
                "link": group_url,
                "description": "官方表情包频道或收集群组"
            }))
    
    # 使用Telegram搜索API找表情包
    sticker_keywords = f"{query} 表情包 stickers"
    telegram_groups = search_telegram_groups(sticker_keywords, limit=3)
    
    # 生成结果
    if results or telegram_groups:
        response = f"*{query}* 相关表情包资源：\n\n"
        
        # 添加预设结果
        for category, group in results:
            response += f"• [{group['name']}]({group['link']})\n  {group['description']}\n\n"
        
        # 添加搜索结果
        for group in telegram_groups:
            response += f"• [{group['name']}]({group['link']})\n  {group['description']}\n\n"
        
        # 添加直接使用指南
        response += "\n*使用表情包*：\n"
        response += "1. 点击上方链接进入群组/频道\n"
        response += "2. 查看并选择喜欢的表情包\n"
        response += "3. 点击'Add Sticker'添加到您的收藏\n"
        response += "4. 在任何聊天中点击表情按钮使用\n"
        
        # 添加表情包制作指南链接
        response += "\n想制作自己的表情包？使用 @Stickers 机器人"
    else:
        response = f"抱歉，没有找到 '{query}' 相关的表情包资源。\n\n请尝试其他关键词，或直接访问 [Telegram表情商店](https://t.me/addstickers)"
    
    return send_telegram_message(chat_id, response, parse_mode="Markdown")

# 处理帮助命令
def handle_help_command(chat_id):
    help_text = """
*可用命令列表*：

• /start - 启动机器人
• /help - 显示帮助信息
• /search [关键词] - 网络搜索
• /group - 浏览推荐资源群组
• /group [分类名] - 查看特定分类的推荐群组
• /group [关键词] - 搜索相关群组（包括推荐群组）
• /jump [关键词] - 直接搜索并跳转到Telegram公共群组
• /sticker [关键词] - 搜索表情包资源

*表情包下载功能*：
• 直接发送任意表情包给机器人，它会自动下载并转换格式
• 点击「下载整个表情包」按钮可获取完整表情包集合

*使用示例*：
- 搜索Python教程：`/search Python 教程`
- 浏览推荐群组：`/group`
- 查看影视分类群组：`/group 影视`
- 搜索电影相关群组：`/group 电影`
- 直接搜索任何群组：`/jump 资源分享`
- 查找猫咪表情包：`/sticker 猫咪`
- 下载表情包：发送任意表情包给机器人
    """
    return send_telegram_message(chat_id, help_text, parse_mode="Markdown")

# 处理收到的消息
def process_update(update_data):
    # 提取消息数据
    message = update_data.get("message")
    if not message:
        callback_query = update_data.get("callback_query")
        if callback_query:
            # 处理回调查询（表情包下载按钮点击）
            return process_callback_query(callback_query)
        return {"status": "error", "message": "No message or callback_query in update"}
    
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return {"status": "error", "message": "No chat_id found"}
    
    # 处理表情包消息
    sticker = message.get("sticker")
    if sticker:
        return handle_sticker_message(chat_id, sticker, message)
    
    text = message.get("text", "")
    
    # 处理命令
    if text.startswith("/start"):
        response = "你好，我是你的 Telegram 资源搜索机器人！\n\n你可以：\n1. 直接发消息给我\n2. 使用 /search 关键词 进行网络搜索\n3. 使用 /group 查看推荐资源群组\n4. 使用 /jump 关键词 搜索任何Telegram群组\n5. 使用 /sticker 关键词 查找表情包资源\n6. 直接发送表情包给我下载\n\n输入 /help 查看所有命令"
        send_telegram_message(chat_id, response)
    elif text.startswith("/help"):
        handle_help_command(chat_id)
    elif text.startswith("/search"):
        # 提取搜索词
        query = text.replace("/search", "").strip()
        handle_search_command(chat_id, query)
    elif text.startswith("/group"):
        # 提取群组搜索词
        query = text.replace("/group", "").strip()
        handle_group_command(chat_id, query)
    elif text.startswith("/jump"):
        # 提取直接搜索词
        query = text.replace("/jump", "").strip()
        handle_jump_command(chat_id, query)
    elif text.startswith("/sticker"):
        # 处理表情包请求
        query = text.replace("/sticker", "").strip()
        handle_sticker_command(chat_id, query)
    else:
        # 尝试将直接消息作为群组搜索处理
        query = text.strip()
        if query:
            # 检查是否是表情相关请求
            if any(keyword in query.lower() for keyword in ["表情", "贴纸", "sticker", "emoji", "表情包"]):
                handle_sticker_command(chat_id, query)
            else:
                handle_jump_command(chat_id, query)
        else:
            response = "请输入要搜索的群组关键词，或使用 /help 查看所有命令"
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

# 处理回调查询（表情包下载按钮点击）
def process_callback_query(callback_query):
    query_id = callback_query.get("id")
    query_data = callback_query.get("data")
    message = callback_query.get("message")
    
    if not query_id or not message:
        return {"status": "error", "message": "Invalid callback query"}
    
    chat_id = message.get("chat", {}).get("id")
    
    # 处理表情包下载按钮点击
    if query_data and query_data.startswith("download_set:"):
        set_name = query_data.split(":")[1]
        # 直接提供添加贴纸集的链接
        set_url = f"https://t.me/addstickers/{set_name}"
        send_telegram_message(chat_id, f"请访问以下链接查看和添加完整表情包：\n{set_url}")
    
    # 应答回调查询
    answer_callback_query(query_id)
    
    return {"status": "success"}

# 回复回调查询
def answer_callback_query(query_id, text=""):
    url = f"{API_URL}/answerCallbackQuery"
    payload = {
        "callback_query_id": query_id,
        "text": text
    }
    requests.post(url, json=payload)

# 处理贴纸消息
def handle_sticker_message(chat_id, sticker, message):
    message_id = message.get("message_id")
    print(f"\n开始处理新的表情包请求...")
    print(f"表情包信息: {sticker}")
    
    # 发送处理中消息
    processing_msg = send_telegram_message(chat_id, "正在处理表情包...")
    processing_msg_id = processing_msg.get("result", {}).get("message_id")
    
    # 用于存储临时文件路径的列表
    temp_files = []
    
    try:
        # 获取贴纸文件信息
        file_id = sticker.get("file_id")
        if not file_id:
            error_msg = "无法获取表情包文件ID，请重试"
            print(error_msg)
            edit_message(chat_id, processing_msg_id, error_msg)
            return {"status": "error", "message": "No file_id in sticker"}
        
        # 获取文件信息
        print(f"获取文件信息: {file_id}")
        file_info = get_file_info(file_id)
        print(f"文件信息响应: {file_info}")
        
        if not file_info.get("ok"):
            error_msg = "获取文件信息失败，请重试"
            print(error_msg)
            edit_message(chat_id, processing_msg_id, error_msg)
            return {"status": "error", "message": "Failed to get file info"}
        
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            error_msg = "无法获取文件路径，请重试"
            print(error_msg)
            edit_message(chat_id, processing_msg_id, error_msg)
            return {"status": "error", "message": "No file_path in file info"}
        
        # 下载文件到临时目录
        try:
            print(f"开始下载文件: {file_path}")
            download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            print(f"下载 URL: {download_url}")
            local_file_path = download_file(download_url)
            temp_files.append(local_file_path)
            print(f"文件下载成功: {local_file_path}")
            print(f"文件大小: {os.path.getsize(local_file_path) if os.path.exists(local_file_path) else 'file not found'} bytes")
            edit_message(chat_id, processing_msg_id, "文件已下载，正在转换...")
        except Exception as e:
            error_msg = f"下载文件失败: {str(e)}"
            print(error_msg)
            edit_message(chat_id, processing_msg_id, error_msg)
            return {"status": "error", "message": f"Failed to download file: {str(e)}"}
        
        try:
            # 确定文件类型和输出格式
            input_extension = os.path.splitext(file_path)[1].lower().replace(".", "")
            print(f"输入文件扩展名: {input_extension}")
            
            if input_extension == "webp":
                output_format = "png"
            else:  # tgs 或其他格式
                output_format = "gif"
            
            print(f"输出格式: {output_format}")
            
            # 创建临时输出文件
            output_temp = tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False)
            output_temp.close()
            temp_files.append(output_temp.name)
            print(f"创建输出临时文件: {output_temp.name}")
            
            # 转换文件
            success = False
            if input_extension == "webp":
                try:
                    print("开始转换 WEBP 文件...")
                    result = subprocess.run(
                        ["ffmpeg", "-y", "-i", local_file_path, output_temp.name],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        success = True
                        print("WEBP 转换成功")
                    else:
                        print(f"WEBP 转换失败: {result.stderr}")
                        edit_message(chat_id, processing_msg_id, "WEBP 转换失败，请重试")
                except subprocess.CalledProcessError as e:
                    print(f"WEBP 转换失败: {e.stderr}")
                    edit_message(chat_id, processing_msg_id, "WEBP 转换失败，请重试")
            elif input_extension == "tgs":
                print("开始转换 TGS 文件...")
                edit_message(chat_id, processing_msg_id, "正在转换 TGS 文件...")
                success = convert_tgs_to_gif(local_file_path, output_temp.name)
                print(f"TGS 转换结果: {'成功' if success else '失败'}")
            else:
                try:
                    print("开始转换其他格式文件...")
                    result = subprocess.run(
                        ["ffmpeg", "-y", "-i", local_file_path, "-vf", "scale=-1:-1", "-r", "20", output_temp.name],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        success = True
                        print("其他格式转换成功")
                    else:
                        print(f"其他格式转换失败: {result.stderr}")
                        edit_message(chat_id, processing_msg_id, "文件转换失败，请重试")
                except subprocess.CalledProcessError as e:
                    print(f"其他格式转换失败: {e.stderr}")
                    edit_message(chat_id, processing_msg_id, "文件转换失败，请重试")
            
            if success:
                print("开始发送转换后的文件...")
                # 发送转换后的文件
                send_document(chat_id, output_temp.name, reply_to_message_id=message_id)
                
                # 添加下载整套表情包的选项
                set_name = sticker.get("set_name")
                if set_name:
                    set_url = f"https://t.me/addstickers/{set_name}"
                    response = "转换完成！\n\n要获取整个表情包，请访问:\n" + set_url
                else:
                    response = "转换完成！"
                
                edit_message(chat_id, processing_msg_id, response)
                print("处理完成")
            else:
                error_msg = "转换失败，请稍后重试。如果问题持续存在，请联系管理员。"
                print(error_msg)
                edit_message(chat_id, processing_msg_id, error_msg)
            
        finally:
            # 清理所有临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        print(f"清理临时文件: {temp_file}")
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")
        
        return {"status": "success" if success else "error"}
        
    except Exception as e:
        error_msg = f"处理表情包时发生错误: {str(e)}"
        print(error_msg)
        edit_message(chat_id, processing_msg_id, error_msg)
        
        # 确保在发生错误时也清理临时文件
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    print(f"清理临时文件: {temp_file}")
                    os.unlink(temp_file)
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")
        
        return {"status": "error", "message": error_msg}

# 获取文件信息
def get_file_info(file_id):
    url = f"{API_URL}/getFile"
    payload = {"file_id": file_id}
    response = requests.post(url, json=payload)
    return response.json()

# 下载文件
def download_file(url):
    """下载文件到临时目录"""
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        raise Exception(f"下载失败，状态码：{response.status_code}")
    
    # 使用临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(response.content)
    temp_file.close()
    
    return temp_file.name

# 转换表情包
def convert_sticker(input_path, output_path, input_extension):
    try:
        import subprocess
        
        # 使用 ffmpeg 转换文件
        if input_extension == "webp":
            # WebP 转 PNG
            subprocess.run(["ffmpeg", "-y", "-i", input_path, output_path], check=True)
        elif input_extension == "tgs":
            # TGS 转 GIF (需要特殊处理)
            subprocess.run(["ffmpeg", "-y", "-i", input_path, "-vf", "scale=-1:-1", "-r", "20", output_path], check=True)
        else:
            # 其他格式转换
            subprocess.run(["ffmpeg", "-y", "-i", input_path, "-vf", "scale=-1:-1", "-r", "20", output_path], check=True)
        
        return True
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

# 发送文件
def send_document(chat_id, file_path, reply_to_message_id=None):
    url = f"{API_URL}/sendDocument"
    
    files = {
        'document': open(file_path, 'rb')
    }
    
    data = {
        'chat_id': chat_id
    }
    
    if reply_to_message_id:
        data['reply_to_message_id'] = reply_to_message_id
    
    response = requests.post(url, data=data, files=files)
    return response.json()

# 编辑消息
def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"{API_URL}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    response = requests.post(url, json=payload)
    return response.json()

# 清理文件
def cleanup_files(*file_paths):
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"清理文件失败: {str(e)}")

# 处理下载整个表情包集合
def handle_download_sticker_set(chat_id, set_name, query_id, message):
    # 发送处理消息
    msg = send_telegram_message(chat_id, f"正在处理表情包集合 {set_name}，请稍候...")
    msg_id = msg.get("result", {}).get("message_id")
    
    try:
        # 获取表情包集合信息
        sticker_set = get_sticker_set(set_name)
        if not sticker_set.get("ok"):
            edit_message(chat_id, msg_id, f"获取表情包集合失败: {sticker_set.get('description', '未知错误')}")
            return
        
        stickers = sticker_set.get("result", {}).get("stickers", [])
        if not stickers:
            edit_message(chat_id, msg_id, f"表情包集合 {set_name} 没有贴纸")
            return
        
        # 更新消息显示进度
        edit_message(chat_id, msg_id, f"正在下载 {len(stickers)} 个表情，请稍候...")
        
        # 创建临时目录
        import time
        folder_path = f"storage/tmp/stickers_{int(time.time() * 1000000)}"
        os.makedirs(folder_path, exist_ok=True)
        
        # 下载并转换所有表情
        finished = 0
        failed = 0
        
        for sticker in stickers:
            try:
                # 获取文件信息
                file_id = sticker.get("file_id")
                file_unique_id = sticker.get("file_unique_id")
                
                file_info = get_file_info(file_id)
                file_path = file_info.get("result", {}).get("file_path")
                
                # 下载文件
                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                local_file_path = download_file(download_url)
                
                # 确定输出格式
                input_extension = os.path.splitext(file_path)[1].lower().replace(".", "")
                output_format = "png" if input_extension == "webp" else "gif"
                output_path = f"{folder_path}/{file_unique_id}.{output_format}"
                
                # 转换文件
                convert_success = convert_sticker(local_file_path, output_path, input_extension)
                
                # 清理原始文件
                os.remove(local_file_path)
                
                if convert_success:
                    finished += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"处理表情 {file_id} 时出错: {str(e)}")
                failed += 1
            
            # 每处理5个更新一次进度
            if (finished + failed) % 5 == 0:
                edit_message(chat_id, msg_id, f"正在下载: {finished + failed}/{len(stickers)}")
        
        # 创建 ZIP 文件
        import zipfile
        zip_path = f"storage/tmp/{set_name}_{int(time.time())}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))
        
        # 更新消息
        edit_message(chat_id, msg_id, f"已转换 {finished} 个表情，失败 {failed} 个，正在上传...")
        
        # 发送 ZIP 文件
        file_size = os.path.getsize(zip_path)
        file_size_mb = file_size // (1024 * 1024)
        
        send_document(chat_id, zip_path, caption=f"表情包集合 {set_name} ({file_size_mb}MB)")
        
        # 更新消息
        edit_message(chat_id, msg_id, f"已成功上传表情包集合 {set_name}，共 {finished} 个表情，失败 {failed} 个")
        
        # 清理文件
        import shutil
        shutil.rmtree(folder_path, ignore_errors=True)
        os.remove(zip_path)
        
    except Exception as e:
        error_msg = f"处理表情包集合时发生错误: {str(e)}"
        edit_message(chat_id, msg_id, error_msg)

# 获取表情包集合
def get_sticker_set(name):
    url = f"{API_URL}/getStickerSet"
    payload = {"name": name}
    response = requests.post(url, json=payload)
    return response.json()

def convert_tgs_to_gif(input_path, output_path):
    """将 TGS 文件转换为 GIF"""
    temp_files = []
    print(f"开始转换 TGS 文件: {input_path} -> {output_path}")
    print(f"检查输入文件是否存在: {os.path.exists(input_path)}")
    print(f"输入文件大小: {os.path.getsize(input_path) if os.path.exists(input_path) else 'file not found'} bytes")
    
    try:
        # 1. 解压缩 TGS 文件（TGS 是 gzip 压缩的 JSON）
        try:
            print("尝试解压缩 TGS 文件...")
            with gzip.open(input_path, 'rb') as f:
                json_data = f.read()
            print(f"成功读取 JSON 数据，大小: {len(json_data)} bytes")
        except Exception as e:
            print(f"TGS 解压缩失败: {str(e)}")
            print(f"文件类型检查: {subprocess.run(['file', input_path], capture_output=True, text=True).stdout}")
            return False
        
        # 2. 保存解压后的 JSON 到临时文件
        try:
            print("创建临时 JSON 文件...")
            json_temp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
            json_temp.write(json_data)
            json_temp.close()
            temp_files.append(json_temp.name)
            print(f"临时 JSON 文件创建成功: {json_temp.name}")
            print(f"临时文件大小: {os.path.getsize(json_temp.name)} bytes")
        except Exception as e:
            print(f"创建临时 JSON 文件失败: {str(e)}")
            return False
        
        # 3. 检查系统工具
        print("\n检查系统工具:")
        for tool in ['convert', 'ffmpeg', 'lottie_convert.py']:
            result = subprocess.run(['which', tool], capture_output=True, text=True)
            print(f"{tool}: {'已安装 - ' + result.stdout.strip() if result.returncode == 0 else '未安装'}")
        
        # 4. 尝试多种转换方法
        conversion_methods = [
            # 方法1: lottie-convert.py
            {
                'name': 'lottie-convert',
                'cmd': ['lottie_convert.py', json_temp.name, output_path]
            },
            # 方法2: ImageMagick
            {
                'name': 'imagemagick',
                'cmd': [
                    'convert',
                    '-delay', '3',
                    '-loop', '0',
                    '-dispose', 'Background',
                    '-layers', 'optimize',
                    '-resize', '512x512>',
                    json_temp.name,
                    output_path
                ]
            },
            # 方法3: ffmpeg
            {
                'name': 'ffmpeg',
                'cmd': [
                    'ffmpeg', '-y',
                    '-i', input_path,
                    '-vf', 'scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color=white@0.0',
                    '-r', '30',
                    output_path
                ]
            }
        ]
        
        for method in conversion_methods:
            try:
                print(f"\n尝试使用 {method['name']} 进行转换...")
                print(f"执行命令: {' '.join(method['cmd'])}")
                result = subprocess.run(method['cmd'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"{method['name']} 转换成功")
                    print(f"检查输出文件: {os.path.exists(output_path)}")
                    if os.path.exists(output_path):
                        print(f"输出文件大小: {os.path.getsize(output_path)} bytes")
                    return True
                else:
                    print(f"{method['name']} 转换失败")
                    print(f"错误输出: {result.stderr}")
            except Exception as e:
                print(f"{method['name']} 发生未知错误: {str(e)}")
                continue
        
        print("所有转换方法都失败了")
        return False
            
    except Exception as e:
        print(f"TGS 转换过程中发生错误: {str(e)}")
        return False
    finally:
        # 清理所有临时文件
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    print(f"清理临时文件: {temp_file}")
                    os.unlink(temp_file)
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")

# 处理表情包（贴纸）消息
async def sticker_handler(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    sticker = update.message.sticker
    
    print(f"[用户: {user.username}] 发送了贴纸：{sticker.file_id}")
    sys.stdout.flush()
    
    processing_msg = await update.message.reply_text("正在处理表情包...")
    
    try:
        file = await context.bot.get_file(sticker.file_id)
        file_path = download_file(file.file_path, TOKEN)
        
        input_extension = os.path.splitext(file_path)[1].lower().replace(".", "")
        
        if input_extension == "webp":
            output_format = "png"
        else:  # tgs 或其他格式
            output_format = "gif"
        
        output_path = f"storage/tmp/convert_{uuid.uuid4().hex}.{output_format}"
        
        success = False
        if input_extension == "webp":
            subprocess.run(["ffmpeg", "-y", "-i", file_path, output_path], check=True)
            success = True
        elif input_extension == "tgs":
            success = convert_tgs_to_gif(file_path, output_path)
        else:
            subprocess.run(["ffmpeg", "-y", "-i", file_path, "-vf", "scale=-1:-1", "-r", "20", output_path], check=True)
            success = True
        
        if success:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(output_path, 'rb'),
                reply_to_message_id=update.message.message_id
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("下载整个表情包", callback_data=f"download_set:{sticker.set_name}")]
            ])
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text="转换完成！",
                reply_markup=keyboard
            )
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text="转换失败，请稍后重试。"
            )
        
        # 清理文件
        os.remove(file_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        
    except Exception as e:
        error_msg = f"处理表情包时发生错误: {str(e)}"
        print(f"[Bot] {error_msg}")
        sys.stdout.flush()
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text=error_msg
        ) 