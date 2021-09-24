from collections.abc import Iterator

import numpy as np
import pandas as pd


class Data(Iterator):
    GOLOGIN_APIKEY = (
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MTQwODg1MDM2MzkxOGU1YjdlNWFiNWIiL'
        'CJ0eXBlIjoiZGV2Iiwiand0aWQiOiI2MTQwODhiODY4Y2E1Njc5NGEwZGNjNWEifQ.eVVNLIeuvRJ-Z'
        'PotsEuZtNAzNd39SB9HdBwa1CqqHdo'
    )
    dataframe = pd.read_csv('https://docs.google.com/spreadsheets/d/1zaxjdu'
                            '9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw/export?'
                            'format=csv&'
                            'id=1zaxjdu9ESYy2MCNuDow0_5PnZpwEsyrdTQ_kk0PMZbw&'
                            'gid=1789053577', dtype={'number': str, 'region': str})

    def __init__(self, argument: str, position: int = 0, threads: int = 1, step_over: int = 0) -> None:
        if threads > 1:
            self._collection = np.array_split(self.dataframe[argument].dropna().tolist(), threads)[position]
        else:
            self._collection = self.dataframe[argument].dropna().tolist()
        self.position = position + step_over

    def __next__(self) -> str:
        try:
            value = self._collection[self.position]
            self.position -= 1
            return value
        except IndexError:
            raise StopIteration
