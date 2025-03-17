# Telegram搜索机器人

这是一个基于Python的Telegram机器人，可以响应用户消息并提供搜索功能。

## 功能特点

- 回复用户的文本消息
- 通过 `/search` 命令搜索网络信息
- 简单易用的界面

## 部署方式

本机器人已部署在Vercel上，可直接通过Telegram使用，无需本地运行。

### 在Telegram中使用

1. 在Telegram中搜索 `@你的机器人用户名`
2. 点击"开始"或发送 `/start` 命令
3. 直接发送消息或使用 `/search 关键词` 进行搜索

## 本地开发

如果你想在本地开发和测试：

1. 克隆此仓库
2. 安装依赖: `pip install -r requirements.txt`
3. 运行机器人: `python bot.py`

## 环境变量

项目需要的环境变量：

- `TELEGRAM_TOKEN`: 你的Telegram机器人Token

## 技术栈

- Python
- python-telegram-bot
- Google搜索API 