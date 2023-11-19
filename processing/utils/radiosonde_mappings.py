"""Dictionary with the nearest radiosonde station for
all radar stations in America.
"""
import logging

_radiosonde_station = {
    "KABR": "72659", "KABX": "72365", "KAKQ": "72402", "KAMA": "72363",
    "KAMX": "72202", "KAPX": "72634", "KARX": "72649", "KATX": "72797",
    "KBBX": "72489", "KBGM": "72518", "KBHX": "72597", "KBIS": "72764",
    "KBLX": "72776", "KBMX": "72230", "KBOX": "74494", "KBRO": "72250",
    "KBUF": "72528", "KBYX": "72201", "KCAE": "72208", "KCBW": "72712",
    "KCBX": "72681", "KCCX": "72520", "KCLE": "72520", "KCLX": "72208",
    "KCRI": "72357", "KCRP": "72251", "KCXX": "72518", "KCYS": "72469",
    "KDAX": "72493", "KDDC": "72451", "KDFX": "72261", "KDGX": "72235",
    "KDIX": "72501", "KDLH": "72747", "KDMX": "72558", "KDOX": "72402",
    "KDTX": "72632", "KDVN": "74455", "KDYX": "72249", "KEAX": "72456",
    "KEMX": "72274", "KENX": "72518", "KEOX": "72221", "KEPZ": "72364",
    "KESX": "72388", "KEVX": "72221", "KEWX": "72251", "KEYX": "72381",
    "KFCX": "72318", "KFDR": "72357", "KFDX": "72363", "KFFC": "72215",
    "KFSD": "72659", "KFSX": "72376", "KFTG": "72469", "KFWS": "72249",
    "KGGW": "72768", "KGJX": "72476", "KGLD": "72562", "KGRB": "72645",
    "KGRK": "72249", "KGRR": "72632", "KGSP": "72317", "KGWX": "72230",
    "KGYX": "74389", "KHDX": "72364", "KHGX": "72240", "KHNX": "74612",
    "KHPX": "72327", "KHTX": "72327", "KICT": "74646", "KICX": "72388",
    "KILN": "72426", "KILX": "74560", "KIND": "72426", "KINX": "74646",
    "KIWA": "72274", "KIWX": "72632", "KJAX": "72206", "KJGX": "72215",
    "KJKL": "72426", "KLBB": "72363", "KLCH": "72240", "KLIX": "72233",
    "KLNX": "72562", "KLOT": "74560", "KLRX": "72582", "KLSX": "74560",
    "KLTX": "72305", "KLVX": "72327", "KLZK": "72340", "KMAF": "72265",
    "KMAX": "72597", "KMBX": "72764", "KMHX": "72305", "KMKX": "72645",
    "KMLB": "74794", "KMOB": "72233", "KMPX": "72649", "KMQT": "72645",
    "KMRX": "72327", "KMSX": "72776", "KMTX": "72572", "KMUX": "72493",
    "KMVX": "72659", "KMXX": "72230", "KNKX": "72293", "KNQA": "72340",
    "KOAX": "72558", "KOHX": "72327", "KOKX": "72501", "KOTX": "72786",
    "KPAH": "72327", "KPBZ": "72520", "KPDT": "72786", "KPOE": "72240",
    "KPUX": "72469", "KRAX": "72317", "KRGX": "72489", "KRIW": "72672",
    "KRLX": "72318", "KRTX": "72694", "KSFX": "72572", "KSGF": "72440",
    "KSHV": "72248", "KSJT": "72265", "KSOX": "72293", "KSRX": "72340",
    "KTBW": "72210", "KTFX": "72776", "KTLH": "72214", "KTLX": "72357",
    "KTWX": "72456", "KTYX": "72518", "KUDX": "72662", "KUEX": "72558",
    "KVAX": "72206", "KVBX": "72393", "KVNX": "74646", "KVTX": "72381",
    "KVWX": "72327", "KYUX": "74004", "PACG": "70398", "PAEC": "70200",
    "PAHG": "70273", "PAIH": "70273", "PAKC": "70326", "PAPD": "70261",
    "PGUA": "70414", "PHKI": "91165", "PHKM": "91285", "PHMO": "91165",
    "PHWA": "91285", "TJUA": "72202", "KLWX": "72403", "PABC": "70219"
}


def get_station(radar_station):
    radar_station = radar_station.upper()
    try:
        if radar_station in _radiosonde_station.keys():
            return _radiosonde_station[radar_station]
        else:
            raise ValueError("Unknown nexrad station")
    except Exception as e:
        logging.error("Error occurred while mapping nexrad station. {}", e)
    return None
