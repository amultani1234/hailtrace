"""Scheduler to periodically trigger the data class
to retrive and process all NEXRAD files from all stations
for the last 24hours"""
import logging
import traceback

from time import sleep
from datetime import datetime, date, time

import schedule

from processing.data import Data

CONFIG_CALC_HSDA = False
TRIGGER_TIME = "07:00"

logging.basicConfig(level=logging.INFO)

def process_radar():
    """Process all radar scans for the entire day"""
    logging.info("Running job process_radar")
    try:
        dt_time = time.fromisoformat('00:00:00.000000')
        start_time = datetime.combine(date.today(), dt_time.min)
        end_time = datetime.combine(date.today(), dt_time.max)
        _ = Data(start_time, end_time, HSDA=CONFIG_CALC_HSDA)
    except:
        logging.error(traceback.format_exc())
        logging.info("Job process_radar completed with error(s)")
    else:
        logging.info("Job process_radar completed successfully")


schedule.every().day.at(TRIGGER_TIME).do(process_radar)

while True:
    schedule.run_pending()
    sleep(500)
