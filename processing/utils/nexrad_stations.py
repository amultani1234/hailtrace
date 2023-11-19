"""List of all NEXRAD stations in the continential US
This file is a placeholder of functionality which will be needed
once the scheduler is in place.
"""
import logging

_radar_stations = [
    "KABR", "KABX", "KAKQ", "KAMA", "KAMX", "KAPX", "KARX", "KATX", "KBBX",
    "KBGM", "KBHX", "KBIS", "KBLX", "KBMX", "KBOX", "KBRO", "KBUF", "KBYX",
    "KCAE", "KCBW", "KCBX", "KCCX", "KCLE", "KCLX", "KCRI", "KCRP", "KCXX",
    "KCYS", "KDAX", "KDDC", "KDFX", "KDGX", "KDIX", "KDLH", "KDMX", "KDOX",
    "KDTX", "KDVN", "KDYX", "KEAX", "KEMX", "KENX", "KEOX", "KEPZ", "KESX",
    "KEVX", "KEWX", "KEYX", "KFCX", "KFDR", "KFDX", "KFFC", "KFSD", "KFSX",
    "KFTG", "KFWS", "KGGW", "KGJX", "KGLD", "KGRB", "KGRK", "KGRR", "KGSP",
    "KGWX", "KGYX", "KHDX", "KHGX", "KHNX", "KHPX", "KHTX", "KICT", "KICX",
    "KILN", "KILX", "KIND", "KINX", "KIWA", "KIWX", "KJAX", "KJGX", "KJKL",
    "KLBB", "KLCH", "KLIX", "KLNX", "KLOT", "KLRX", "KLSX", "KLTX", "KLVX",
    "KLZK", "KMAF", "KMAX", "KMBX", "KMHX", "KMKX", "KMLB", "KMOB", "KMPX",
    "KMQT", "KMRX", "KMSX", "KMTX", "KMUX", "KMVX", "KMXX", "KNKX", "KNQA",
    "KOAX", "KOHX", "KOKX", "KOTX", "KPAH", "KPBZ", "KPDT", "KPOE", "KPUX",
    "KRAX", "KRGX", "KRIW", "KRLX", "KRTX", "KSFX", "KSGF", "KSHV", "KSJT",
    "KSOX", "KSRX", "KTBW", "KTFX", "KTLH", "KTLX", "KTWX", "KTYX", "KUDX",
    "KUEX", "KVAX", "KVBX", "KVNX", "KVTX", "KVWX", "KYUX", "PACG", "PAEC",
    "PAHG", "PAIH", "PAKC", "PAPD", "PGUA", "PHKI", "PHKM", "PHMO", "PHWA",
    "TJUA", "KLWX", "PABC"
]


def is_station(station):
    """Validate existence of station in radar stations above.
    return True if exists
    return False otherwise.
    """
    station = station.upper()
    is_valid = station in _radar_stations
    if not is_valid:
        logging.warning('station %s not found in nexrad sites', station)
    return is_valid
