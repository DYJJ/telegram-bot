#!/usr/bin/env python3
import sys
import gzip
import json
import os
from PIL import Image
import imageio
import tempfile
from lottie import objects
from lottie.parsers import tgs
from lottie.exporters import gif

def convert_tgs_to_gif(input_path, output_path):
    """将TGS文件转换为GIF"""
    try:
        # 解压TGS文件
        with gzip.open(input_path, 'rb') as f:
            tgs_data = f.read()
        
        # 解析TGS数据
        animation = tgs.parse_tgs(tgs_data)
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 导出为GIF
            gif.export_gif(animation, output_path, 30)
            
        print(f"转换成功: {output_path}")
        return True
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法: python3 tgs_converter.py <输入TGS文件> <输出GIF文件>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"错误: 输入文件 {input_path} 不存在")
        sys.exit(1)
    
    success = convert_tgs_to_gif(input_path, output_path)
    sys.exit(0 if success else 1)
