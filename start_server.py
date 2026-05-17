from playwright.sync_api import sync_playwright
import requests
import time
import os

# ================= 配置区 =================
SERVER_URL = "https://panel.vektalnodes.in/server/602306ee-8b39-4c02-a5fc-ee984940c43b"

PANEL_USER = os.environ.get('PANEL_USER')
PANEL_PASS = os.environ.get('PANEL_PASS')
RAW_COOKIE = os.environ.get('PANEL_COOKIE', '')
TG_TOKEN = os.environ.get('TG_TOKEN')
TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
# ==========================================

def log(msg):
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{t}] {msg}")

def save_screenshot(page, name):
    try:
        os.makedirs("screenshots", exist_ok=True)
        path = f"screenshots/{name}.png"
        page.screenshot(path=path)
        log(f"📸 现场已保存: {path}")
    except Exception as e:
        log(f"⚠️ 截图失败: {e}")

def send_telegram(title, summary):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    text = f"🤖 <b>{title}</b>\n\n{summary}\n\n🕒 <i>{time.strftime('%Y-%m-%d %H:%M:%S')}</i>"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def parse_cookies(cookie_string):
    cookies = []
    if not cookie_string: return cookies
    for item in cookie_string.split(';'):
        if '=' in item:
            k, v = item.strip().split('=', 1)
            cookies.append({
                "name": k,
                "value": v,
                "domain": "panel.vektalnodes.in",
                "path": "/"
            })
    return cookies

def run_server_starter():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, 
            proxy={"server": "socks5://127.0.0.1:10808"}, # 强制走本地 Xray 家宽代理
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        parsed_cookies = parse_cookies(RAW_COOKIE)
        if parsed_cookies:
            context.add_cookies(parsed_cookies)
            log("🍪 成功注入身份 Cookie")

        page = context.new_page()
        log("🚀 启动浏览器，访问 renqi 服务器面板...")
        
        try:
            page.goto(SERVER_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(3) 
            
            # 精准判断：只有存在密码框，才是真正的登录页
            if page.locator("input[type='password']").is_visible():
                log("⚠️ 发现密码框，Cookie 失效，启动账号密码备用登录方案...")
                page.locator("input[type='text'], input[name='user'], input[id='user']").first.fill(PANEL_USER)
                page.locator("input[type='password']").fill(PANEL_PASS)
                page.locator("button[type='submit']").click()
                
                page.wait_for_url("**/server/**", timeout=20000)
                page.wait_for_load_state("networkidle")
                log("✅ 账号密码登录成功！")
            else:
                log("✅ 免密直登成功，已在控制台页面！")
            
            time.sleep(3) 
            
            # 寻找并点击 Start 按钮
            start_btn = page.locator("button:has-text('Start')").first
            
            if start_btn.is_visible():
                log("▶️ 发现 Start 按钮，正在点击启动...")
                start_btn.click()
                
                # 等待倒计时出现并读取它
                log("⏳ 已点击启动，等待面板响应倒计时...")
                time.sleep(5) 
                
                countdown_text = "未知"
                try:
                    auto_stop_element = page.locator("text=/Auto Stop:/i").first
                    countdown_text = auto_stop_element.inner_text(timeout=5000)
                    log(f"⏰ 成功捕获倒计时状态: {countdown_text}")
                except Exception:
                    log("⚠️ 未能抓取到倒计时文本，可能面板响应较慢。")
                
                save_screenshot(page, "server_started_countdown")
                    
                log("🎉 renqi 服务器唤醒完毕！")
                send_telegram("🟢 renqi 服务器已唤醒", f"<b>指令状态：</b>成功点击 Start\n<b>面板状态：</b>{countdown_text}")
            else:
                log("⚠️ 未找到 Start 按钮，服务器可能正在运行中。")
                save_screenshot(page, "server_already_running")
                send_telegram("🔵 renqi 服务器状态", "<b>执行结果：</b>未发现启动按钮，服务器可能正在运行。")

        except Exception as e:
            log(f"❌ 运行过程中发生异常: {e}")
            save_screenshot(page, "server_start_error")
            send_telegram("🚨 renqi 唤醒异常", f"<b>错误原因：</b>{e}")

        finally:
            browser.close()

if __name__ == "__main__":
    run_server_starter()
