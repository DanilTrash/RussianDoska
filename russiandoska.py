import itertools
from time import sleep

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from logger import logger
from data import Data
from baseclass import BaseClass


class Russiandoska(BaseClass):
    LOGGER = logger('Russiandoska')

    def city_region_fields(self, category: str, region: str, city: str = 'Moscow') -> bool:
        try:
            self.driver.get(category)
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
            return True
        except TimeoutException as error:
            self.LOGGER.error(error)
            return False
        except Exception as error:
            self.LOGGER.exception(error)
            return False

    def input_fields(self, title: str, description: str, number: str) -> bool:
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
            image_input = f'//input[@name="image_upload[0][1]"]'
            self.driver.find_element_by_xpath(image_input).send_keys(self.get_random_image())
            return True
        except WebDriverException:
            self.LOGGER.error('input_fields WebDriverException')
            return False
        except Exception as error:
            self.LOGGER.exception(error)
            return False

    def captcha_input(self) -> bool:
        try:
            captcha_xpath = '//*[@id="captcha"]'
            element = self.driver.find_element_by_xpath(captcha_xpath)
            location = element.location_once_scrolled_into_view
            png = self.driver.get_screenshot_as_png()
            captcha_answer_xpath = '//input[@name="image_control"]'
            solved_captcha = self.solve_captcha(location, element.size, png, f'captcha_{self.position}.png')
            if not solved_captcha:
                return False
            self.driver.find_element_by_xpath(captcha_answer_xpath).send_keys(solved_captcha)
            return True
        except NoSuchElementException:
            self.LOGGER.error('captcha_input NoSuchElementException')
            return False
        except Exception as error:
            self.LOGGER.exception(error)
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
            self.check_mail(self.email)
            return True
        except AssertionError:
            return False
        except (TimeoutException, NoSuchElementException) as error:
            self.LOGGER.error(error)
            return False
        except Exception as error:
            self.LOGGER.exception(error)
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

    def spam(self, category, region, title, description, number) -> bool:
        print(f'captcha: {self.rucaptcha_balance} astroproxy: {self.astroproxy_balance}')
        result = self.city_region_fields(category, region, city='Moscow') == 'TimeoutException'
        if result is not True:
            return result
        self.input_fields(title, description, number)
        result = self.captcha_input()
        if result is not True:
            return result
        result = self.success_page()
        self.LOGGER.info(result)
        if not result:
            self.fail()
        return result


def main(position: int, threads: int) -> None:
    headless = True
    titles = itertools.cycle(Data('titles', position, threads))
    details = itertools.cycle(Data('details', position, threads))
    proxy = Data('proxy', position)
    categories = itertools.cycle(Data('category', position))
    regions = itertools.cycle(Data('region'))
    numbers = itertools.cycle(Data('number'))
    while True:
        doska = Russiandoska(headless_input=headless, proxy=next(proxy), position=position)
        for category in categories:
            for region in regions:
                for number in numbers:
                    doska.spam(category, region, next(titles), next(details), number)
        doska.tearddown()


if __name__ == '__main__':
    from threading import Thread
    threads = 1
    threads_list = []
    for i in range(threads):
        thread = Thread(target=main, args=(i, threads))
        threads_list.append(thread)
        thread.start()
    for th in threads_list:
        th.join()
