import argparse
import itertools
import os
from io import BytesIO
from random import choice
from sys import platform
from time import sleep

import pandas as pd
import requests
from PIL import Image
from captcha_solver import CaptchaServiceError, CaptchaSolver, SolutionTimeoutError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from onesec_api import Mailbox
import logger


LOGGER = logger.logger('Russiandoska')
if platform == "linux" or platform == "linux2":
    IMAGES_PATH = '/home/danil/images'
elif platform == "win32":
    IMAGES_PATH = 'C:/Users/KIEV-COP-4/Desktop/images'


class Russiandoska:
    def __init__(self, titles_input, details_input, headless_input):
        self.title = choice(titles_input)
        self.detail = choice(details_input)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        astropoxy_balance = self.astroproxy_balance()
        rucaptcha_balance = self.rucaptcha_balance()
        print(f'astroproxy: {astropoxy_balance} captcha: {rucaptcha_balance}')
        if astropoxy_balance > 0:
            print(f'proxy connected ')
            options.add_argument(rf'--proxy-server=109.248.7.161:11795')
        if headless_input:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

    @staticmethod
    def rucaptcha_balance():
        req = requests.get('http://rucaptcha.com/res.php?key=42a3a6c8322f1bec4b5ba84b85fdbe2f&action=getbalance')
        captcha_balance = int(req.json())
        return captcha_balance

    @staticmethod
    def astroproxy_balance():
        try:
            req = requests.get('https://astroproxy.com/api/v1/balance?token=81c870ced3d7a5d5')
            astroproxy_balance = req.json()['data']['balance']
            return astroproxy_balance
        except Exception as error:
            LOGGER.error(error)
            return 0

    @staticmethod
    def check_mail(email):
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
                requests.get(link)
                return
            except IndexError:
                continue

    def take_captcha(self, captcha):
        element = self.driver.find_element_by_xpath(captcha)
        location = element.location_once_scrolled_into_view
        size = element.size
        png = self.driver.get_screenshot_as_png()
        im = Image.open(BytesIO(png))
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        im = im.crop((left, top, right, bottom))
        im.save('captcha.png')
        solver = CaptchaSolver('rucaptcha', api_key='42a3a6c8322f1bec4b5ba84b85fdbe2f')
        raw_data = open('captcha.png', 'rb').read()
        print('решение капчи')
        try:
            captcha_answer = solver.solve_captcha(raw_data, recognition_time=80)
            return captcha_answer
        except CaptchaServiceError:
            return False

    def spam(self):
        try:
            print('вход')
            self.driver.get(choice(df['category'].dropna().tolist()))
            country = '/html/body/div/div[3]/div[2]/form/div[3]/select[1]/option[2]'
            try:
                WebDriverWait(self.driver, 15).until(ec.presence_of_element_located((By.XPATH, country))).click()
            except TimeoutException:
                print('не удалиось на страницу')
                return False
            msc = 4
            # spb = 7
            # city = f'//*[@id="a12"]/option[{choice([spb, msc])}]'
            city = f'//*[@id="a12"]/option[{choice([msc])}]'
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
            random_image = choice([file for file in os.listdir(IMAGES_PATH) if file.endswith('jpg')])
            jpg = f"{IMAGES_PATH}/{random_image}"  # image.jpg
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
                    ec.presence_of_element_located((By.XPATH, publish_input))).click()
                self.check_mail(email)
                LOGGER.info(f'advertisement published {phone_number} {email}')
                return True
            except (AssertionError, TimeoutException):
                print('объявление не опубликовано')
                return False
        except (TimeoutException, SolutionTimeoutError, WebDriverException) as error:
            LOGGER.exception(error)
            return False


def main():
    try:
        doska = Russiandoska(titles, details, args.headless)
        doska.spam()
        doska.driver.quit()
    except Exception as error:
        LOGGER.exception(error)
        logger.email_alert('russianDoska', 'LOG', 'log.log')


if __name__ == '__main__':
    headless: bool = False
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", dest="headless", default=headless, type=bool)
    args = parser.parse_args()
    df = pd.read_csv('https://docs.google.com/spreadsheets/d/1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw/export?'
                     'format=csv&'
                     'id=1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw&'
                     'gid=1789053577', dtype={'number': str})
    titles = df['titles'].dropna().tolist()
    details = df['details'].dropna().tolist()
    numbers = itertools.cycle(df['number'].dropna().tolist())
    while True:
        main()
