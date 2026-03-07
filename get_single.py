import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.get("https://www.ouinfo.ca/scholarships/alumni-award-of-excellence-gold")
time.sleep(3)
with open("single_scholarship.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
driver.quit()
print("Saved single_scholarship.html")
