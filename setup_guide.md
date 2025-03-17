# 部署指南：将Telegram机器人部署到GitHub和Vercel

## 第一步：上传到GitHub

1. 在GitHub上创建新仓库
   - 访问 https://github.com/new
   - 输入仓库名称，例如 `telegram-search-bot`
   - 选择公开或私有（根据需要）
   - 不要初始化README，.gitignore或license
   - 点击"创建仓库"

2. 将本地代码推送到GitHub
   ```bash
   # 添加所有文件到Git
   git add .
   
   # 提交更改
   git commit -m "初始化提交"
   
   # 添加远程仓库（替换为你的GitHub用户名和仓库名）
   git remote add origin https://github.com/你的用户名/telegram-search-bot.git
   
   # 推送代码到GitHub
   git push -u origin master
   ```

## 第二步：部署到Vercel

1. 注册/登录Vercel
   - 访问 https://vercel.com/
   - 使用GitHub账号登录，或创建新账号

2. 导入GitHub项目
   - 点击"Import Project"或"New Project"
   - 选择"Import Git Repository"
   - 授权Vercel访问你的GitHub账号（如果尚未完成）
   - 从列表中选择你的Telegram机器人仓库

3. 配置项目
   - 项目名称：保持默认或自定义
   - 构建设置：保持默认设置
   - 环境变量：添加 `TELEGRAM_TOKEN` 设置为你的Bot Token

4. 点击"Deploy"开始部署

5. 设置Telegram Webhook
   - 部署完成后，获取Vercel提供的URL（例如 `https://你的项目.vercel.app`）
   - 访问 `https://你的项目.vercel.app/api/webhook` 来设置Webhook

## 第三步：测试机器人

1. 在Telegram中找到你的机器人并发送消息测试
2. 如果机器人响应，恭喜你！部署成功

## 故障排除

1. 如果机器人没有响应:
   - 检查Vercel日志查找错误
   - 确认环境变量设置正确
   - 确认Webhook设置成功

2. Vercel部署问题:
   - 查看构建日志了解错误详情
   - 确保所有依赖都在requirements.txt中列出 