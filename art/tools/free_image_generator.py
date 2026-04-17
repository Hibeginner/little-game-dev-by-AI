"""
免费图片生成工具 - 使用 Pollinations.ai API
完全免费，无需 API Key，无需注册
GitHub: https://github.com/pollinations/pollinations

说明:
- 默认模型 (flux) 通常输出 1024x1024，若参数不兼容则可能降级为 768x768
- 建议保持 aspect ratio 参数与 width/height 匹配
"""

import urllib.parse
import requests
import os
import sys
from datetime import datetime


class PollinationsImageGenerator:
    BASE_URL = "https://image.pollinations.ai/prompt/"

    def __init__(self, save_dir=None):
        self.save_dir = save_dir or os.path.dirname(os.path.abspath(__file__))
        os.makedirs(self.save_dir, exist_ok=True)

    def generate(self, prompt, width=1024, height=1024, seed=None, model="flux", nologo=True, save_path=None):
        encoded_prompt = urllib.parse.quote(prompt)
        params = [f"width={width}", f"height={height}"]
        if seed is not None: params.append(f"seed={seed}")
        params.append(f"model={model}")
        if nologo: params.append("nologo=true")
        
        url = f"{self.BASE_URL}{encoded_prompt}?{'&'.join(params)}"
        print(f"[1/2] 正在生成图片... ({width}x{height})")
        
        try:
            response = requests.get(url, timeout=180)
            if response.status_code != 200:
                print(f"  ❌ 请求失败: {response.text[:200]}")
                return None
            
            ct = response.headers.get("Content-Type", "")
            if not ct.startswith("image/"):
                print(f"  ❌ 返回非图片: {ct}")
                return None
                
            if save_path is None:
                ext = "png" if "png" in ct else "jpg"
                save_path = os.path.join(self.save_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}")
                
            with open(save_path, "wb") as f: f.write(response.content)
            print(f"[2/2] ✅ 已保存: {save_path}")
            return save_path
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return None

if __name__ == "__main__":
    gen = PollinationsImageGenerator()
    gen.generate(
        prompt="An adorable chubby baby with rosy cheeks, smiling happily, warm lighting, high quality",
        width=512, height=512, seed=42, save_path=os.path.join(gen.save_dir, "cute_baby.png")
    )
