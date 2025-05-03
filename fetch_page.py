# -*- coding: utf-8 -*-

import random
import json
import string
import sys
import requests
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager # 用于自动下载 Chromedriver
from selenium.webdriver.chrome.service import Service as ChromeService



DRIVER_PATH = r"E:\23_script\chromedriver.exe"
TARGET_URL = "https://tuijianvpn.com/1044"

class FetchPage:
  def __init__(self, url: str, timeout:int=30, driver_path:str = DRIVER_PATH, cookie: str = ""):
    self.url = url.strip()
    self.driver_path = driver_path
    self.link = self.time = ""
    self.timeout = timeout    
    self.driver = None
    self.wait = None
    self.cookie = cookie
  
  @staticmethod
  def random_str(length: int) -> str:
    """生成指定长度的随机字母数字字符串"""
    letters_and_digits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

  def config_chrome(self):
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 启用无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--log-level=3")  # 降低日志等级（只显示错误）
    # --- 尝试添加一些让浏览器看起来更真实的选项 ---
    # 设置 User-Agent (模拟 Windows 上的 Chrome)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36") # 示例 User-Agent，请根据需要更新
    # 移除一些可能暴露自动化的标志
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # 阻止 navigator.webdriver 标志
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    self.chrome_options = chrome_options
    # print(">>> 正在初始化 WebDriver 并启动 Chrome 浏览器...")
    # self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
    if sys.platform == "win32":
      service = ChromeService(self.driver_path)
    else:
      service = ChromeService(ChromeDriverManager().install())
    self.driver = webdriver.Chrome(service=service, options=chrome_options)
    # print(">>> WebDriver 初始化成功。")
    self.driver.set_page_load_timeout(self.timeout)
    self.wait = WebDriverWait(self.driver, self.timeout)
    self.driver.get(self.url)

  def wait_visibility(self, selector: str):
    try:
      self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
      # print(f"wait element: {selector}")
      return True
    except Exception as e:
      print(f">> not found element: {selector}")
      return False

  def set_input_value(self, value: str, selector: str):
    self.wait_visibility(selector)
    input_element = self.driver.find_element(By.CSS_SELECTOR, selector)
    input_element.send_keys(value) # 发送按键，填写名字
    # print(f"set input value: {selector}")
    return input_element

  def click_element(self, selector: str):
    self.wait_visibility(selector)
    input_element = self.driver.find_element(By.CSS_SELECTOR, selector)
    input_element.click()
    # print(f"click element: {selector}")
    return input_element

  def add_cookie(self):
    if not self.cookie:
      return
    cookies = self.cookie.split(';')
    cookies = [c.strip() for c in cookies if c.strip()]
    cookie_domain = urllib.parse.urlparse(self.url).hostname

    for cookie in cookies:
      parts = cookie.split('=', 1)
      if len(parts) == 2:
        name = parts[0]
        value = urllib.parse.unquote(parts[1])
        self.driver.add_cookie({
          'name': name,
          'value': value,
          'domain': cookie_domain,
          'path': '/'
        })


