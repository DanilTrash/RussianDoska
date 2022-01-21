import configparser
import imaplib
import os
from io import BytesIO
from random import choice
from time import sleep

import mailparser
import requests
from PIL import Image
from captcha_solver import CaptchaServiceError, CaptchaSolver, SolutionTimeoutError
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

logger.add('log.log')


def check_mail_1secmain(email: str) -> None:  # fix separate extracting link from mail and going throw that link
    for _ in range(2):
        sleep(1)
        login, domain = email.split('@')
        API = 'https://www.1secmail.com/api/v1/'
        response = requests.get(API, params={'action': 'getMessages', 'login': login, 'domain': domain})
        try:
            response_json_id_ = response.json()[0]['id']
            message = requests.get(
                API, params={'action': 'readMessage', 'login': login, 'domain': domain, 'id': response_json_id_}
            )
            link = message.json()['textBody'].split('\n')[3]
            return link
        except IndexError:
            continue


def mail_check_rumbler(email, password):
    imap = imaplib.IMAP4_SSL("imap.rambler.ru", 993)
    imap.login(email, password)
    imap.select()
    typ, message_numbers = imap.search(None, 'ALL')
    for num in message_numbers[0].split()[::-1]:
        _, data = imap.fetch(num, '(RFC822)')
        raw_message = data[0][1]
        mail = mailparser.parse_from_bytes(raw_message)
        result = mail.body.split('\n')
        for line in result:
            if 'ad_features_edit' in line:
                return line


