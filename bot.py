import sys
import os
import requests
import time
import uuid
import zipfile
import shutil
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from googlesearch import search

# 你的 Bot Token
TOKEN = "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA"

# 处理 /start 命令
async def start(update: Update, context: CallbackContext) -> None:
    response = "你好，我是你的 Telegram 机器人！\n你可以：\n1. 直接发消息给我\n2. 使用 /search 关键词 来搜索\n3. 发送表情包给我来下载"
    print("[Bot] " + response)  # 打印机器人的回复
    sys.stdout.flush()
    await update.message.reply_text(response)

# 处理搜索命令
async def search_command(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("请输入要搜索的关键词，例如：/search Python 教程")
        return
    
    query = ' '.join(context.args)
    print(f"[用户: {update.message.from_user.username}] 搜索: {query}")
    sys.stdout.flush()

    try:
        # 获取前5个搜索结果
        search_results = list(search(query, num_results=5))
        
        if search_results:
            response = f"搜索 '{query}' 的结果：\n\n"
            for i, url in enumerate(search_results, 1):
                response += f"{i}. {url}\n"
        else:
            response = f"抱歉，没有找到与 '{query}' 相关的结果。"
        
        print(f"[Bot] 返回搜索结果")
        sys.stdout.flush()
        await update.message.reply_text(response)
    except Exception as e:
        error_msg = f"搜索时发生错误: {str(e)}"
        print(f"[Bot] {error_msg}")
        sys.stdout.flush()
        await update.message.reply_text(error_msg)

# 处理所有文本消息，并在控制台打印
async def echo(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user  # 获取用户信息
    text = update.message.text  # 获取用户发送的文本

    # 在终端打印用户消息，并强制刷新
    print(f"[用户: {user.username}] {text}")
    sys.stdout.flush()  # 强制刷新输出

    # 机器人回复消息
    response = f"你说的是: {text}"
    print(f"[SuperDYJ_Bot] {response}")  # 打印机器人的回复
    sys.stdout.flush()
    await update.message.reply_text(response)

# 下载文件的辅助函数
def download_file(url, token=None):
    if token and "bot.telegram.org" in url:
        url = f"{url}?file_api={token}"
    
    print(f"下载文件: {url}")
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        raise Exception(f"下载失败，状态码：{response.status_code}")
    
    # 创建临时目录（如果不存在）
    os.makedirs("storage/tmp", exist_ok=True)
    
    # 从URL获取文件扩展名
    file_ext = os.path.splitext(url.split('/')[-1])[1]
    if not file_ext:
        # 如果URL没有扩展名，尝试从内容类型获取
        content_type = response.headers.get('Content-Type', '')
        if 'image/webp' in content_type:
            file_ext = '.webp'
        elif 'application/x-tgsticker' in content_type:
            file_ext = '.tgs'
        elif 'image/' in content_type:
            file_ext = f".{content_type.split('/')[-1]}"
        else:
            # 默认扩展名
            file_ext = ''
    
    # 生成带扩展名的随机文件名
    file_name = f"storage/tmp/upload_{uuid.uuid4().hex}{file_ext}"
    
    print(f"保存文件: {file_name}")
    with open(file_name, 'wb') as f:
        f.write(response.content)
    
    return file_name

# 处理表情包（贴纸）消息
async def sticker_handler(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    sticker = update.message.sticker  # 获取贴纸信息
    
    # 在终端打印用户发送的贴纸信息
    print(f"[用户: {user.username}] 发送了贴纸：{sticker.file_id}")
    sys.stdout.flush()
    
    # 回复正在处理的消息
    processing_msg = await update.message.reply_text("正在处理表情包...")
    
    try:
        # 获取文件信息
        file = await context.bot.get_file(sticker.file_id)
        
        # 下载文件
        file_path = download_file(file.file_path, TOKEN)
        
        # 确定输出文件类型（基于输入文件类型）
        input_extension = os.path.splitext(file_path)[1].lower().replace(".", "")
        
        if input_extension == "webp":
            output_format = "png"
        else:  # tgs 或其他格式
            output_format = "gif"
        
        output_path = f"storage/tmp/convert_{uuid.uuid4().hex}.{output_format}"
        
        # 转换贴纸
        success = False
        if input_extension == "webp":
            # 使用 ImageMagick 或 ffmpeg 转换 webp 到 png
            subprocess.run(["ffmpeg", "-y", "-i", file_path, output_path], check=True)
            success = True
        elif input_extension == "tgs":
            # 使用我们的转换函数
            from api.webhook import convert_tgs_to_gif
            success = convert_tgs_to_gif(file_path, output_path)
            if not success:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg.message_id,
                    text="表情包转换失败，可能是不支持的TGS格式。我们提供了一个简单的替代图片。如果需要原始图片，请联系管理员。"
                )
                return
        else:
            # 其他格式也用 ffmpeg 转换
            subprocess.run(["ffmpeg", "-y", "-i", file_path, "-vf", "scale=-1:-1", "-r", "20", output_path], check=True)
            success = True
        
        # 发送转换后的文件
        await context.bot.send_document(
            chat_id=update.effective_chat.id, 
            document=open(output_path, 'rb'),
            reply_to_message_id=update.message.message_id
        )
        
        # 更新处理消息
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text="处理完成！"
        )
        
        # 清理临时文件
        os.remove(file_path)
        os.remove(output_path)
        
    except Exception as e:
        # 处理错误
        print(f"处理贴纸时出错: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text=f"处理失败: {str(e)}"
        )

# 处理下载整个表情包的回调查询
async def download_sticker_set(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    # 获取表情包集合名称
    set_name = query.data.split(":")[1]
    
    # 发送处理消息
    msg = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="正在处理表情包集合，请稍候...",
        reply_to_message_id=query.message.message_id
    )
    
    try:
        # 获取表情包集合信息
        sticker_set = await context.bot.get_sticker_set(set_name)
        
        # 创建临时目录
        folder_path = f"storage/tmp/stickers_{int(time.time() * 1000000)}"
        os.makedirs(folder_path, exist_ok=True)
        
        # 更新消息显示进度
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=msg.message_id,
            text=f"正在下载 {len(sticker_set.stickers)} 个表情，请稍候..."
        )
        
        # 下载并转换所有表情
        finished = 0
        failed = 0
        for sticker in sticker_set.stickers:
            try:
                # 获取文件信息
                file = await context.bot.get_file(sticker.file_id)
                
                # 下载文件
                file_path = download_file(file.file_path, TOKEN)
                
                # 确定输出文件类型
                input_extension = os.path.splitext(file_path)[1].lower().replace(".", "")
                
                if input_extension == "webp":
                    output_format = "png"
                else:  # tgs 或其他格式
                    output_format = "gif"
                
                output_path = f"{folder_path}/{sticker.file_unique_id}.{output_format}"
                
                # 转换贴纸
                success = False
                if input_extension == "webp":
                    subprocess.run(["ffmpeg", "-y", "-i", file_path, output_path], check=True)
                    success = True
                elif input_extension == "tgs":
                    from api.webhook import convert_tgs_to_gif
                    success = convert_tgs_to_gif(file_path, output_path)
                    if not success:
                        print(f"处理表情包 {sticker.file_id} TGS转换失败")
                        failed += 1
                        # 清理原始文件
                        os.remove(file_path)
                        continue
                else:
                    subprocess.run(["ffmpeg", "-y", "-i", file_path, "-vf", "scale=-1:-1", "-r", "20", output_path], check=True)
                    success = True
                
                # 清理原始文件
                os.remove(file_path)
                
                finished += 1
            except Exception as e:
                print(f"处理表情包 {sticker.file_id} 时出错: {str(e)}")
                failed += 1
            
            # 每处理5个更新一次进度
            if (finished + failed) % 5 == 0:
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=msg.message_id,
                    text=f"正在下载: {finished + failed}/{len(sticker_set.stickers)}"
                )
        
        # 创建 ZIP 文件
        zip_path = f"storage/tmp/{set_name}_{int(time.time())}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file), 
                              os.path.relpath(os.path.join(root, file), folder_path))
        
        # 更新消息
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=msg.message_id,
            text=f"已转换 {finished} 个表情，失败 {failed} 个，正在上传..."
        )
        
        # 发送 ZIP 文件
        file_size = os.path.getsize(zip_path)
        file_size_mb = file_size // (1024 * 1024)
        
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=open(zip_path, 'rb'),
            caption=f"表情包集合 {set_name} ({file_size_mb}MB)"
        )
        
        # 更新消息
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=msg.message_id,
            text=f"已成功上传表情包集合 {set_name}，共 {finished} 个表情，失败 {failed} 个"
        )
        
        # 清理文件
        shutil.rmtree(folder_path, ignore_errors=True)
        os.remove(zip_path)
        
    except Exception as e:
        error_msg = f"处理表情包集合时发生错误: {str(e)}"
        print(f"[Bot] {error_msg}")
        sys.stdout.flush()
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=msg.message_id,
            text=error_msg
        )

# 主程序
def main():
    # 创建应用程序实例
    app = Application.builder().token(TOKEN).build()

    # 添加处理程序
    app.add_handler(CommandHandler("start", start))  # /start 命令
    app.add_handler(CommandHandler("search", search_command))  # /search 命令
    
    # 修复过滤器，使用filters.Sticker.ALL或实例化一个filters.Sticker()
    app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_handler))  # 处理贴纸消息
    
    # 处理回调查询
    app.add_handler(CallbackQueryHandler(download_sticker_set, pattern="^download_set:"))  # 添加回调查询处理器
    
    # 处理普通消息
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))  # 处理所有文本消息
    
    # 启动机器人（轮询模式）
    print("机器人已启动！")
    app.run_polling()

if __name__ == "__main__":
    print("机器人已启动！")  # 启动时打印一条消息
    sys.stdout.flush()  # 强制刷新输出
    main()