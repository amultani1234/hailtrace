"""@class SondeDownloader
Implementation of utility to retrieve radiosonde files
from server for analysis.
"""
import logging
import os
import pickle
import shutil

from datetime import datetime, timedelta

import swifter
import numpy as np
import pandas as pd

from requests_html import HTMLSession

from processing.utils.radiosonde_mappings import _radiosonde_station as stations

months = {
    'JAN': 1,
    'FEB': 2,
    'MAR': 3,
    'APR': 4,
    'MAY': 5,
    'JUN': 6,
    'JUL': 7,
    'AUG': 8,
    'SEP': 9,
    'OCT': 10,
    'NOV': 11,
    'DEC': 12
}


class SondeDownloader:
    """Class responsible for retrieving radio sonde data, utilized
    in the calculation of MEHS and HSDA.

    # Arguments:
        date: the date from which to retrieve radiosonde data from
    """
    _CRITICAL_TEMP = 647.096  # Kelvins
    _CRITICAL_PRESSURE = 220640  # hPascals
    _COEFFICIENTS = [-7.85951783, 1.84408259, -11.7866497, 22.6807411, -15.9618719, 1.80122502]
    _REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362"
    }

    def __init__(self, date):
        """Make time range for getting radio sonde data"""
        self._date = date - timedelta(hours=8)
        self._enddate = date + timedelta(hours=8)

        self._tempdir = os.getcwd() + '/.sonde/'
        if not os.path.isdir(self._tempdir):
            os.mkdir(self._tempdir, 0o777)

        """Keep stored in pickled file to save RAM except when needed"""
        self.handle = self._tempdir + self._date.strftime('%m%d%Y%H%M') + ".p"
        if not os.path.exists(self.handle):
            self.sondes = self.getsondes(self._date)
            with open(self.handle, "wb") as f:
                pickle.dump(self.sondes, f)
        self.sondes = None

    def __del__(self):
        self._clean_downloads()

    def _clean_downloads(self):
        """Since the NEXRAD files are large in size, there is no benefit
        in keeping them after data has been extracted, so delete them"""
        try:
            if os.path.isdir(self._tempdir):
                shutil.rmtree(self._tempdir)
        except Exception as e:
            logging.error('Error occurred while deleting {}. {}'.format(self._tempdir, e))

    def getsondes(self, _date):
        """Make request to get and then parse radiosonde data"""
        """Make request"""
        access = "+".join(stations.values())
        url = \
            'https://ruc.noaa.gov/raobs/GetRaobs.cgi?' + \
            'shour=All+Times&ltype=All+Levels&wunits=Tenths+of+Meters%2FSecond&' + \
            'bdate=' + self._date.strftime("%Y%m%d%H") + \
            '&edate=' + self._enddate.strftime("%Y%m%d%H") + \
            '&access=' + access + \
            "osort%3DStation+Series+Sort&osort=Station+Series+Sort&oformat=FSL+format+%28ASCII+text%29"
        session = HTMLSession()
        response = session.get(url, headers=self._REQUEST_HEADERS)

        """Parse data"""
        lines = response.text.split("\n")
        array = []
        for item in lines:
            array.append([self.helper(chunk) for chunk in item.split(" ") if chunk not in " "])
        sondes = {}

        if array[-1] == []:
            del array[-1]

        start = None
        status = 0
        for idx, row in enumerate(array):
            if (array[idx][0] == 254) & (status == 0):
                start = idx
                status = 1
            elif array[idx][0] == 254:
                self.push_dict(sondes, array[start:idx])
                start = idx
            elif idx == (len(array) - 1):
                self.push_dict(sondes, array[start:idx + 1])
                break
            else:
                continue

        return sondes

    def helper(self, chunk):
        """TODO: add docstring"""
        if chunk == '99999':
            return np.nan
        nums = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-')
        str = False
        for char in chunk:
            if char not in nums:
                str = True
        if str:
            return chunk
        else:
            return int(chunk)

    def relative_humidity(self, temp, dewpt):
        """Calculate relative humidity, which is the ratio of water vapour pressure (P_W) to
        the saturation water vapour pressure (over water) at the gas temp"""
        return self.pws(dewpt) / self.pws(temp)

    def pws(self, T):
        """Calculates water vapour pressure

        Reference https://www.vaisala.com/en/system/files?file=documents/Humidity_Conversion_Formulas_B210973EN.pdf
        """
        if T < 0:
            A = 6.114742
            m = 9.778707
            Tn = 273.1466
        else:
            A = 6.089613
            m = 7.33502
            Tn = 230.3921
        return (A * pow(10, ((m * T) / (T + Tn))))

    def push_dict(self, dict, array):
        """TODO: add docstring"""
        if array[0][0] != 254 or array[1][0] != 1 or array[2][0] != 2 or array[3][0] != 3:
            logging.error(
                "Invalid Sonde File Format. Review Sonde Input Specifications at:\nhttps://ruc.noaa.gov/raobs/fsl_format-new.html\nCode may need adjustment in sonde.py if format has changed.")
            return
        station = array[1][2]
        if str(station) not in stations.values():
            return
        temp = array[0][1:5]
        hour, day, month, year = int(temp[0]), int(temp[1]), months[temp[2]], int(temp[3])
        date = datetime(year, month, day, hour)
        df = pd.DataFrame(columns=['pressure', 'height', 'temperature', 'dewpt', 'wind_dir', 'wind_spd'])
        for idx, row in enumerate(array):
            if idx < 4:
                continue
            df.loc()[idx - 4] = row[1:]
        df[df == 99999] = np.nan
        df['temperature'] = df.swifter.apply(lambda x: x['temperature'] / 10.0, axis=1)
        df['dewpt'] = df.swifter.apply(lambda x: x['dewpt'] / 10.0, axis=1)
        df['rh'] = df.swifter.apply(lambda x: self.relative_humidity(x['temperature'], x['dewpt']), axis=1)

        df.station = station
        df.date = date
        alt1 = self._extract_wbt(df[['height', 'temperature']].dropna(), 0)
        alt2 = self._extract_wbt(df[['height', 'temperature']].dropna(), -20)
        if (alt1 is None) or (alt2 is None):
            dict[station] = {date: (df, (None))}
        else:
            dict[station] = {date: (df, (alt1, alt2))}

    @staticmethod
    def _extract_wbt(df, target):
        """
        This function finds the altitudes at which the air temperature changes to 0C and -20C.
        As it is unlikely for the transition to be exactly at an altitude contained in the sonde
        array, this function interpolates the approximate altitude from the transitions above and below
        the desired temperatures.

        :return alt_below - (ratio * alt_dif)
        """
        temp_above, temp_below, alt_above, alt_below = 0, 0, 0, 0

        arr = np.asarray(df)
        if np.shape(arr)[0] == 0:
            return None

        for i in range(len(arr)):
            if arr[i, 1] <= target:
                if i == 0:
                    alt = arr[i, 0]
                else:
                    temp_above = arr[i - 1, 1]
                    temp_below = arr[i, 1]
                    alt_above = arr[i - 1, 0]
                    alt_below = arr[i, 0]
                    ratio = (target - temp_below) / (temp_above - temp_below)
                    alt_dif = alt_below - alt_above
                    alt = alt_below - (ratio * alt_dif)
                break
        if arr[-1, 1] > target:
            alt = None
        return alt

    def get_data(self):
        with open(self.handle, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def get_altitudes(sondes, station):
        if sondes[1]is not None:
            return sondes[1]
        else:
            return None
