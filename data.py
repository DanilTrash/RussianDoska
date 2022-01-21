import configparser

import pandas as pd


class Data:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.dataframe = pd.read_csv(
            r'https://docs.google.com/spreadsheets/d/1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw/export?format=csv&id=1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw&gid=1789053577',
            dtype={
                'proxy': str,
                'titles': str,
                'titles_spb': str,
                'details': str,
                'details_spb': str,
                'category': str,
                'region': str,
                'number': str,
                'number_spb': str,
            }
            )

    def __call__(self, arg):
        value = self.dataframe[arg]
        return value
