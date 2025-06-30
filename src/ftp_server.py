#!/usr/bin/python
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# Author: chenwuchen.ml@outlook.com                                          
# Date: 2025/06/27 17:06:54 
# 功能：输入文件路径，生成wget下载链接                                           
# usage: python3 tools/ftp_server.py               
# 
########################################################################
from flask import Flask, request, send_file, render_template_string, abort, request as flask_request
import os
import time
import socket

app = Flask(__name__)

SERVER_PORT = 8089
EXPIRE_SECONDS = 86400  # 24小时

download_registry = {}

# ✅ 获取本机真实局域网IP（避免127.0.0.1）
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # 不实际连接，只取本机出口IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ✅ HTML 模板：复制按钮复制完整wget命令
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>Wget 下载链接生成器</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f0f0f0;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
    }
    .container {
      background: #fff;
      padding: 2em;
      border-radius: 12px;
      box-shadow: 0 0 15px rgba(0,0,0,0.1);
      max-width: 700px;
      width: 100%;
    }
    h2 {
      text-align: center;
      color: #333;
      margin-bottom: 1.5em;
    }
    textarea {
      width: 100%;
      padding: 10px;
      font-size: 1em;
      border: 1px solid #ccc;
      border-radius: 8px;
      resize: none;
      box-sizing: border-box;
    }
    .buttons {
      margin-top: 1em;
      display: flex;
      justify-content: space-between;
    }
    button {
      padding: 10px 20px;
      font-size: 1em;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      transition: background-color 0.3s;
    }
    button[type="submit"] {
      background: #007bff;
      color: white;
    }
    button[type="submit"]:hover {
      background: #0056b3;
    }
    button[type="reset"] {
      background: #6c757d;
      color: white;
    }
    button[type="reset"]:hover {
      background: #5a6268;
    }
    .result-section {
      margin-top: 2em;
    }
    .result-label {
      font-weight: 600;
      color: #333;
      margin-bottom: 0.5em;
      display: block;
      font-size: 1.1em;
    }
    .output-wrapper {
      position: relative;
    }
    .output-box {
      background: #f7f7f7;
      padding: 1em;
      padding-right: 120px; /* 为按钮留出空间 */
      border-radius: 8px;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.85em; /* 减小字体 */
      word-wrap: break-word;
      border: 1px solid #e0e0e0;
      line-height: 1.6;
      min-height: 50px;
      display: flex;
      align-items: center;
    }
    .wget-command {
      color: #d73a49;
      font-weight: 600;
    }
    .download-link {
      color: #0366d6;
      word-break: break-all;
    }
    .copy-btn {
      position: absolute;
      top: 50%;
      right: 10px;
      transform: translateY(-50%);
      background: #28a745;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 5px;
      font-size: 0.85em;
      cursor: pointer;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      gap: 5px;
      white-space: nowrap;
    }
    .copy-btn:hover {
      background: #218838;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .copy-btn:active {
      transform: translateY(-50%) scale(0.98);
      box-shadow: none;
    }
    .tooltip {
      position: absolute;
      bottom: 100%;
      right: 0;
      margin-bottom: 8px;
      background: #28a745;
      color: white;
      padding: 6px 12px;
      font-size: 0.8em;
      border-radius: 4px;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
      white-space: nowrap;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .tooltip::after {
      content: '';
      position: absolute;
      top: 100%;
      right: 20px;
      border: 5px solid transparent;
      border-top-color: #28a745;
    }
    .tooltip.show {
      opacity: 1;
      visibility: visible;
      transform: translateY(-3px);
    }
    label {
      display: block;
      margin-bottom: 0.5em;
      color: #555;
      font-weight: 500;
    }
    .error-message {
      margin-top: 1em;
      padding: 10px;
      background: #f8d7da;
      color: #721c24;
      border: 1px solid #f5c6cb;
      border-radius: 5px;
      text-align: center;
    }
    .success-icon {
      color: #28a745;
      margin-right: 5px;
    }
    
    /* 响应式设计 */
    @media (max-width: 600px) {
      .container {
        padding: 1.5em;
      }
      .output-box {
        font-size: 0.75em;
        padding-right: 10px;
        padding-bottom: 50px; /* 移动端按钮放到下方 */
      }
      .copy-btn {
        top: auto;
        bottom: 10px;
        right: 10px;
        transform: none;
      }
      .tooltip {
        bottom: auto;
        top: -35px;
      }
      .tooltip::after {
        top: auto;
        bottom: -10px;
        border-top-color: transparent;
        border-bottom-color: #28a745;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>🔗 Wget 下载链接生成器</h2>
    <form method="post" action="/generate">
      <label for="filepath">请输入服务器上的文件路径：</label>
      <textarea name="filepath" id="filepath" rows="3" placeholder="例如: /home/user/file.txt" required>{{ filepath if filepath else '' }}</textarea>
      <div class="buttons">
        <button type="submit">生成链接</button>
        <button type="reset">重置</button>
      </div>
    </form>

    {% if download_url %}
      <div class="result-section">
        <label class="result-label"><span class="success-icon">✓</span>wget命令：</label>
        <div class="output-wrapper">
          <div class="output-box">
            <span id="wgetCommand"><span class="wget-command">wget</span> <span class="download-link">{{ download_url }}</span></span>
          </div>
          <button class="copy-btn" onclick="copyToClipboard()">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
              <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
            </svg>
            复制命令
            <div class="tooltip" id="tooltip">已复制到剪贴板!</div>
          </button>
        </div>
      </div>
    {% endif %}

    {% if error %}
      <div class="error-message">
        ⚠️ {{ error }}
      </div>
    {% endif %}
  </div>

  <script>
    function copyToClipboard() {
      // 获取完整的wget命令
      const wgetCommand = document.getElementById("wgetCommand").textContent.trim();
      
      // 创建临时文本区域用于复制
      const tempTextArea = document.createElement("textarea");
      tempTextArea.value = wgetCommand;
      tempTextArea.style.position = "absolute";
      tempTextArea.style.left = "-9999px";
      document.body.appendChild(tempTextArea);
      
      // 选择并复制文本
      tempTextArea.select();
      tempTextArea.setSelectionRange(0, 99999); // 兼容移动设备
      
      try {
        const successful = document.execCommand('copy');
        if (successful) {
          showTooltip();
        } else {
          fallbackCopy(wgetCommand);
        }
      } catch (err) {
        fallbackCopy(wgetCommand);
      }
      
      // 移除临时元素
      document.body.removeChild(tempTextArea);
    }
    
    function fallbackCopy(text) {
      // 使用 Clipboard API 作为降级方案
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          showTooltip();
        }).catch(err => {
          prompt("复制失败，请手动复制以下命令：", text);
        });
      } else {
        prompt("复制失败，请手动复制以下命令：", text);
      }
    }
    
    function showTooltip() {
      const tooltip = document.getElementById("tooltip");
      const button = document.querySelector('.copy-btn');
      
      // 添加动画效果
      tooltip.classList.add("show");
      button.style.background = "#1e7e34";
      
      setTimeout(() => {
        tooltip.classList.remove("show");
        button.style.background = "#28a745";
      }, 2000);
    }
    
    // 双击命令框也可以复制
    document.addEventListener('DOMContentLoaded', function() {
      const outputBox = document.querySelector('.output-box');
      if (outputBox) {
        outputBox.addEventListener('dblclick', function(e) {
          copyToClipboard();
        });
        
        // 添加提示
        outputBox.title = "双击复制命令";
      }
    });
    
    // 记住上次输入的路径
    window.addEventListener('load', function() {
      const savedPath = localStorage.getItem('lastFilePath');
      if (savedPath && !document.getElementById('filepath').value) {
        document.getElementById('filepath').value = savedPath;
      }
    });
    
    // 保存输入的路径
    document.querySelector('form').addEventListener('submit', function() {
      const filepath = document.getElementById('filepath').value;
      localStorage.setItem('lastFilePath', filepath);
    });
  </script>
