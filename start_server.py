from playwright.sync_api import sync_playwright
import requests
import time
import os

# ================= 配置区 =================
SERVER_URL = "https://panel.vektalnodes.in/server/602306ee-8b39-4c02-a5fc-ee984940c43b"

# 从 GitHub Secrets 动态读取所有敏感信息
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
            # 强制浏览器走云端部署的家宽代理
            proxy={"server": "socks5://127.0.0.1:10808"},
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
        # 赋予家宽节点充分的加载时间 (60秒)
        page.set_default_timeout(60000)
        
        log("🚀 启动浏览器，通过纯净家宽访问 renqi 面板...")
        
        try:
            page.goto(SERVER_URL)
            page.wait_for_load_state("networkidle")
            time.sleep(3) 

            cookie_btn = page.locator("button:has-text('Accept & Continue')").first
            if cookie_btn.is_visible():
                log("🍪 发现 Cookie 授权弹窗，正在点击 Accept & Continue...")
                cookie_btn.click()
            
                log("⏳ 等待面板后台保存 Cookie 状态...")
                time.sleep(10) 
            
                saving_text = page.locator("text=Saving panel cookie consent...")
                if saving_text.is_visible() or cookie_btn.is_visible():
                    log("⚠️ 发现弹窗卡在保存状态（可能是广告追踪脚加载失败）。")
                    log("🔄 本地授权大概率已写入，直接强行刷新页面突破障碍！")
                    page.reload()
                    page.wait_for_load_state("networkidle")
                    time.sleep(5)
            
            # 判断是否在登录页
            if page.locator("input[type='password']").is_visible():
                log("⚠️ 发现密码框，Cookie 失效，启动账号密码备用登录方案...")
                page.locator("input[type='text'], input[name='user'], input[id='user']").first.fill(PANEL_USER)
                page.locator("input[type='password']").fill(PANEL_PASS)
                page.locator("button[type='submit']").click()
                
                page.wait_for_url("**/server/**")
                page.wait_for_load_state("networkidle")
                log("✅ 账号密码登录成功！")
            else:
                log("✅ 免密直登成功，已在控制台页面！")
            
            time.sleep(3) 

            log("🔎 检查是否触发了反广告拦截机制...")
            adblock_btn = page.locator("button:has-text('Recheck Now')").first
            if adblock_btn.is_visible():
                log("⚠️ 触发了 AdBlock 检测弹窗！正在尝试点击 Recheck Now...")
                adblock_btn.click()
                
                # 等待面板重新验证广告脚本加载情况
                time.sleep(8) 
                page.wait_for_load_state("networkidle")
                
                # 如果点完还在，说明真的是被 Xray 底层拦截了
                if adblock_btn.is_visible():
                    log("❌ Recheck 失败！请务必检查并移除 XRAY_JSON 中的广告拦截规则 (block)！")
                    
            # 寻找并点击 Start 按钮
            start_btn = page.locator("button:has-text('Start')").first
            
            if start_btn.is_visible():
                log("▶️ 发现 Start 按钮，正在点击启动...")
                start_btn.click()
                
                # ==========================================
                # 🟢 终极升级：动态等待 Watch Ad 并兼容多种 HTML 标签
                # ==========================================
                log("⏳ 已点击 Start，动态等待页面跳转和广告加载...")
                
                try:
                    # 同时匹配 button 和 a 标签，最多耐心等待 15 秒
                    watch_ad_btn = page.locator("button:has-text('Watch Ad'), a:has-text('Watch Ad')").first
                    watch_ad_btn.wait_for(state="visible", timeout=15000)
                    
                    log("📺 成功捕获广告界面！正在点击 Watch Ad...")
                    watch_ad_btn.click()
                    
                    log("⏳ 正在挂机播放广告 (可能长达30秒)，等待后台结算...")
                    # 动态监听是否自动跳回了控制台（出现 Auto Stop）
                    page.wait_for_selector("text=/Auto Stop:/i", timeout=60000)
                    log("✅ 广告结算完毕！已自动重定向回服务器页面。")
                    time.sleep(3) # 给页面渲染留点缓冲
                    
                except Exception:
                    log("⏩ 15秒内未检测到广告按钮，可能直接跳过了广告，尝试直接抓取状态...")
                    # 如果卡死，兜底刷新一下
                    if page.locator("text=Support VektalNodes").is_visible():
                        log("⚠️ 页面似乎卡在广告前置页，尝试强刷回退...")
                        page.goto(SERVER_URL)
                        page.wait_for_load_state("networkidle")
                        time.sleep(5)
                # ==========================================
                
                countdown_text = "未知"
                try:
                    auto_stop_element = page.locator("text=/Auto Stop:/i").first
                    countdown_text = auto_stop_element.inner_text(timeout=10000)
                    log(f"⏰ 成功捕获倒计时状态: {countdown_text}")
                except Exception:
                    log("⚠️ 未能抓取到倒计时文本，服务器可能响应较慢。")
                
                save_screenshot(page, "server_started_countdown")
                    
                log("🎉 renqi 服务器唤醒完毕！")
                send_telegram("🟢 renqi 服务器已唤醒", f"<b>指令状态：</b>成功跨越广告启动\n<b>面板状态：</b>{countdown_text}")

        except Exception as e:
            log(f"❌ 运行过程中发生异常: {e}")
            save_screenshot(page, "server_start_error")
            send_telegram("🚨 renqi 唤醒异常", f"<b>错误原因：</b>{e}")

        finally:
            time.sleep(2)
            browser.close()

if __name__ == "__main__":
    run_server_starter()
