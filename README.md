# Telegram搜索与表情转换机器人

这是一个基于Python的Telegram机器人，可以响应用户消息，提供搜索功能，并支持各种表情包的格式转换。

## 功能特点

* 回复用户的文本消息
* 通过 `/search` 命令搜索网络信息
* 通过 `/group` 和 `/jump` 命令查找和推荐群组
* 通过 `/sticker` 命令搜索表情包
* 自动下载和转换Telegram表情包(TGS格式)为GIF格式
* 支持将MP4视频文件转换为GIF格式
* 所有转换后的文件保存到专门的目录中，方便用户下载和管理

## 部署方式

本机器人已部署在Vercel上，可直接通过Telegram使用，无需本地运行。

### 在Telegram中使用

1. 在Telegram中搜索 `@你的机器人用户名`
2. 点击"开始"或发送 `/start` 命令
3. 直接发送消息或使用各种命令使用机器人功能
4. 发送表情包或MP4文件给机器人，它会自动转换并回复文件

## 本地开发

如果你想在本地开发和测试：

1. 克隆此仓库
2. 安装依赖: 
   ```
   pip install -r requirements.txt
   npm install
   ```
3. 运行机器人: `python bot.py`

## 环境变量

项目需要的环境变量：

* `TELEGRAM_TOKEN`: 你的Telegram机器人Token

## 技术栈

* Python
* Node.js
* FFmpeg (用于视频转换)
* puppeteer-core (用于TGS转换)

## 文件转换功能

* **TGS转换**：使用Node.js和puppeteer渲染Lottie动画，并使用FFmpeg将其转换为GIF
* **MP4转换**：使用FFmpeg将MP4视频文件转换为优化的GIF动画
* **存储管理**：转换后的文件分别存储在`storage/gif_files`和`storage/mp4_files`目录中 