from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import subprocess
import webbrowser
import time
import datetime

subprocess.Popen(r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrometemp"')

option = Options()
option.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
try:
    driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=option)
except:
    chromedriver_autoinstaller.install(True)
    driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=option)
driver.implicitly_wait(10)

url = 'https://3282-1-220-128-60.ngrok.io/room/a'
driver.get(url)


imageList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
for i in imageList:
    time.sleep(3)
    imageName = str(i) + ".png"
    driver.save_screenshot(imageName)
    webbrowser.open(imageName)