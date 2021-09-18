from __future__ import annotations
import itertools
import os
from io import BytesIO
from random import choice
from sys import platform
from time import sleep
from collections.abc import Iterable, Iterator
from typing import Any, List

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
dataframe = pd.read_csv('https://docs.google.com/spreadsheets/d/1zaxjdu'
                        '9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw/export?'
                        'format=csv&'
                        'id=1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw&'
                        'gid=1789053577', dtype={'number': str, 'region': str})


class Data(Iterator):
    def __init__(self, argument, position) -> None:
        self._collection = dataframe[argument].dropna().tolist()
        self.position = position

    def __next__(self) -> str:
        # return next(self._collection)
        try:
            value = self._collection[self.position]
            self.position += 1
            return value
        except IndexError:
            raise StopIteration


class Russiandoska:
    def __init__(self, headless_input, proxy, position) -> None:
        self.position = position
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.astropoxy = self.astroproxy_balance()
        self.rucaptcha = self.rucaptcha_balance()
        print(f'captcha: {self.rucaptcha} astroproxy: {self.astropoxy}')
        # if self.astropoxy > 0:
        self.proxy = proxy
        options.add_argument(f'--proxy-server={self.proxy}')
        if headless_input:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

    @staticmethod
    def rucaptcha_balance():
        try:
            req = requests.get('http://rucaptcha.com/res.php?key=42a3a6c8322f1bec4b5ba84b85fdbe2f&action=getbalance')
            captcha_balance = int(req.json())
            return captcha_balance
        except Exception as error:
            LOGGER.error(error)
            return 0

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
        im.save(f'captcha_{self.position}.png')
        solver = CaptchaSolver('rucaptcha', api_key='42a3a6c8322f1bec4b5ba84b85fdbe2f')
        raw_data = open(f'captcha_{self.position}.png', 'rb').read()
        print('решение капчи')
        try:
            captcha_answer = solver.solve_captcha(raw_data, recognition_time=80)
            return captcha_answer
        except CaptchaServiceError:
            return False

    def spam(self, title, description, category, region, number):
        try:
            self.driver.get(category)
            country = '/html/body/div/div[3]/div[2]/form/div[3]/select[1]/option[2]'
            WebDriverWait(self.driver, 15).until(ec.presence_of_element_located((By.XPATH, country))).click()
            # city_choice = choice(['Moscow', 'spb', 'sochi'])
            # city_choice = choice(['Moscow', 'spb'])
            city_choice = 'Moscow'
            if city_choice == 'Moscow':
                city = f'//*[@id="a12"]/option[4]'
                self.driver.find_element_by_xpath(city).click()
                region = f'//*[@id="a13"]/option[{region}]'
                self.driver.find_element_by_xpath(region).click()
            # if city_choice == 'spb':
            #     region = f'//*[@id="a12"]/option[7]'
            #     self.driver.find_element_by_xpath(region).click()
            # if city_choice == 'sochi':
            #     region = f'//*[@id="a12"]/option[2]'
            #     self.driver.find_element_by_xpath(region).click()
            #     city = f'//*[@id="a13"]/option[4]'
            #     self.driver.find_element_by_xpath(city).click()
            title_input = '//input[@name="title"]'
            self.driver.find_element_by_xpath(title_input).send_keys(title)
            details_textarea = '//textarea[@name="detail"]'
            self.driver.find_element_by_xpath(details_textarea).send_keys(description)
            email = str(Mailbox())
            input_email = '//input[@id="email"]'
            self.driver.find_element_by_xpath(input_email).send_keys(email)
            input_email = '//input[@id="email_confirm"]'
            self.driver.find_element_by_xpath(input_email).send_keys(email)
            phone_input = '//input[@name="pub_phone1"]'
            self.driver.find_element_by_xpath(phone_input).send_keys(number)
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
            assert 'Вы допустили ошибку. Исправьте ее, и попробуйте еще раз' not in self.driver.page_source
            publish_input = '//input[@value="Опубликовать"]'
            WebDriverWait(self.driver, 15).until(
                ec.presence_of_element_located((By.XPATH, publish_input))).click()
            self.check_mail(email)
            LOGGER.info(f'{self.position} {number} опубликован')
            return True
        except (AssertionError, TimeoutException, SolutionTimeoutError, WebDriverException) as error:
            LOGGER.error(f'{self.position} {number} не опубликован')
            return False


def main(position):
    headless = False
    titles = itertools.cycle(Data('titles', position))
    details = itertools.cycle(Data('details', position))
    proxys = itertools.cycle(Data('proxy', position))
    while True:
        categories = Data('category', position)
        for category in categories:
            regions = Data('region', 0)
            for region in regions:
                numbers = Data('number', 0)
                for number in numbers:
                    doska = Russiandoska(headless, next(proxys), position)
                    try:
                        doska.spam(next(titles), next(details), category, region, number)
                    except Exception as error:
                        LOGGER.exception(error)
                    doska.driver.quit()


if __name__ == '__main__':
    from threading import Thread
    threads = 3
    threads_list = []
    for i in range(threads):
        thread = Thread(target=main, args=(i,))
        threads_list.append(thread)
        thread.start()
    for th in threads_list:
        th.join()
