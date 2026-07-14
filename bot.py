#!/data/data/com.termux/files/usr/bin/python
import os
import base64
import zlib
import requests
import pyfiglet
import json
import time
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
import zipfile  # ADDED FOR ZIP
import shutil   # ADDED FOR ZIP

# ============================================================
# CONSOLE INITIALIZE
# ============================================================
console = Console()

# ============================================================
# TELEGRAM BOT CONFIGURATION
# ============================================================
TELEGRAM_BOT_TOKEN = "8691293365:AAHI0BQPox3DEq1styTI1s48VQgTgQjggVE"
TELEGRAM_CHAT_ID = "8416089909"

OUTPUT_PREFIX = "protected_"
DECODE_PREFIX = "decoded_"

# ============================================================
# PROTECTION FUNCTIONS
# ============================================================

def protect_html_fast(html_code):
    compressed = zlib.compress(html_code.encode("utf-8"), level=6)
    encoded = base64.b64encode(compressed).decode()
    
    protected = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Protected by Dgtl Protect</title>
</head>
<body>
<script>
(function(){{
const data = "{encoded}";
async function decode(){{
    const binary = atob(data);
    const bytes = new Uint8Array(binary.length);
    for(let i = 0; i < binary.length; i++) {{
        bytes[i] = binary.charCodeAt(i);
    }}
    const stream = new DecompressionStream("deflate");
    const writer = stream.writable.getWriter();
    writer.write(bytes);
    writer.close();
    const buffer = await new Response(stream.readable).arrayBuffer();
    return new TextDecoder().decode(buffer);
}}
decode().then(html => {{
    document.open();
    document.write(html);
    document.close();
}});
}})();
</script>
</body>
</html>
"""
    return protected

# ============================================================
# FIXED PYTHON PROTECT FUNCTION
# ============================================================

def protect_python_fast(python_code):
    """Python code ko protect karega - FULLY WORKING"""
    try:
        if isinstance(python_code, bytes):
            python_code = python_code.decode('utf-8')
        
        compressed = zlib.compress(python_code.encode("utf-8"), level=6)
        encoded = base64.b64encode(compressed).decode()
        
        protected = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import zlib
import sys
import os

def decode_and_execute():
    try:
        encoded = "{encoded}"
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded)
        code = decompressed.decode("utf-8")
        exec(code, globals())
    except Exception as e:
        print(f"[!] Error: {{e}}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    decode_and_execute()
'''
        return protected
    except Exception as e:
        encoded = base64.b64encode(python_code.encode('utf-8')).decode()
        protected = f'''#!/usr/bin/env python3
import base64
import sys
try:
    exec(base64.b64decode("{encoded}").decode())
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
'''
        return protected

# ============================================================
# DECODE FUNCTIONS
# ============================================================

def decode_html_protected(html_code):
    try:
        match = re.search(r'const data = "([^"]+)"', html_code)
        if not match:
            return None, "No encoded data found"
        
        encoded = match.group(1)
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded)
        return decompressed.decode("utf-8"), "HTML Decoded"
    except Exception as e:
        return None, str(e)

def decode_python_protected(python_code):
    try:
        match = re.search(r'encoded = "([^"]+)"', python_code)
        if not match:
            return None, "No encoded data found"
        
        encoded = match.group(1)
        decoded = base64.b64decode(encoded)
        decompressed = zlib.decompress(decoded)
        return decompressed.decode("utf-8"), "Python Decoded"
    except Exception as e:
        return None, str(e)

def decode_file_instant(filepath):
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return None, "File not found"
        
        content = filepath.read_text(encoding='utf-8')
        
        if filepath.suffix.lower() == '.html' or filepath.suffix.lower() == '.htm':
            decoded, msg = decode_html_protected(content)
            if decoded:
                out = DECODE_PREFIX + filepath.name
                Path(out).write_text(decoded, encoding='utf-8')
                return str(Path(out).absolute()), "HTML Decoded"
            return None, msg
            
        elif filepath.suffix.lower() == '.py':
            decoded, msg = decode_python_protected(content)
            if decoded:
                out = DECODE_PREFIX + filepath.name
                Path(out).write_text(decoded, encoding='utf-8')
                if os.name != 'nt':
                    os.chmod(out, 0o755)
                return str(Path(out).absolute()), "Python Decoded"
            return None, msg
        else:
            return None, "Only .html, .htm or .py files"
    except Exception as e:
        return None, str(e)

# ============================================================
# EXTRACT WEBSITE - FIXED WITH ZIP 📦
# ============================================================

def extract_website_full(url):
    """Full website extractor - Returns ZIP file with all content"""
    try:
        # Clean URL
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        console.print(f"[cyan]🌐 Extracting: {url}[/cyan]")
        
        # Headers - Real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # GET request with timeout
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Get domain
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").replace("/", "_")
        if not domain:
            domain = "website"
        
        # Create folder
        folder_name = f"{domain}_extracted"
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        os.makedirs(folder_name, exist_ok=True)
        
        # Save main HTML
        html_content = response.text
        html_file = os.path.join(folder_name, "index.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Extract and save CSS
        css_links = re.findall(r'href=[\'"]?([^\'" >]+\.css[^\'" >]*)', html_content)
        css_count = 0
        for css_url in css_links:
            try:
                full_css_url = urljoin(url, css_url)
                css_response = session.get(full_css_url, headers=headers, timeout=10)
                if css_response.status_code == 200:
                    css_filename = f"style_{css_count}.css"
                    css_path = os.path.join(folder_name, css_filename)
                    with open(css_path, 'w', encoding='utf-8') as f:
                        f.write(css_response.text)
                    css_count += 1
            except:
                pass
        
        # Extract and save JS
        js_links = re.findall(r'src=[\'"]?([^\'" >]+\.js[^\'" >]*)', html_content)
        js_count = 0
        for js_url in js_links:
            try:
                full_js_url = urljoin(url, js_url)
                js_response = session.get(full_js_url, headers=headers, timeout=10)
                if js_response.status_code == 200:
                    js_filename = f"script_{js_count}.js"
                    js_path = os.path.join(folder_name, js_filename)
                    with open(js_path, 'w', encoding='utf-8') as f:
                        f.write(js_response.text)
                    js_count += 1
            except:
                pass
        
        # Save as single file with all content
        all_content = f"""<!-- Extracted from: {url} -->
