from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import re
import urllib.parse

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
    "科技": ["https://t.me/technology_cn", "https://t.me/tech_news_zh"]
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

*使用示例*：
- 搜索Python教程：`/search Python 教程`
- 浏览推荐群组：`/group`
- 查看影视分类群组：`/group 影视`
- 搜索电影相关群组：`/group 电影`
- 直接搜索任何群组：`/jump 资源分享`
    """
    return send_telegram_message(chat_id, help_text, parse_mode="Markdown")

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
        response = "你好，我是你的 Telegram 资源搜索机器人！\n\n你可以：\n1. 直接发消息给我\n2. 使用 /search 关键词 进行网络搜索\n3. 使用 /group 查看推荐资源群组\n4. 使用 /jump 关键词 搜索任何Telegram群组\n\n输入 /help 查看所有命令"
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
    else:
        # 尝试将直接消息作为群组搜索处理
        query = text.strip()
        if query:
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