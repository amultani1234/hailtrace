"""Responsible for mapping which SRTM file
is need for each radar station which is used to calculate
corrective beam blocking for HSDA"""
import logging
import os

from processing.utils.nexrad_stations import _radar_stations

def srtm(station):
    file = os.getcwd() + "/processing/utils/srtm/{}.tif".format(station)
    if os.path.isfile(file):
        return file
    return "UNDEF"
