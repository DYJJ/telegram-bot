#!/bin/bash

# 创建必要的目录
mkdir -p storage/tmp

# 检查操作系统类型
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    # 安装 Homebrew（如果没有）
    which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # 安装必要的工具
    brew install ffmpeg
    brew install imagemagick
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y ffmpeg imagemagick
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        sudo yum install -y epel-release
        sudo yum install -y ffmpeg ImageMagick
    fi
fi

# 检查安装是否成功
echo "检查依赖安装情况..."
if ! command -v ffmpeg &> /dev/null; then
    echo "错误：ffmpeg 未安装成功"
    exit 1
fi

if ! command -v convert &> /dev/null; then
    echo "错误：ImageMagick 未安装成功"
    exit 1
fi

echo "所有依赖安装完成！" 