</body>
</html>
"""

# ✅ 首页
@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

# ✅ 生成下载链接
@app.route('/generate', methods=['POST'])
def generate_link():
    filepath = request.form.get('filepath', '').strip()
    
    # 验证文件是否存在
    if not filepath:
        return render_template_string(HTML_TEMPLATE, error="请输入文件路径", filepath=filepath)
    
    if not os.path.isfile(filepath):
        return render_template_string(HTML_TEMPLATE, error=f"文件不存在: {filepath}", filepath=filepath)

    filename = os.path.basename(filepath)
    now = time.time()
    
    # 清理过期的链接
    expired = [k for k, v in download_registry.items() if now - v[1] > EXPIRE_SECONDS]
    for k in expired:
        del download_registry[k]
    
    # 注册新的下载链接
    download_registry[filename] = (filepath, now)

    # 获取服务器IP和端口
    server_ip = flask_request.host.split(':')[0] if flask_request.host else get_local_ip()
    download_url = f"http://{server_ip}:{SERVER_PORT}/download/{filename}"

    return render_template_string(HTML_TEMPLATE, download_url=download_url, filepath=filepath)

# ✅ 文件下载接口
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    now = time.time()
    
    # 清理过期的链接
    expired = [k for k, v in download_registry.items() if now - v[1] > EXPIRE_SECONDS]
    for k in expired:
        del download_registry[k]

    # 检查文件是否在注册表中
    entry = download_registry.get(filename)
    if not entry:
        abort(404, description="链接已过期或不存在")
    
    filepath = entry[0]
    if not os.path.isfile(filepath):
        abort(404, description="文件不存在")
    
    # 发送文件
    return send_file(filepath, as_attachment=True, download_name=filename)

# ✅ 启动
if __name__ == '__main__':
    print(f"服务器启动在: http://{get_local_ip()}:{SERVER_PORT}")
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)