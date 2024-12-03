# -*- coding: utf-8 -*-
"""
Created on Sun May 26 09:06:49 2024

@author: admin
"""

import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image
import io
import time

# 크롬드라이버 위치 설정
DRIVER_PATH = r'C:\python\chromedriver.exe'

def fetch_image_urls(search_name, driver):
    #url = f'https://www.google.com/search?q={search_name}&source=lnms&tbm=isch'
   
    url = f'https://search.naver.com/search.naver?ssc=tab.image.all&where=image&sm=tab_jum&query={search_name}'
    driver.get(url)
    time.sleep(2)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    img_tags = soup.find_all('img')
    urls = [img['src'] for img in img_tags if img.get('src', '').startswith('http')]
    return urls

def save_images(urls, search_name):
    os.makedirs(f'./images/{search_name}', exist_ok=True)
    count = 0
    for url in urls:
        try:
            response = requests.get(url, stream=True)
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size
            if width >= 250 and height >= 250:
                file_name = f'./images/{search_name}/{count}.png'
                with open(file_name, 'wb') as out_file:
                    out_file.write(response.content)
                print(f'{file_name} saved')
                count += 1
                if count == 80:
                    break
        except Exception as e:
            print(f"Error saving {url}: {e}")

def main():
    search_terms = ['랙돌','샴고양이','노르웨이숲','메인쿤','브리티시 숏헤어','코리안 숏헤어','스코티시 폴드','러시안 블루','뱅갈고양이','페르시안','아비시니안','아메리칸 숏헤어','터키시 앙고라','스핑크스 고양이'] 

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        for term in search_terms:
            urls = fetch_image_urls(term, driver)
            save_images(urls, term)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
