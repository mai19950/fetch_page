# https://ip.ihuan.me/today/2025/06/18/12.html
from datetime import datetime
import os
import re
import pytz
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import aiofiles
import aiohttp
import asyncio
import yaml

IP_PATH = "proxy_ip.yml"
CHECK_URI = "http://www.baidu.com"
# CHECK_URI = "http://github.com"

semaphore = asyncio.Semaphore(100)

class AsyncChromeClient:
  def __init__(self, headless: bool = True):
    self.headless = headless
    self.driver = None

  async def __aenter__(self):
    def init_driver():
      load_dotenv()
      options = Options()
      if self.headless:
        options.add_argument("--headless")
      options.add_argument("--disable-gpu")
      options.add_argument("--no-sandbox")
      options.add_argument("--disable-dev-shm-usage")

      chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
      if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
      else:
        service = Service(ChromeDriverManager().install())
      return webdriver.Chrome(service=service, options=options)
    
    self.driver = await asyncio.to_thread(init_driver)
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    await asyncio.to_thread(self.driver.quit)

  async def get_page_source(self, url: str) -> str:
    await asyncio.to_thread(self.driver.get, url)
    return await asyncio.to_thread(lambda: self.driver.page_source)


async def check_ip(proxy: str, timeout: int = 5) -> str:
  """
  检查代理 IP 是否可用，目标站点为 https://www.baidu.com

  参数:
    proxy: 代理地址，例如 "http://123.123.123.123:8080"
    timeout: 超时时间（秒）

  返回:
    True 如果代理可用，否则 False
  """
  async with semaphore:
    try:
      timeout_cfg = aiohttp.ClientTimeout(total=timeout)
      async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        async with session.get(CHECK_URI, proxy=proxy, headers={"User-Agent": "Mozilla/5.0"}) as resp:
          if resp.status == 200:
            return proxy
          return ""
    except Exception as e:
      return ""


async def fetch_ip():
  async with AsyncChromeClient() as browser:
    beijing_tz = datetime.now(pytz.timezone("Asia/Shanghai"))
    url_part = beijing_tz.strftime("today/%Y/%m/%d/%H.html")
    html = await browser.get_page_source(f"https://ip.ihuan.me/{url_part}")
  matches = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d+\b", html)
  # print(matches)
  res_ip = list(set(f"http://{ip}" for ip in matches))
  print(f"proxy_ip: {len(res_ip)}")
  before_size = os.path.getsize(IP_PATH)
  # tasks = [check_ip(f"http://{ip}") for ip in matches]
  # ips = await asyncio.gather(*tasks, return_exceptions=True)
  # print(f"ips: {len(ips)}")
  # for ip in ips:
  #   if isinstance(ip, str) and ip != "":
  #     print(ip)
  #     res_ip.add(ip)
  async with aiofiles.open(IP_PATH, "w+", encoding="utf-8") as f:
    await f.write(yaml.safe_dump(res_ip, allow_unicode=True))
  after_size = os.path.getsize(IP_PATH)
  if after_size != before_size:
    github_output_path = os.environ.get("GITHUB_OUTPUT")
    if github_output_path:
      with open(github_output_path, 'a', encoding="utf-8") as f:
        f.write(f"proxy_msg=Update proxy_ip.yml at {beijing_tz.strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
  asyncio.run(fetch_ip())