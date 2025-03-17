import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from googlesearch import search

# 你的 Bot Token
TOKEN = "7707884696:AAHeEq7AgFQkVMY9X8ShxytIW_AsCRHPEmA"

# 处理 /start 命令
async def start(update: Update, context: CallbackContext) -> None:
    response = "你好，我是你的 Telegram 机器人！\n你可以：\n1. 直接发消息给我\n2. 使用 /search 关键词 来搜索"
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

# 主程序
def main():
    app = Application.builder().token(TOKEN).build()

    # 注册命令和消息处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_command))  # 添加搜索命令处理器
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))  # 处理所有文本消息

    # 启动机器人
    app.run_polling()

if __name__ == "__main__":
    print("机器人已启动！")  # 启动时打印一条消息
    sys.stdout.flush()  # 强制刷新输出
    main()