<!-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- CSS Files: {css_count} | JS Files: {js_count} -->

{html_content}
"""
        full_file = f"{domain}_full.html"
        with open(full_file, 'w', encoding='utf-8') as f:
            f.write(all_content)
        
        # ============================================================
        # CREATE ZIP FILE - NEW ✅
        # ============================================================
        zip_filename = f"{domain}_website.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from folder
            for root, dirs, files in os.walk(folder_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=os.path.dirname(folder_name))
                    zipf.write(file_path, arcname)
            
            # Add full HTML file
            zipf.write(full_file, os.path.basename(full_file))
        
        # Get size
        total_size = os.path.getsize(zip_filename)
        
        # Summary
        summary = f"""✅ Extraction Complete!
📁 Website: {domain}
📄 HTML: {format_size(os.path.getsize(html_file))}
🎨 CSS: {css_count} files
📜 JS: {js_count} files
📦 ZIP: {zip_filename} ({format_size(total_size)})
📂 All files inside ZIP"""
        
        console.print(f"[green]{summary}[/green]")
        
        # Cleanup folder and single files
        try:
            shutil.rmtree(folder_name)
            if os.path.exists(full_file):
                os.remove(full_file)
        except:
            pass
        
        return zip_filename, total_size, summary
        
    except requests.exceptions.Timeout:
        return None, 0, "⏰ Timeout - Website too slow"
    except requests.exceptions.ConnectionError:
        return None, 0, "🔌 Connection Error - Website not reachable"
    except requests.exceptions.HTTPError as e:
        return None, 0, f"❌ HTTP Error: {e}"
    except Exception as e:
        return None, 0, f"❌ Error: {str(e)}"

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

# ============================================================
# TELEGRAM BOT
# ============================================================
class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        self.user_sessions = {}
        self.running = True
        self.temp_dir = os.path.join(os.getcwd(), "temp_files")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.test_connection()
    
    def test_connection(self):
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    console.print(f"[green]✅ Bot connected: @{data['result']['username']}[/green]")
                    return True
            console.print("[red]❌ Invalid bot token![/red]")
            return False
        except:
            console.print("[red]❌ Connection error![/red]")
            return False
    
    def send_message(self, text, chat_id=None, reply_markup=None):
        if chat_id is None:
            chat_id = self.chat_id
        
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, data=data, timeout=5)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def send_file_fast(self, file_path, chat_id=None, caption=""):
        if chat_id is None:
            chat_id = self.chat_id
        
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            return None
        
        url = f"{self.base_url}/sendDocument"
        try:
            with open(file_path, 'rb') as f:
                files = {'document': (os.path.basename(file_path), f, 'application/octet-stream')}
                data = {'chat_id': chat_id, 'caption': caption}
                response = requests.post(url, data=data, files=files, timeout=20)
                return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def download_file_fast(self, file_id):
        try:
            url = f"{self.base_url}/getFile"
            params = {"file_id": file_id}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if not data.get('ok'):
                return None
            
            file_path = data['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            
            response = requests.get(file_url, timeout=20, stream=True)
            if response.status_code != 200:
                return None
            
            filename = file_path.split('/')[-1]
            if not filename:
                filename = f"file_{int(time.time())}.bin"
            
            full_path = os.path.join(self.temp_dir, filename)
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            return full_path
        except:
            return None
    
    def send_startup_message(self):
        try:
            text = f"""🚀 <b>Dgtl Protect Bot</b>
