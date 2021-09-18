from __future__ import annotations

import itertools
import os
from collections.abc import Iterator
from io import BytesIO
from random import choice
from sys import platform
from time import sleep

import pandas as pd
import numpy as np
import requests
from PIL import Image
from captcha_solver import CaptchaServiceError, CaptchaSolver, SolutionTimeoutError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

import logger
from onesec_api import Mailbox

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
    def __init__(self, argument, position, threads=1) -> None:
        if threads > 1:
            self._collection = np.array_split(dataframe[argument].dropna().tolist(), threads)[position]
        else:
            self._collection = dataframe[argument].dropna().tolist()
        self.position = position

    def __next__(self) -> str:
        try:
            value = self._collection[self.position]
            self.position += 1
            return value
        except IndexError:
            raise StopIteration


class Russiandoska:
    def __init__(self, headless_input, proxy, position=0) -> None:
        self.email = str(Mailbox())
        self.position = position
        self.proxy = proxy
        self.astropoxy = self.astroproxy_balance()
        self.rucaptcha = self.rucaptcha_balance()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
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
            return 0

    @staticmethod
    def astroproxy_balance():
        try:
            req = requests.get('https://astroproxy.com/api/v1/balance?token=81c870ced3d7a5d5')
            astroproxy_balance = req.json()['data']['balance']
            return astroproxy_balance
        except Exception as error:
            return 0

    @staticmethod
    def check_mail(email):  # fix убрать этот метод в класс Mailbox
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

    @staticmethod
    def solve_captcha(location, size, png, name):
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        im = Image.open(BytesIO(png))
        im = im.crop((left, top, right, bottom))
        im.save(name)
        solver = CaptchaSolver('rucaptcha', api_key='42a3a6c8322f1bec4b5ba84b85fdbe2f')
        raw_data = open(name, 'rb').read()
        print('solving captcha')
        try:
            captcha_answer = solver.solve_captcha(raw_data, recognition_time=80)
            return captcha_answer
        except (CaptchaServiceError, SolutionTimeoutError):
            return False

    def city_region_fields(self, region, city='Moscow'):
        try:
            country = '/html/body/div/div[3]/div[2]/form/div[3]/select[1]/option[2]'
            WebDriverWait(self.driver, 15).until(ec.presence_of_element_located((By.XPATH, country)),
                                                 'TimeoutException unable to locate country element xpath').click()
            if city == 'Moscow':
                self.driver.find_element_by_xpath(f'//*[@id="a12"]/option[4]').click()
                self.driver.find_element_by_xpath(f'//*[@id="a13"]/option[{region}]').click()
            if city == 'spb':
                self.driver.find_element_by_xpath(f'//*[@id="a12"]/option[7]').click()
            if city == 'sochi':
                self.driver.find_element_by_xpath(f'//*[@id="a12"]/option[2]').click()
                self.driver.find_element_by_xpath(f'//*[@id="a13"]/option[4]').click()
            return 'city_region_fields True'
        except TimeoutException as error:
            LOGGER.error(error)
            return 'TimeoutException'
        except Exception as error:
            LOGGER.exception(error)
            return 'city_region_fields False'

    def input_fields(self, title, description, number):
        try:
            title_input = '//input[@name="title"]'
            self.driver.find_element_by_xpath(title_input).send_keys(title)
            details_textarea = '//textarea[@name="detail"]'
            self.driver.find_element_by_xpath(details_textarea).send_keys(description)
            input_email = '//input[@id="email"]'
            self.driver.find_element_by_xpath(input_email).send_keys(self.email)
            input_email = '//input[@id="email_confirm"]'
            self.driver.find_element_by_xpath(input_email).send_keys(self.email)
            phone_input = '//input[@name="pub_phone1"]'
            self.driver.find_element_by_xpath(phone_input).send_keys(number)
            random_image = choice([file for file in os.listdir(IMAGES_PATH) if file.endswith('jpg')])
            image_input = f'//input[@name="image_upload[0][1]"]'
            self.driver.find_element_by_xpath(image_input).send_keys(f"{IMAGES_PATH}/{random_image}")
            return 'input_fields True'
        except WebDriverException:
            LOGGER.error('input_fields WebDriverException')
            return 'input_fields False'
        except Exception as error:
            LOGGER.exception(error)
            return 'input_fields False'

    def captcha_input(self):
        try:
            captcha_xpath = '//*[@id="captcha"]'
            element = self.driver.find_element_by_xpath(captcha_xpath)
            location = element.location_once_scrolled_into_view
            png = self.driver.get_screenshot_as_png()
            captcha_answer_xpath = '//input[@name="image_control"]'
            solved_captcha = self.solve_captcha(location, element.size, png, f'captcha_{self.position}.png')
            if not solved_captcha:
                return 'captcha doesn`t solved'
            self.driver.find_element_by_xpath(captcha_answer_xpath).send_keys(solved_captcha)
            return True
        except NoSuchElementException:
            LOGGER.error('captcha_input NoSuchElementException')
            return False
        except Exception as error:
            LOGGER.exception(error)
            return False

    def success_page(self):
        try:
            success_button = '//button[@name="preview"]'
            self.driver.find_element_by_xpath(success_button).click()
            sleep(1)
            assert 'Вы допустили ошибку. Исправьте ее, и попробуйте еще раз' not in self.driver.page_source
            publish_input = '//input[@value="Опубликовать"]'
            WebDriverWait(self.driver, 7).until(
                ec.presence_of_element_located((By.XPATH, publish_input)),
                'TimeoutException //input[@value="Опубликовать"]').click()
            self.check_mail(self.email)
            return True
        except AssertionError:
            return False
        except (TimeoutException, NoSuchElementException) as error:
            LOGGER.error(error)
            return False
        except Exception as error:
            LOGGER.exception(error)
            return False

    def fail(self):
        try:
            error_info = WebDriverWait(self.driver, 2).until(
                lambda d: self.driver.find_element_by_xpath('//*[@id="wrapper"]/div[3]'),
                message='TimeoutException error info')
            print(error_info.text)
            return True
        except TimeoutException:
            return False

    def spam(self, category, region, title, description, number):
        print(f'captcha: {self.rucaptcha} astroproxy: {self.astropoxy}')
        self.driver.get(category)
        result = self.city_region_fields(region, city='Moscow') == 'TimeoutException'
        if result == 'TimeoutException':
            return result
        self.input_fields(title, description, number)
        result = self.captcha_input()
        if not result:
            return result
        result = self.success_page()
        LOGGER.info(result)
        if not result:
            self.fail()
        return result


def main(position, threads):
    headless = False
    titles = itertools.cycle(Data('titles', position, threads))
    details = itertools.cycle(Data('details', position, threads))
    proxys = itertools.cycle(Data('proxy', position))
    while True:
        doska = Russiandoska(headless, next(proxys), position)
        categories = Data('category', position)
        for category in categories:
            regions = Data('region', 0)
            for region in regions:
                numbers = Data('number', 0)
                for number in numbers:
                    doska.spam(category, region, next(titles), next(details), number)
        doska.driver.quit()


if __name__ == '__main__':
    from threading import Thread
    threads = 3
    threads_list = []
    for i in range(threads):
        thread = Thread(target=main, args=(i, threads))
        threads_list.append(thread)
        thread.start()
    for th in threads_list:
        th.join()
