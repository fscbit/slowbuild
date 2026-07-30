"""
文件加密打包工具
用法：把要加密的文件路径和密码填到下面，运行即可生成自解密 HTML

要求：Python 3，不需要安装任何库
"""

import base64
import os

# ====== 在这里修改 ======
TARGET_FILE = r"C:\Users\你的用户名\Desktop\要加密的文件.js"  # 要加密的文件路径
PASSWORD = "Fsc123456%"     # 密码
OUTPUT_FILE = None           # 输出路径，None = 同目录下 .html
TITLE = "加密文件查看器"      # 网页标题
# =======================


def encrypt_file(filepath, password, output=None, title="加密文件查看器"):
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
    
    key = bytes([(ord(password[i % len(password)]) + i * 7) & 0xFF for i in range(32)])
    encrypted = bytes([raw_bytes[i] ^ key[i % 32] for i in range(len(raw_bytes))])
    cipher = base64.b64encode(encrypted).decode('ascii')
    
    # 验证
    test_raw = base64.b64decode(cipher)
    test_dec = bytes([test_raw[i] ^ key[i % 32] for i in range(len(test_raw))])
    assert test_dec == raw_bytes, '加密验证失败！'
    
    if output is None:
        output = os.path.splitext(filepath)[0] + '_加密.html'
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>
body{{font-family:Microsoft YaHei,sans-serif;background:#1a1a2e;color:#eee;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}}
.box{{background:#16213e;padding:30px;border-radius:12px;width:500px;text-align:center;box-shadow:0 0 30px rgba(0,0,0,0.5)}}
input{{padding:10px 16px;border:2px solid #0f3460;border-radius:8px;background:#1a1a2e;color:#fff;font-size:16px;width:220px;outline:none}}
input:focus{{border-color:#e94560}}
button{{padding:10px 24px;background:#e94560;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin-left:10px}}
button:hover{{background:#c23152}}
textarea{{width:100%;height:400px;background:#0f3460;color:#0f0;border:none;border-radius:8px;padding:12px;font-family:Consolas,monospace;font-size:13px;resize:vertical;margin-top:15px;box-sizing:border-box}}
.hint{{font-size:13px;color:#888;margin-top:8px}}
</style></head><body>
<div class="box">
<h2>🔒 {title}</h2>
<p>输入密码查看内容</p>
<input type="password" id="pw" placeholder="请输入密码" onkeydown="if(event.key==='Enter')decrypt()">
<button onclick="decrypt()">解锁</button>
<div class="hint">解锁后自动复制到剪贴板</div>
<textarea id="out" readonly style="display:none" onclick="this.select()"></textarea>
</div>
<script>
var CIPHER="{cipher}";
function decrypt(){{
  var pw=document.getElementById("pw").value;
  var key=new Uint8Array(32);
  for(var i=0;i<32;i++)key[i]=(pw.charCodeAt(i%pw.length)+i*7)&255;
  try{{
    var raw=Uint8Array.from(atob(CIPHER),function(c){{return c.charCodeAt(0)}});
    var dec=new Uint8Array(raw.length);
    for(var i=0;i<raw.length;i++)dec[i]=raw[i]^key[i%32];
    var result=new TextDecoder('utf-8').decode(dec);
    var out=document.getElementById("out");
    out.value=result;out.style.display="block";
    out.select();
    try{{document.execCommand("copy")}}catch(e){{}}
    document.querySelector("h2").textContent="✅ 已解锁 · 内容已复制到剪贴板";
  }}catch(e){{
    document.querySelector("h2").textContent="❌ 密码错误，请重试";
  }}
}}
</script></body></html>'''
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output, len(raw_bytes), len(encrypted)


if __name__ == '__main__':
    out, raw_size, enc_size = encrypt_file(TARGET_FILE, PASSWORD, OUTPUT_FILE, TITLE)
    print(f'✅ 加密完成！')
    print(f'   输入: {TARGET_FILE} ({raw_size} 字节)')
    print(f'   输出: {out}')
    print(f'   密码: {PASSWORD}')