✅ Status: Online

<b>📌 Features:</b>
🛡️ Protect HTML - Encode
🛡️ Protect Python - Encode
🔓 Decode HTML - Decode
🔓 Decode Python - Decode
🌐 Extract Website - Get HTML

Send /start"""
            self.send_message(text)
        except:
            pass
    
    def get_updates(self):
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 15
        }
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get("result", [])
            return []
        except:
            return []
    
    # ============================================================
    # MAIN KEYBOARD
    # ============================================================
    
    def main_keyboard(self):
        return {
            "keyboard": [
                ["🛡️ Protect HTML", "🔓 Decode HTML"],
                ["🛡️ Protect Python", "🔓 Decode Python"],
                ["🌐 Extract Website"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    # ============================================================
    # START
    # ============================================================
    
    def handle_start(self, chat_id):
        text = """🤖 <b>Dgtl Protect Bot</b>

<b>📌 Features:</b>

🛡️ <b>Protect HTML</b> - Encode HTML file
🛡️ <b>Protect Python</b> - Encode Python file
🔓 <b>Decode HTML</b> - Decode protected HTML
🔓 <b>Decode Python</b> - Decode protected Python
🌐 <b>Extract Website</b> - Get HTML from URL

<b>⚡ Fast & Easy!</b>

<b>👨‍💻 Developer:</b> Aryan Afridi

