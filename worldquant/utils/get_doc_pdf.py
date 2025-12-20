import json
import time
import base64
import os
from os.path import expanduser

# 检查依赖库
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("❌ 缺少必要的库，请先运行: pip install selenium webdriver-manager")
    exit(1)

def get_credentials():
    """读取本地账号密码文件"""
    path = expanduser(r"C:\Users\nay\Desktop\qr\qr\worldquant\idcode.txt")
    with open(path) as f:
        return json.load(f)

def save_url_to_pdf(url, output_filename):
    creds = get_credentials()
    username, password = creds
    
    # 设置 Chrome 选项
    chrome_options = Options()
    # chrome_options.add_argument('--headless') # 如果不想看到浏览器弹出，取消此行注释
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')
    
    print("🚀 正在启动浏览器...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 1. 登录流程
        print("🔐 正在登录 WorldQuant Brain...")
        driver.get("https://platform.worldquantbrain.com/login")
        
        wait = WebDriverWait(driver, 30)
        
        # 定位并输入账号 (根据页面常见的 name="username" 或 type="email")
        print("   输入账号...")
        email_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='username'], input[type='email']")))
        email_field.clear()
        email_field.send_keys(username)
        
        # 定位并输入密码
        print("   输入密码...")
        pass_field = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password']")
        pass_field.clear()
        pass_field.send_keys(password)
        
        # 处理 Cookie 弹窗 (防止遮挡登录按钮)
        try:
            print("   检查 Cookie 弹窗...")
            cookie_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept')]"))
            )
            cookie_btn.click()
            print("   ✅ 已点击 Accept 按钮")
            time.sleep(1)
        except Exception:
            print("   ℹ️ 未检测到 Cookie 弹窗或无需处理")

        # 点击登录按钮
        print("   点击登录...")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # 等待登录跳转 (简单等待几秒，确保 Token 写入和页面跳转)
        time.sleep(8) 
        
        # 2. 跳转到目标文档
        print(f"📄 正在跳转至文档: {url}")
        driver.get(url)
        
        # 等待文档内容渲染 (给予充分时间加载图片和文字)
        time.sleep(5)
        
        # 3. 生成 PDF
        print("🖨️  正在生成 PDF...")
        # 使用 Chrome DevTools Protocol (CDP) 的 Page.printToPDF 命令直接生成 PDF 数据
        result = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,       # 打印背景图/色
            "landscape": False,            # 纵向
            "paperWidth": 8.27,            # A4 宽度 (英寸)
            "paperHeight": 11.69,          # A4 高度 (英寸)
            "marginTop": 0.4,
            "marginBottom": 0.4,
            "marginLeft": 0.4,
            "marginRight": 0.4,
            "displayHeaderFooter": False   # 不显示页眉页脚
        })
        
        # 保存文件
        output_path = expanduser(fr"C:\Users\nay\Desktop\qr\qr\worldquant\{output_filename}")
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(result['data']))
            
        print(f"✅ PDF 保存成功: {output_path}")
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        # 如果出错，可以查看浏览器界面了解原因
    # finally:
    #     driver.quit()

if __name__ == "__main__":
    target_url = "https://platform.worldquantbrain.com/learn/documentation/discover-brain/about-brain-platform"
    save_url_to_pdf(target_url, "about_brain_platform.pdf")