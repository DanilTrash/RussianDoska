from loguru import logger
import itertools
import argparse

from baseclass import Browser
from data import Data

logger.add('log.log')


class Client:
    def __init__(self, city):
        data = Data()
        self.city = city
        if city == 'msc':
            self.titles = itertools.cycle(data('titles').dropna().tolist()[::-1])
            self.details = itertools.cycle(data('details').dropna().tolist()[::-1])
            self.numbers = itertools.cycle(data('number').dropna().tolist())
        if city == 'spb':
            self.titles = itertools.cycle(data('titles_spb').dropna().tolist()[::-1])
            self.details = itertools.cycle(data('details_spb').dropna().tolist()[::-1])
            self.numbers = itertools.cycle(data('number_spb').dropna().tolist())
        self.proxy = itertools.cycle(data('proxy').dropna().tolist())
        self.categories = itertools.cycle(data('category').dropna().tolist())
        self.regions = itertools.cycle(data('region').dropna().tolist())
        self.email = data('email').dropna().tolist()[0]
        self.password = data('password').dropna().tolist()[0]

    def __call__(self):
        with Browser(proxy=next(self.proxy)) as doska:
            doska.auth(self.email, self.password)
            while True:
                for category in self.categories:
                    for region in self.regions:
                        for number in self.numbers:
                            title = next(self.titles)
                            detail = next(self.details)
                            doska(category, region, title, detail, number, self.city)


def main():
    try:
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument(dest='city')
        args = arg_parser.parse_args()
        client = Client(args.city)
        client()
    except Exception as error:
        logger.exception(error)


if __name__ == '__main__':
    main()