Click any button below!"""
        self.send_message(text, chat_id, self.main_keyboard())
    
    # ============================================================
    # PROTECT HTML
    # ============================================================
    
    def handle_protect_html(self, chat_id):
        self.send_message("🛡️ <b>Send HTML file to protect</b>", chat_id)
        self.user_sessions[chat_id] = {"action": "protect_html"}
    
    def process_protect_html(self, chat_id, file_id, file_name):
        if not (file_name.lower().endswith('.html') or file_name.lower().endswith('.htm')):
            self.send_message("❌ Send .html or .htm file!", chat_id)
            return
        
        input_file = self.download_file_fast(file_id)
        if not input_file:
            self.send_message("❌ Download failed!", chat_id)
            return
        
        result, ftype = protect_file_instant(input_file)
        if not result:
            self.send_message(f"❌ Protection failed!", chat_id)
            return
        
        self.send_message("✅ Protected!", chat_id)
        self.send_file_fast(result, chat_id, f"🛡️ {os.path.basename(result)}")
        
        try:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(result): os.remove(result)
        except: pass
        
        self.user_sessions[chat_id] = {}
    
    # ============================================================
    # PROTECT PYTHON
    # ============================================================
    
    def handle_protect_python(self, chat_id):
        self.send_message("🛡️ <b>Send Python file to protect</b>", chat_id)
        self.user_sessions[chat_id] = {"action": "protect_python"}
    
    def process_protect_python(self, chat_id, file_id, file_name):
        if not file_name.lower().endswith('.py'):
            self.send_message("❌ Send .py file!", chat_id)
            return
        
        input_file = self.download_file_fast(file_id)
        if not input_file:
            self.send_message("❌ Download failed!", chat_id)
            return
        
        result, ftype = protect_file_instant(input_file)
        if not result:
            self.send_message(f"❌ Protection failed: {ftype}", chat_id)
            return
        
        self.send_message("✅ Protected!", chat_id)
        self.send_file_fast(result, chat_id, f"🛡️ {os.path.basename(result)}")
        
        try:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(result): os.remove(result)
        except: pass
        
        self.user_sessions[chat_id] = {}
    
    # ============================================================
    # DECODE HTML
    # ============================================================
    
    def handle_decode_html(self, chat_id):
        self.send_message("🔓 <b>Send protected HTML file to decode</b>", chat_id)
        self.user_sessions[chat_id] = {"action": "decode_html"}
    
    def process_decode_html(self, chat_id, file_id, file_name):
        if not (file_name.lower().endswith('.html') or file_name.lower().endswith('.htm')):
            self.send_message("❌ Send .html or .htm file!", chat_id)
            return
        
        input_file = self.download_file_fast(file_id)
        if not input_file:
            self.send_message("❌ Download failed!", chat_id)
            return
        
        result, msg = decode_file_instant(input_file)
        if not result:
            self.send_message(f"❌ Decode failed: {msg}", chat_id)
            return
        
        self.send_message("✅ Decoded!", chat_id)
        self.send_file_fast(result, chat_id, f"🔓 {os.path.basename(result)}")
        
        try:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(result): os.remove(result)
        except: pass
        
        self.user_sessions[chat_id] = {}
    
    # ============================================================
    # DECODE PYTHON
    # ============================================================
    
    def handle_decode_python(self, chat_id):
        self.send_message("🔓 <b>Send protected Python file to decode</b>", chat_id)
        self.user_sessions[chat_id] = {"action": "decode_python"}
    
    def process_decode_python(self, chat_id, file_id, file_name):
        if not file_name.lower().endswith('.py'):
            self.send_message("❌ Send .py file!", chat_id)
            return
        
        input_file = self.download_file_fast(file_id)
        if not input_file:
            self.send_message("❌ Download failed!", chat_id)
            return
        
        result, msg = decode_file_instant(input_file)
        if not result:
            self.send_message(f"❌ Decode failed: {msg}", chat_id)
            return
        
        self.send_message("✅ Decoded!", chat_id)
        self.send_file_fast(result, chat_id, f"🔓 {os.path.basename(result)}")
        
        try:
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(result): os.remove(result)
        except: pass
        
        self.user_sessions[chat_id] = {}
    
    # ============================================================
    # EXTRACT WEBSITE - FIXED ✅
    # ============================================================
    
    def handle_extract(self, chat_id):
        self.send_message("🌐 <b>Send website URL</b>\nExample: example.com\n\n✅ Any website works!", chat_id)
        self.user_sessions[chat_id] = {"action": "extract"}
    
    def process_extract(self, chat_id, url):
        if not url or url.strip() == "":
            self.send_message("❌ Send a valid URL!", chat_id)
            return
        
        self.send_message("⏳ Extracting website...\nThis may take a few seconds...", chat_id)
        
        filename, size, summary = extract_website_full(url.strip())
        
        if filename:
            self.send_message(f"✅ {summary}", chat_id)
            self.send_file_fast(filename, chat_id, f"📦 {filename}")
            try:
                if os.path.exists(filename): os.remove(filename)
            except: pass
        else:
            self.send_message(f"❌ {summary}", chat_id)
        
        self.user_sessions[chat_id] = {}
    
    # ============================================================
    # RUN
    # ============================================================
    
    def run(self):
        console.clear()
        try:
            banner = pyfiglet.figlet_format("Dgtl Protect", font="small")
        except:
            banner = "=== Dgtl Protect ==="
        
        colored = Text(banner, style="bold cyan")
        console.print(Panel(colored, box=box.DOUBLE, border_style="cyan",
                          title="[bold green] v2.0 [/bold green]",
                          subtitle="[bold yellow] Developer: MixyOx-6 [/bold yellow]"))
        console.print()
        
        console.print("[yellow]🔌 Connecting...[/yellow]")
        if not self.test_connection():
            return
        
        console.print("[green]✅ Connected![/green]")
        console.print("[green]✅ Bot Running - FAST![/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        console.print()
        console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
        console.print("[white]🤖 Bot ready![/white]")
        console.print("[yellow]⚡ 4 Features: Protect, Decode, Extract[/yellow]")
        console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
        console.print()
        
        while self.running:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        
                        if "document" in message:
                            document = message["document"]
                            file_id = document["file_id"]
                            file_name = document.get("file_name", "unknown")
                            
                            console.print(f"[cyan]📁 Received: {file_name}[/cyan]")
                            
                            session = self.user_sessions.get(chat_id, {})
                            action = session.get("action")
                            
                            if action == "protect_html":
                                self.process_protect_html(chat_id, file_id, file_name)
                            elif action == "protect_python":
                                self.process_protect_python(chat_id, file_id, file_name)
                            elif action == "decode_html":
                                self.process_decode_html(chat_id, file_id, file_name)
                            elif action == "decode_python":
                                self.process_decode_python(chat_id, file_id, file_name)
                            else:
                                self.send_message("❌ Click a button first!\nSend /start", chat_id)
                            continue
                        
                        if not text:
                            continue
                        
                        session = self.user_sessions.get(chat_id, {})
                        if session.get("action") == "extract":
                            self.process_extract(chat_id, text)
                            continue
                        
                        if text == "/start" or text == "/help":
                            self.handle_start(chat_id)
                        elif text == "🛡️ Protect HTML":
                            self.handle_protect_html(chat_id)
                        elif text == "🛡️ Protect Python":
                            self.handle_protect_python(chat_id)
                        elif text == "🔓 Decode HTML":
                            self.handle_decode_html(chat_id)
                        elif text == "🔓 Decode Python":
                            self.handle_decode_python(chat_id)
                        elif text == "🌐 Extract Website":
                            self.handle_extract(chat_id)
                        else:
                            self.send_message("❌ Send /start", chat_id)
                
                time.sleep(0.2)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Stopped[/yellow]")
                self.running = False
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                time.sleep(0.5)
        
        console.print("[green]✅ Stopped[/green]")

# ============================================================
# PROTECT FILE HELPER
# ============================================================

def protect_file_instant(filepath):
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return None, "File not found"
        
        if filepath.suffix.lower() == '.html' or filepath.suffix.lower() == '.htm':
            content = filepath.read_text(encoding='utf-8')
            protected = protect_html_fast(content)
            out = OUTPUT_PREFIX + filepath.name
            Path(out).write_text(protected, encoding='utf-8')
            return str(Path(out).absolute()), "HTML"
            
        elif filepath.suffix.lower() == '.py':
            content = filepath.read_text(encoding='utf-8')
            protected = protect_python_fast(content)
            out = OUTPUT_PREFIX + filepath.name
            
            with open(out, 'w', encoding='utf-8') as f:
                f.write(protected)
            
            if os.name != 'nt':
                os.chmod(out, 0o755)
            
            return str(Path(out).absolute()), "Python"
        else:
            return None, "Unsupported file type"
    except Exception as e:
        return None, str(e)

# ============================================================
# MAIN
# ============================================================
def main():
    console.clear()
    try:
        banner = pyfiglet.figlet_format("Dgtl Protect", font="small")
    except:
        banner = "=== Dgtl Protect ==="
    
    colored = Text(banner, style="bold cyan")
    console.print(Panel(colored, box=box.DOUBLE, border_style="cyan",
                      title="[bold green] v2.0 [/bold green]",
                      subtitle="[bold yellow] Developer: Aryan Afridi [/bold yellow]"))
    console.print()
    
    bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    bot.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")