class Browser:

    def __init__(self, proxy: str = None) -> None:
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.IMAGES_PATH = config['Options']['IMAGES_PATH']
        self.ru_captcha_apikey = config['Options']['ru_captcha_apikey']
        self.astroproxy_apikey = config['Options']['astroproxy_apikey']
        self.headless = config['Options']['headless']
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        options.headless = self.headless
        self.driver = webdriver.Chrome(options=options)

    def __enter__(self):
        return self

    def __call__(self, category: str,
                 region: str,
                 title: str,
                 description: str,
                 number: str,
                 city: str, link: str = '') -> bool:
        logger.info(f'captcha: {self.rucaptcha_balance}')
        result = self.city_region_fields(category, region, city)
        if result is False:
            return result
        self.input_fields(title, description, link, number)
        result = self.captcha_input('captcha_' + city)
        if result is False:
            return result
        result = self.success_page()
        logger.info(result)
        if result is False:
            self.fail()
        return result

    @property
    def rucaptcha_balance(self):
        params = {'key': self.ru_captcha_apikey, 'action': 'getbalance'}
        try:
            req = requests.get('http://rucaptcha.com/res.php',
                               params=params)
            return req.content
        except Exception:
            return 0

    @property
    def astroproxy_balance(self):
        params = {'token': self.astroproxy_apikey}
        try:
            req = requests.get('https://astroproxy.com/api/v1/balance', params=params)
            return req.content
        except Exception:
            return 0

    @staticmethod
    def crop_captcha(location: dict, size: dict, png: bytes, file_name: str) -> str:  # fix
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        im = Image.open(BytesIO(png))
        im = im.crop((left, top, right, bottom))
        im.save(file_name)
        return file_name

    def solve_captcha(self, image_path: str) -> str:
        """
        takes captcha path as str and sends image to captcha_solver

        :param image_path:
        :return:
        """
        solver = CaptchaSolver('rucaptcha', api_key=self.ru_captcha_apikey)
        captcha_image = open(image_path, 'rb').read()
        print('solving captcha')
        try:
            captcha_answer = solver.solve_captcha(captcha_image, recognition_time=80)
            return captcha_answer
        except (CaptchaServiceError, SolutionTimeoutError):
            return ''

    @property
    def get_random_image(self) -> str:  # fix make as property
        random_image = choice([file for file in os.listdir(self.IMAGES_PATH) if file.endswith('jpg')])
        return f"{self.IMAGES_PATH}/{random_image}"

    def city_region_fields(self, category: str, region: str = '1', city: str = 'msc') -> bool:
        try:
            self.driver.get(category)
            country = '/html/body/div/div[3]/div[2]/form/div[3]/select[1]/option[2]'
            WebDriverWait(self.driver, 15).until(ec.presence_of_element_located((By.XPATH, country)),
                                                 'TimeoutException unable to locate country element xpath').click()
            if city == 'msc':
                self.driver.find_element_by_xpath(f'//*[@id="a12"]/option[4]').click()
                self.driver.find_element_by_xpath(f'//*[@id="a13"]/option[{region}]').click()
            if city == 'spb':
                self.driver.find_element_by_xpath(f'//*[@id="a12"]/option[7]').click()
            if city == 'sochi':
                self.driver.find_element_by_xpath(f'//*[@id="a12"]/option[2]').click()
                self.driver.find_element_by_xpath(f'//*[@id="a13"]/option[4]').click()
            return True
        except TimeoutException as error:
            logger.error(error)  # fix
            return False
        except Exception as error:
            logger.exception(error)  # fix
            return False

    def input_fields(self, title: str, description: str, link: str, number: str) -> bool:
        title_input = '//input[@name="title"]'
        details_textarea = '//textarea[@name="detail"]'
        phone_input = '//input[@name="pub_phone1"]'
        image_input = f'//input[@name="image_upload[0][1]"]'
        try:
            self.driver.find_element_by_xpath(title_input).send_keys(title)
            self.driver.find_element_by_xpath(details_textarea).send_keys(description + link)
            input_email = '//input[@id="email"]'
            input_email_confirm = '//input[@id="email_confirm"]'
            # self.email = str(Mailbox())
            # self.driver.find_element_by_xpath(input_email).send_keys(self.email)
            # self.driver.find_element_by_xpath(input_email_confirm).send_keys(self.email)
            self.driver.find_element_by_xpath(phone_input).send_keys('+' + number)
            self.driver.find_element_by_xpath(image_input).send_keys(self.get_random_image)
            return True
        except WebDriverException:
            logger.error('input_fields WebDriverException')
            return False
        except Exception as error:
            logger.exception(error)
            return False

    def auth(self, email, password):
        link = 'https://www.russiandoska.ru/user.php?action=user_login'
        self.driver.get(link)
        try:
            self.driver.find_element_by_name('email').send_keys(email)
            self.driver.find_element_by_name('password').send_keys(password)
            self.driver.find_element_by_xpath('//input[@value="Войти"]').click()
            return True
        except Exception as error:
            logger.exception(error)
            return False

    def captcha_input(self, captcha_name: str) -> bool:
        try:
            captcha_xpath = '//*[@id="captcha"]'
            captcha_answer_xpath = '//input[@name="image_control"]'
            element = self.driver.find_element_by_xpath(captcha_xpath)
            location = element.location_once_scrolled_into_view
            png = self.driver.get_screenshot_as_png()
            captcha_path = self.crop_captcha(location, element.size, png, f'{captcha_name}.png')
            solved_captcha = self.solve_captcha(captcha_path)
            if not solved_captcha:
                return False
            self.driver.find_element_by_xpath(captcha_answer_xpath).send_keys(solved_captcha)
            return True
        except NoSuchElementException:
            logger.error('captcha_input NoSuchElementException')
            return False
        except Exception as error:
            logger.exception(error)
            return False

    def success_page(self) -> bool:
        try:
            success_button = '//button[@name="preview"]'
            self.driver.find_element_by_xpath(success_button).click()
            sleep(1)
            assert 'Вы допустили ошибку. Исправьте ее, и попробуйте еще раз' not in self.driver.page_source
            publish_input = '//input[@value="Опубликовать"]'
            WebDriverWait(self.driver, 7).until(
                ec.presence_of_element_located((By.XPATH, publish_input)),
                'TimeoutException //input[@value="Опубликовать"]').click()
            # self.email, self.email_password = 'adudconjoitegoba@rambler.ru	1sLjVdAIps'.split('\t')  # fix
            # link = mail_check_rumbler(self.email, self.email_password)
            # self.driver.get(link)
            # requests.get(link)
            return True
        except AssertionError:
            return False
        except (TimeoutException, NoSuchElementException) as error:
            logger.error(error)
            return False
        except Exception as error:
            logger.exception(error)
            return False

    def fail(self) -> bool:
        try:
            error_info = WebDriverWait(self.driver, 2).until(
                lambda d: self.driver.find_element_by_xpath('//*[@id="wrapper"]/div[3]'),
                message='TimeoutException error info')
            print(error_info.text)
            return True
        except TimeoutException:
            return False

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.driver.quit()
