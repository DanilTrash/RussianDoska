from selenium.webdriver.common.keys import Keys
import itertools
from threading import Thread

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait

from baseclass import BaseClass
from data import Data
from logger import logger


class Sexlove(BaseClass):
    LOGGER = logger('sexlove', file='sexlove.log')

    def step_one(self, title, detail, contact):
        URL = 'https://sex-love24.com/adverts-create'
        self.driver.get(URL)
        try:
            WebDriverWait(self.driver, 10).until(lambda d: self.driver.find_element_by_name('AdvertsUser[title]'))
            self.driver.find_element_by_name('AdvertsUser[title]').send_keys(title)
            self.driver.find_element_by_name('AdvertsUser[text]').send_keys(detail)
            self.driver.find_element_by_name('AdvertsUser[email]').send_keys(contact)
            self.driver.find_element_by_xpath('//*[@id="select2-advertsuser-city-container"]').click()
            self.driver.find_element_by_xpath('/html/body/span/span/span[1]/input').send_keys('Москва')
            self.driver.find_element_by_xpath('/html/body/span/span/span[1]/input').send_keys(Keys.ENTER)
            return True
        except NoSuchElementException as error:
            self.LOGGER.error(error)
            return False

    def step_success(self):
        self.driver.find_element_by_xpath('//*[@id="w0"]/div/button').click()

    def spam(self, title, detail, contact):
        if self.step_one(title, detail, contact):
            self.step_success()


def main(position):
    headless = False
    titles = itertools.cycle(Data('titles'))
    details = itertools.cycle(Data('details'))
    numbers = itertools.cycle(Data('number'))
    proxy = itertools.cycle(Data('proxy'))
    while True:
        sexlove = Sexlove(headless, next(proxy), position)
        sexlove.spam(next(titles), next(details), next(numbers))


if __name__ == '__main__':
    threads = 1
    threads_list = []
    for i in range(threads):
        thread = Thread(target=main, args=(i,))
        threads_list.append(thread)
        thread.start()
    for th in threads_list:
        th.join()
