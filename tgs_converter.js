const fs = require('fs');
const zlib = require('zlib');
const puppeteer = require('puppeteer-core');
const path = require('path');

async function findChrome() {
    const paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', // macOS
        '/usr/bin/google-chrome',                                      // Linux
        '/usr/bin/chromium-browser',                                  // Linux
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', // Windows
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ];
    
    for (const path of paths) {
        if (fs.existsSync(path)) {
            return path;
        }
    }
    throw new Error('找不到Chrome浏览器，请先安装Chrome');
}

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function convertTgsToGif(inputPath, outputPath) {
    let browser = null;
    let tempHtmlPath = null;
    
    try {
        // 读取并解压TGS文件
        const compressedData = fs.readFileSync(inputPath);
        const jsonData = zlib.gunzipSync(compressedData).toString();
        
        // 创建一个临时HTML文件来渲染动画
        tempHtmlPath = path.join(__dirname, 'temp.html');
        const html = `
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        background: transparent;
                    }
                    #animation {
                        width: 512px;
                        height: 512px;
                        background: transparent;
                    }
                </style>
            </head>
            <body>
                <div id="animation"></div>
                <script>
                    const animationData = ${jsonData};
                    const anim = lottie.loadAnimation({
                        container: document.getElementById('animation'),
                        renderer: 'svg',
                        loop: true,
                        autoplay: true,
                        animationData: animationData
                    });
                    
                    // 让动画知道它已经加载完成
                    anim.addEventListener('DOMLoaded', function() {
                        document.body.setAttribute('data-loaded', 'true');
                    });
                </script>
            </body>
            </html>
        `;
        fs.writeFileSync(tempHtmlPath, html);

        // 查找Chrome路径
        const chromePath = await findChrome();
        console.log('使用Chrome路径:', chromePath);

        // 启动浏览器
        browser = await puppeteer.launch({
            executablePath: chromePath,
            headless: "new",
            args: ['--no-sandbox']
        });

        const page = await browser.newPage();
        await page.setViewport({ width: 512, height: 512 });
        await page.goto(`file://${tempHtmlPath}`);
        
        // 等待动画加载
        await page.waitForFunction(() => {
            return document.body.getAttribute('data-loaded') === 'true';
        }, { timeout: 5000 });

        // 给额外时间让动画开始播放
        await delay(500);

        // 捕获多个帧
        const frames = [];
        const totalFrames = 90; // 保持高帧数以获得流畅动画
        for (let i = 0; i < totalFrames; i++) {
            const frame = await page.screenshot({ 
                type: 'png',
                omitBackground: true
            });
            frames.push(frame);
            await delay(33); // 约30fps的捕获速度
        }

        // 使用ffmpeg将帧转换为GIF
        const { spawn } = require('child_process');
        const ffmpeg = spawn('ffmpeg', [
            '-f', 'image2pipe',
            '-framerate', '15', // 调整为较快的播放速度
            '-i', '-',
            '-vf', 'scale=512:512:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse=dither=sierra2_4a', // 改善GIF质量
            '-loop', '0', // 无限循环
            '-f', 'gif', // 明确指定输出格式为GIF
            '-y',
            outputPath
        ]);

        for (const frame of frames) {
            ffmpeg.stdin.write(frame);
        }
        ffmpeg.stdin.end();

        await new Promise((resolve, reject) => {
            ffmpeg.on('close', (code) => {
                if (code === 0) resolve();
                else reject(new Error(`FFmpeg进程退出，代码：${code}`));
            });
        });
        
        console.log('转换成功');
        process.exit(0);
    } catch (error) {
        console.error('转换失败:', error);
        process.exit(1);
    } finally {
        // 清理资源
        if (browser) {
            await browser.close();
        }
        if (tempHtmlPath && fs.existsSync(tempHtmlPath)) {
            fs.unlinkSync(tempHtmlPath);
        }
    }
}

if (process.argv.length !== 4) {
    console.log('使用方法: node tgs_converter.js <输入TGS文件> <输出GIF文件>');
    process.exit(1);
}

convertTgsToGif(process.argv[2], process.argv[3]); 