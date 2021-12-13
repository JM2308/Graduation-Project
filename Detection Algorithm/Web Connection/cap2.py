from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import subprocess
import webbrowser
import time
import pyscreenshot as ImageGrab
from tkinter import *

root = Tk()

monitor_height = root.winfo_screenheight()
monitor_width = root.winfo_screenwidth()

print("width x height = %d x %d (pixels)" % (monitor_width, monitor_height))
mainloop()

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


time.sleep(5)

im = ImageGrab.grab(bbox=(150, 200, 800, 1300))
im.save('part.png')
webbrowser.open('part.png')
