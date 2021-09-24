from __future__ import annotations

import itertools
from time import sleep

from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, TimeoutException, \
    UnexpectedAlertPresentException
from selenium.webdriver.support.wait import WebDriverWait

import logger
from baseclass import BaseClass
from data import Data


class Rudos(BaseClass):
    LOGGER = logger.logger('rudos', file='rudos.log')

    def first_step(self, title, detail, contact):
        self.driver.get('https://rudos.ru/newadv/')
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: self.driver.find_element_by_name('name_adv'),
                'name_adv name doesn`t appeared').send_keys(title)
            self.driver.find_element_by_name('category').send_keys('Знакомства')
            self.driver.find_element_by_name('category_lvl_n[1]').send_keys('Женщина познакомится с мужчиной')
            self.driver.find_element_by_name('text_adv').send_keys(detail + '\n' + contact)
            self.driver.find_element_by_xpath('//*[@id="fileupload"]').send_keys(self.get_random_image())
            sleep(1)
            return True
        except (NoSuchElementException, TimeoutException) as error:
            self.LOGGER.error(error)
            return False

    def input_fields(self, contact, name):
        try:
            self.driver.find_element_by_name('telefon').send_keys(contact)
            self.driver.find_element_by_name('region_adv').send_keys('Московская область')
            self.driver.find_element_by_name('city_adv').send_keys('Москва')
            self.driver.find_element_by_name('email').send_keys(self.email)
            self.driver.find_element_by_name('name_user').send_keys(name)
            return True
        except Exception as error:
            self.LOGGER.error(error)
            return False

    def third_step(self):
        try:
            l = self.driver.find_element_by_id('on_check_rules_advert').location_once_scrolled_into_view
            self.driver.find_element_by_xpath('//*[@id="on_check_rules_advert"]/div').click()
            element = self.driver.find_element_by_xpath('//*[@id="captcha"]')
            location = element.location_once_scrolled_into_view
            png = self.driver.get_screenshot_as_png()
            self.driver.find_element_by_name('captcha').send_keys(self.solve_captcha(location, element.size, png,
                                                                                     'rudos_captcha.png'))
            self.driver.find_element_by_xpath('//*[@id="form_upload"]/div/div[17]/ul/li[8]').click()
            return True
        except Exception as error:
            self.LOGGER.error(error)
            return False

    def success(self):
        try:
            element = self.driver.find_element_by_xpath('//*[@id="form_upload"]/div/div[19]/div/input')
            element.click()
            WebDriverWait(self.driver, 5).until(lambda d: self.driver.find_element_by_xpath('//*[@class="success-add"]'))
            return True
        except TimeoutException as error:
            self.LOGGER.error(error)
            return False

    def spam(self, title, detail, contact, name):
        result = self.first_step(title, detail, contact)
        if result is True:
            result = self.input_fields(contact, name)
        if result is True:
            result = self.third_step()
        if result is True:
            result = self.success()
            sleep(30)
        self.LOGGER.info(result)
        return result


def main(position):
    headless = True
    titles = itertools.cycle(Data('titles'))
    details = itertools.cycle(Data('details'))
    names = itertools.cycle(Data('name'))
    while True:
        doska = Rudos(headless_input=headless, position=position)
        numbers = Data('number')
        for number in numbers:
            doska.spam(title=next(titles), detail=next(details), contact=number, name=next(names))
        doska.driver.quit()


if __name__ == '__main__':
    main(0)