class FetchTuiJian(FetchPage):
  def __init__(self, url, timeout = 30, driver_path = DRIVER_PATH, cookie = ""):
    super().__init__(url, timeout, driver_path, cookie)

  def post_comment(self):
    # print("\n>>> 开始执行模拟交互操作...")
    comment_input_selector = '#wpd-editor-0_0 > div.ql-editor > p'
    # 1. 等待评论输入框可点击并点击
    # print(">>> 正在等待评论输入框并点击...")
    self.click_element(comment_input_selector)
    # 2. 生成随机文本并设置到输入框 (使用 JS，模拟 Go 脚本的 Evaluate)
    rand_str = self.random_str(5)
    self.driver.execute_script(f"document.querySelector('{comment_input_selector}').textContent = '{rand_str}';")
    # print(">>> 评论文本已设置。")
    # print("\n>>> 开始执行模拟填写表单和提交...")
    # 定义新的选择器 (与 Go 脚本中的对应)
    name_input_selector = '#wc_name-0_0' # 名字输入框选择器
    email_input_selector = '#wc_email-0_0' # 邮箱输入框选择器
    submit_button_selector = '#wpd-field-submit-0_0' # 提交按钮选择器
    # 3. 填写名字
    self.uname = self.random_str(5) # 生成随机名字
    # 等待名字输入框可见并找到元素
    self.set_input_value(self.uname, name_input_selector)
    # 4. 填写邮箱
    self.set_input_value(self.random_str(5) + "@gmail.com", email_input_selector)
    # 5. 等待提交按钮可点击并点击
    self.click_element(submit_button_selector)
    # print(">>> 模拟填写表单和提交完成。")

  def reload_page(self):
    # print("\n>>> 开始执行等待结果、重新加载和提取数据...")
    # 定义需要等待的元素选择器 
    wait_after_submit_selector_template = 'img[alt="%s"]'
    # 提取数据的元素选择器
    extracted_element_selector = '.su-box-content.su-u-clearfix.su-u-trim pre'
    # 6. 等待提交后出现的元素 (使用之前生成的随机名字在 alt 属性中查找 img)
    # 需要使用之前生成的名字变量。确保你在函数顶部定义了 name 和 email 变量，或者在这里能访问到它们。
    # 检查一下你之前的代码，name 变量应该在填写名字前生成并赋值了。
    wait_selector_after_submit = wait_after_submit_selector_template % self.uname # 使用之前生成的随
    # 等待元素可见
    self.wait_visibility(wait_selector_after_submit)
    # 7. 重新加载页面
    # print(">>> 正在重新加载页面...")
    self.driver.refresh()
    # 8. 等待提取数据的元素可见 (在重新加载后)
    self.wait_visibility(extracted_element_selector)
    # 9. 提取数据
    self.link = self.driver.execute_script(f"return document.querySelectorAll('{extracted_element_selector}')[0]?.innerText;")
    time_element = self.driver.execute_script(f"return document.querySelector('.su-label.su-label-type-success')?.textContent")
    if time_element:
      self.time = time_element.split('：')[1].strip()
    print(f"FetchTuiJian: {self.link}, {self.time}")

  def main(self):
    try:
      self.config_chrome()
      self.post_comment()
      self.reload_page()
    except Exception as e:
      print(f"\n>>> 发生错误: {e}")
    finally:
      if self.driver:
        # print(">>> 退出 WebDriver.")
        self.driver.quit()
      return self


class FetchVpnea(FetchTuiJian):
  def __init__(self, url, timeout=30, driver_path=DRIVER_PATH, cookie=""):
    super().__init__(url, timeout, driver_path, cookie)

  def post_comment(self):
    # 添加评论内容
    textarea_selector = 'textarea.text.joe_owo__target'
    self.click_element(textarea_selector).send_keys(self.random_str(5))
    # 用户名 邮箱
    author_input_selector = 'input[name="author"]'
    email_input_selector = 'input[name="mail"]'
    self.uname = self.random_str(5)
    self.set_input_value(self.uname, author_input_selector)
    self.set_input_value(self.random_str(5) + "@gmail.com", email_input_selector) # 发送按键，填写邮箱
    # 点击发送
    submit_button_selector = 'div.submit > button[type="submit"]'
    self.click_element(submit_button_selector)
    self.extracted_element_selector = '.joe_container code'
    if not self.wait_visibility(self.extracted_element_selector):
      self.add_cookie()
      self.driver.refresh()

  def reload_page(self):
    # self.driver.refresh()    
    self.wait_visibility(self.extracted_element_selector)
    self.link = self.driver.execute_script(f"return document.querySelector('{self.extracted_element_selector}')?.innerText;")
    time_ele = self.driver.execute_script("return document.querySelector('.success .joe_message__content')?.textContent;")
    if time_ele:
      self.time = time_ele.split('：')[1].strip()
    print(f"FetchVpnea: {self.link}, {self.time}")


def main():
  filepath = 'data.json'
  const = "constant.json"
  data = []
  flag = False
  try:
    with open(filepath, "rb") as f:
      data = json.load(f)
  except:
    pass
  with open(const, "rb") as f:
    page_data = json.load(f)
  for item in page_data:
    url, page = item["url"], item["page"]
    page_it = next((d for d in data if d["page"] == page), None)
    if page_it is None:
      page_it = {}
      data.append(page_it)
    try:
      with requests.get(page_it.get("link", ""), timeout=10, headers={"user-agent": "v2rayNG/1.8.3"}) as res:
        res.raise_for_status()
    except:
      flag = True
      instance = globals()[item["class"]](url, cookie=item["cookie"]).main()
      page_it["page"] = page
      page_it["link"] = instance.link
      page_it["time"] = instance.time

  if flag:
    with open(filepath, "w+", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
  # FetchVpnea(url="https://vpnea.com/mfjd.html").main()
  # FetchVpnea(url="https://vpnoe.com/mfjd.html").main()
  # FetchTuiJian(TARGET_URL).main()
  # pass
  main()