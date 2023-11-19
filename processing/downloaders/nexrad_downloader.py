"""@class RadarDownloader
Implementation of utility to retrieve NEXRAD files
from server for analysis
"""
import logging
import os
import queue
import shutil
import threading
from datetime import datetime, timedelta

from numpy import array_split

from processing.utils.nexrad_stations import is_station
from processing.utils.nexradaws import nexradawsinterface as nexradaws
from processing.db.db_connection import get_connection


class RadarDownloader:
    """Responsible for downloading NEXRAD radar files from a given
    radar station within a given date range

    # Arguments:
        stations: list
            list of NEXRAD stations to retrieve data from
        start_date: datetime
            datatime object specifying the start of the date range used
            to filter data being retrieved
        end_date: datetime
            datetime object specifying the end of the date range used
            to filter data being retrieved. Optional argument, will
            default to the same date as the start_date with time 23:59 UTC
    """
    MAX_THREADS = 8

    def __init__(self, stations, start_date, end_date):
        # Init date range
        self._start_date = start_date
        self._end_date = end_date
        if not isinstance(self._start_date, datetime) or not isinstance(self._end_date, datetime):
            raise ValueError("Illegal start/end date, expected objects of type datetime")
        if self._start_date > self._end_date:
            raise ValueError("Illegal date range, start date must precced end date")
        elif self._start_date == self._end_date:
            raise ValueError("Illegal date range, start and end are equal")
        if self._start_date > datetime.now():
            raise ValueError("Illegal date range, start/end cannot be in the future")

        # Init stations
        self._stations = stations
        if len(self._stations) == 0:
            raise ValueError("Illegal station specified, expected a valid NEXRAD station")
        for station in self._stations:
            if not is_station(station):
                raise ValueError("Illegal station specified, no NEXRAD station named {}".format(station))

        # Make temp dir to hold downloaded radar data
        self._tempdir = os.getcwd() + '/.data/'
        if not os.path.isdir(self._tempdir):
            os.mkdir(self._tempdir, 0o777)

        # Establish conn with NEXRAD S3 bucket
        self._conn = nexradaws.NexradAwsInterface()

        # Download all radar data for given parameters
        self._radars = []
        self._scans = self._conn.get_avail_scans_in_range(
            self._start_date, self._end_date,
            self._stations)
        if len(self._scans) != 0:
            self._download_all()
        else:
            db_conn = get_connection()
            info = {
                'station': self._stations,
                'error': "NO_SCANS"
            }
            db_conn.hailtrace['log_proc_errors'].insert_one(info)
            logging.error("No scans found for {}".format(self._stations))

    def __del__(self):
        self._clean_downloads()

    def _clean_downloads(self):
        """Since the NEXRAD files are large in size, there is no benefit
        in keeping them after data has been extracted. This function is then
        utilized to delete the folder containing those files periodically."""
        try:
            if os.path.isdir(self._tempdir):
                shutil.rmtree(self._tempdir)
        except OSError as os_except:
            logging.error('Error occurred while deleting {}. {}'.format(
                self._tempdir, os_except))

    def _download_helper(self, file_to_proc, running):
        """Downloads radars corresponding to the sublist self._scans[start:end].
        Store downloaded radar files in self._radars"""
        while True:
            try:
                scan_range = file_to_proc.get(True, 1)
                start = scan_range[0]
                end = scan_range[1] + 1
                logging.info('downloading sweeps {}-{}'.format(start, end))
                files = self._conn.download(
                    self._scans[start:end], self._tempdir)
                for file in files.success:
                    self._radars.append(file)
                logging.info("{} files failed downloading".format(
                    files.failed_count))
                logging.info("{} files successfully downloading".format(
                    files.success_count))
                file_to_proc.task_done()
            except queue.Empty:
                if not running.is_set():
                    break

    def _init_download_threads(self):
        """Spawns threads for downloading NEXRAD scans"""
        threads = []
        running = threading.Event()
        file_to_process = queue.Queue()
        running.set()
        for _ in range(1, self.MAX_THREADS):
            thread = threading.Thread(
                target=self._download_helper,
                args=(file_to_process, running)
            )
            thread.start()
            threads.append(thread)
        logging.info(
            '{} threads created for radar downloading'.format(self.MAX_THREADS))
        return threads, running, file_to_process

    def _download_all(self):
        """Downloads all radars for all scans retrieved. Generates n threads,
        then chunks total scans in to n sub lists, assigns each thread a chunk
        which is a list containing the scans the thread is to download"""
        # Filter _MDM files which we do not need
        self._scans = [
            scan for scan in self._scans if '_MDM' not in scan.filename]

        # Cases when number of scans is < MAX_THREADS
        if len(self._scans) < self.MAX_THREADS:
            self.MAX_THREADS = len(self._scans)
            print("{} used for downloading".format(self.MAX_THREADS))

        threads, running, jobs = self._init_download_threads()
        chunks = array_split(range(len(self._scans)), self.MAX_THREADS)
        for chunk in chunks:
            jobs.put((chunk[0], chunk[-1]))
        running.clear()
        for thread in threads:
            thread.join()

    def set_date_range(self, start_date, end_date):
        """Change the date range to retrieve NEXRAD data"""
        self._start_date = start_date
        self._end_date = end_date
        self._scans = self._conn.get_avail_scans_in_range(
            self._start_date, self._end_date,
            self._stations)

    def set_stations(self, radar_stations):
        """Change the station(s) to retrieve NEXRAD data"""
        self._stations = radar_stations
        self._scans = self._conn.get_avail_scans_in_range(
            self._start_date, self._end_date,
            self._stations)

    def get_radar(self, idx=0):
        """Download and decode NEXRAD scan"""
        try:
            if idx < len(self._radars):
                return self._radars[idx].open_pyart()
            # Invalid index requested
            raise ValueError("Index is out of bounds {}".format(idx))
        except ValueError as idx_exception:
            logging.error("{}".format(idx_exception))
        return None

    def get_nexrad_files(self, limit=-1):
        """Get list of NEXRAD files (optionally limit number of elements)"""
        return self._radars[:limit]

    def get_count(self):
        """Get number of NEXRAD files download and currently holding"""
        return len(self._radars)

    def get_collection_time(self, idx):
        """Get the time for when data in NEXRAD file was collected"""
        return self._radars[idx].scan_time

    def get_radar_id(self, idx):
        """Get the NEXRAD site id for a given NEXRAD file"""
        return self._radars[idx].radar_id

    def get_metadata(self, idx):
        """Get the time and NEXRAD site id for a given NEXRAD file"""
        return {
            'collectiontime': self.get_collection_time(idx),
            'station': self.get_radar_id(idx)
        }
