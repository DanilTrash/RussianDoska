import argparse
import itertools
import logging
import os
from io import BytesIO
from random import choice
from re import findall
from time import sleep

import pandas as pd
import requests
from PIL import Image
from captcha_solver import CaptchaServiceError, CaptchaSolver, SolutionTimeoutError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from onesec_api import Mailbox

logger = logging.getLogger('main')
consolehandler = logging.StreamHandler()
fileHandler = logging.FileHandler('log.log', encoding='utf-8', mode='w')
logger.addHandler(fileHandler)
logger.addHandler(consolehandler)
formatter = logging.Formatter('%(asctime)s ~ %(levelname)s: %(message)s')
fileHandler.setFormatter(formatter)
logger.setLevel(logging.INFO)
consolehandler.setLevel(logging.INFO)
fileHandler.setLevel(logging.INFO)


class Russiandoska():
    def __init__(self, titles, details, headless):
        self.title = choice(titles)
        self.detail = choice(details)
        options = webdriver.ChromeOptions()
        astropoxy_balance = self.astroproxy_balance()
        rucaptcha_balance = self.rucaptcha_balance()
        print(f'astroproxy: {astropoxy_balance} captcha: {rucaptcha_balance}')
        if astropoxy_balance > 0:
            print(f'proxy connected ')
            options.add_argument(rf'--proxy-server=109.248.7.161:11795')
        if headless:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

    def rucaptcha_balance(self):
        req = requests.get('http://rucaptcha.com/res.php?key=42a3a6c8322f1bec4b5ba84b85fdbe2f&action=getbalance')
        captcha_balance = int(req.json())
        return captcha_balance

    def astroproxy_balance(self):
        while True:
            try:
                req = requests.get('https://astroproxy.com/api/v1/balance?token=81c870ced3d7a5d5')
                astroproxy_balance = req.json()['data']['balance']
                return astroproxy_balance
            except KeyError as error:
                logger.warning(error)

    def check_mail(self, email):
        for _ in range(2):
            sleep(1)
            login, domain = email.split('@')
            API = 'https://www.1secmail.com/api/v1/'
            response = requests.get(API, params={'action': 'getMessages',
                                                 'login': login,
                                                 'domain': domain})
            try:
                response_json_id_ = response.json()[0]['id']
                message = requests.get(API, params={'action': 'readMessage',
                                                    'login': login,
                                                    'domain': domain,
                                                    'id': response_json_id_})
                link = message.json()['textBody'].split('\n')[3]
                r = requests.get(link)
                return
            except IndexError:
                continue

    def take_captcha(self, captcha):
        element = self.driver.find_element_by_xpath(captcha)
        location = element.location_once_scrolled_into_view
        size = element.size
        png = self.driver.get_screenshot_as_png()  # saves screenshot of entire page

        im = Image.open(BytesIO(png))  # uses PIL library to open image in memory

        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        im = im.crop((left, top, right, bottom))  # defines crop points
        im.save('captcha.png')  # saves new cropped image
        solver = CaptchaSolver('rucaptcha', api_key='42a3a6c8322f1bec4b5ba84b85fdbe2f')
        raw_data = open('captcha.png', 'rb').read()
        print('решение капчи')
        try:
            captcha_answer = solver.solve_captcha(raw_data, recognition_time=80)  # fixme CaptchaServiceError
            return captcha_answer
        except CaptchaServiceError:
            return False

    def spam(self):
        try:
            print('вход')
            self.driver.get(choice(df['category'].dropna().tolist()))
            country = '/html/body/div/div[3]/div[2]/form/div[3]/select[1]/option[2]'
            try:
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, country))).click()
            except TimeoutException:
                print('не удалиось на страницу')
                return False
            city = f'//*[@id="a12"]/option[{choice([7, 4])}]'
            self.driver.find_element_by_xpath(city).click()
            titile_input = '//input[@name="title"]'
            self.driver.find_element_by_xpath(titile_input).send_keys(self.title)
            details_textarea = '//textarea[@name="detail"]'
            self.driver.find_element_by_xpath(details_textarea).send_keys(self.detail)
            email = str(Mailbox())
            print(email)
            input_email = '//input[@id="email"]'
            self.driver.find_element_by_xpath(input_email).send_keys(email)
            input_email = '//input[@id="email_confirm"]'
            self.driver.find_element_by_xpath(input_email).send_keys(email)
            phone_number = next(numbers)
            phone_input = '//input[@name="pub_phone1"]'
            self.driver.find_element_by_xpath(phone_input).send_keys(phone_number)
            random_image = choice([
                file for file in os.listdir(f'/home/danil/images') if findall(r'\w+$', file)[0] == 'jpg'
            ])
            jpg = f"/home/danil/images/{random_image}"  # image.jpg
            image_input = f'//input[@name="image_upload[0][1]"]'
            self.driver.find_element_by_xpath(image_input).send_keys(jpg)
            captcha_element = '//*[@id="captcha"]'
            solved_captcha = self.take_captcha(captcha_element)
            if not solved_captcha:
                print('капча не решена сервисом')
                return False
            self.driver.find_element_by_xpath('//input[@name="image_control"]').send_keys(solved_captcha)
            success_button = '//button[@name="preview"]'
            self.driver.find_element_by_xpath(success_button).click()  # fixme
            sleep(1)
            try:
                assert 'Вы допустили ошибку. Исправьте ее, и попробуйте еще раз' not in self.driver.page_source
                publish_input = '//input[@value="Опубликовать"]'
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, publish_input))).click()
                self.check_mail(email)
                logger.info(f'advertisement published {phone_number} {email}')
                return True
            except (AssertionError, TimeoutException):
                print('объявление не опубликовано')
                return False
        except (TimeoutException, SolutionTimeoutError, WebDriverException) as error:
            logger.exception(error)
            return False


if __name__ == '__main__':
    df = pd.read_csv('https://docs.google.com/spreadsheets/d/1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw/export?'
                     'format=csv&'
                     'id=1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw&'
                     'gid=1789053577', dtype={'number': str})
    titles = df['titles'].dropna().tolist()
    details = df['details'].dropna().tolist()
    numbers = itertools.cycle(df['number'].dropna().tolist())
    headless: bool = False
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", dest="headless", default=headless, type=bool)
    args = parser.parse_args()
    while True:
        doska = Russiandoska(titles, details, headless=args.headless)
        doska.spam()
        doska.driver.quit()
