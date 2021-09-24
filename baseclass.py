import os
from io import BytesIO
from random import choice
from sys import platform
from time import sleep
import requests
from PIL import Image
from captcha_solver import CaptchaServiceError, CaptchaSolver, SolutionTimeoutError
from selenium import webdriver

import logger
from onesec_api import Mailbox
from gologin import GoLogin
from data import Data


class BaseClass:
    LOGGER = logger.logger(__file__)
    if platform == "linux" or platform == "linux2":
        IMAGES_PATH = '/home/danil/images'
    elif platform == "win32":
        IMAGES_PATH = 'C:/Users/KIEV-COP-4/Desktop/images'

    def __init__(self, headless_input: bool = False, proxy: str = None, position: int = 0) -> None:
        self.email = str(Mailbox())
        self.position = position
        self.proxy = proxy
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        if headless_input:
            options.add_argument('--headless')

        self.driver = webdriver.Chrome(options=options)
        self.LOGGER.info(options.arguments)

    def tearddown(self) -> None:
        self.driver.quit()
        # sleep(2)
        # self.gl.stop()
        # sleep(2)
        # self.gl.delete(self.profile_id)

    @property
    def rucaptcha_balance(self) -> int:
        try:
            req = requests.get('http://rucaptcha.com/res.php?key=42a3a6c8322f1bec4b5ba84b85fdbe2f&action=getbalance')
            captcha_balance = int(req.json())
            return captcha_balance
        except Exception:
            return 0

    @property
    def astroproxy_balance(self) -> int:
        try:
            req = requests.get('https://astroproxy.com/api/v1/balance?token=81c870ced3d7a5d5')
            astroproxy_balance = req.json()['data']['balance']
            return astroproxy_balance
        except Exception:
            return 0

    @staticmethod
    def check_mail(email: str) -> None:  # fix убрать этот метод в класс Mailbox
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
    def solve_captcha(location: dict, size: dict, png: bytes, file_name: str) -> str:
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        im = Image.open(BytesIO(png))
        im = im.crop((left, top, right, bottom))
        im.save(file_name)
        solver = CaptchaSolver('rucaptcha', api_key='42a3a6c8322f1bec4b5ba84b85fdbe2f')
        raw_data = open(file_name, 'rb').read()
        print('solving captcha')
        try:
            captcha_answer = solver.solve_captcha(raw_data, recognition_time=80)
            return captcha_answer
        except (CaptchaServiceError, SolutionTimeoutError):
            return ''

    def get_random_image(self) -> str:
        random_image = choice([file for file in os.listdir(self.IMAGES_PATH) if file.endswith('jpg')])
        return f"{self.IMAGES_PATH}/{random_image}"
