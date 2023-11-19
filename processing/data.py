'''@class Data
The class file for the Data class
For the Hailtrace processing in Python
'''
import logging
import os
import pickle
import time
from datetime import datetime, timedelta

import pyart.map.grid_mapper

''' NEXRAD and Radiosonde Stations Lists '''
from processing.utils.nexrad_stations import _radar_stations as radar_stations
from processing.utils.radiosonde_mappings import _radiosonde_station as _stations

''' Downloaders and Data References '''
from processing.downloaders.nexrad_downloader import RadarDownloader
from processing.downloaders.sonde_downloader import SondeDownloader
from processing.utils.srtm.srtm import srtm

''' Algorithms '''
from processing.algorithms.hdr import HailDifferentialReflectivity
from processing.algorithms.hsda import main as hsda_main
from processing.algorithms.mehs import MaximumExpectedHailSize

''' Conversion and Exporting Utilities '''
from processing.utils.geojson_converter import GeoJSONConverter
import processing.db.db_connection as db


class Data:
    '''
    For initialization, this class will default to downloading and processing data for most recent 10-minute period.
    This time period can be modified for automated processing by altering the default parameters in the __init__
    function. If running manually, just set start and end dates to desired date time in a proper date time format.
    If running from a separate script, use "from datetime import datetime, timedelta" to set appropriate format.
    If an invalid format is passed, class will default to the parameters established in __init__
    '''

    def __init__(self, start_date, end_date=None, stations=None, HSDA=False):
        # Init Date Range
        self._start_date = start_date
        self._end_date = end_date
        if self._end_date is None:
            logging.warning("No end date provided, defaulting to 1 day range")
            self._end_date = self._start_date - timedelta(hours=24)

        # Init Station Range
        self._stations = stations
        if self._stations is None:
            self._stations = radar_stations
        self.HSDA = HSDA

        # Init downloader
        self.sonde_pickles = []  # pickle array
        time_dif = self._end_date - self._start_date
        loops = int(-(-(time_dif.total_seconds() / 3600)) // 4)
        if loops <= 0: loops = 1
        for idx in range(loops):
            sonde = SondeDownloader(self._start_date + timedelta(hours=4 * idx))
            handle = "pickle{}".format(idx)
            with open(handle, "wb") as f:
                pickle.dump(sonde.get_data(), f)
            self.sonde_pickles.append(handle)

        logging.info("Data class __init__ complete, start_date={} end_date={} stations={}".format(
            self._start_date, self._end_date, self._stations
        ))

        self._conn = db.get_connection()

        ## Loop to iterate through tine blocks, as sonde data is only valid for a few hours worth of calculations
        for station in self._stations:  ## One station at a time
            for idx in range(loops):  ## NUmber of 4 hour blocks to iterate through
                # Init downloaders
                all_sondes = None
                with open(self.sonde_pickles[idx], "rb") as f:
                    all_sondes = pickle.load(f)
                usmo = int(_stations[station.upper()])
                if (all_sondes is not None) and (usmo in all_sondes.keys()):
                    sondes = all_sondes[usmo][list(all_sondes[usmo].keys())[0]]
                else:
                    sondes = None
                start = self._start_date + timedelta(hours=(4 * idx))
                end = self._end_date + timedelta(hours=(4 * idx))
                self._radar_downloader = RadarDownloader(
                    stations=(station,),
                    start_date=start, end_date=end)

                logging.info("Data class __init__ complete, dates={}{} stations={}".format(
                    start, end, station
                ))

                self._processed_radars = []
                self._processed_grids = []

                tracker = 10  ## Number of radars to do per chunk to save heap space allowed for python
                count = 0
                for _idx, radarfile in enumerate(
                        self._radar_downloader._radars):  ## Modifying calls so RAM doesnt get killed
                    if count < tracker:
                        radar = self._radar_downloader.get_radar(_idx)
                        radar = radar.extract_sweeps([0])
                        self.proc_helper(radar, _idx, sondes)
                        count += 1
                    else:
                        self._gen_json()
                        self._processed_radars = []
                        self._processed_grids = []
                        ## Start next objs
                        radar = self._radar_downloader.get_radar(_idx)
                        self.proc_helper(radar, idx, sondes)
                        count = 1

                if (len(self._processed_grids) > 0) or (len(self._processed_radars) > 0):
                    self._gen_json()
                    self._processed_radars = []
                    self._processed_grids = []

                self._radar_downloader._clean_downloads()
                self._radar_downloader = None
                with open(self.sonde_pickles[idx], "wb") as f:
                    pickle.dump(all_sondes, f)

    def proc_helper(self, radar, idx, sondes):
        if sondes is not None:
            alts = sondes[1]
        else:
            alts = None
        radar_date = self._radar_downloader.get_collection_time(idx)
        radar_id = self._radar_downloader.get_radar_id(idx)
        
        # Apply HDR
        logging.info("applying HDR")
        radar = HailDifferentialReflectivity(radar).get_radar()
        if alts is not None:
            # Apply HSDA
            srtm_file = srtm(radar.metadata['instrument_name'])
            if self.HSDA and os.path.isfile(srtm_file):
                logging.info("applying HSDA")
                gatefilter = pyart.filters.GateFilter(radar)
                gatefilter.exclude_transition()
                gatefilter.exclude_masked("reflectivity")
                radar = self.proc_hsda(radar, gatefilter, srtm_file, sondes)
            elif self.HSDA and not os.path.isfile(srtm_file):  # intentionally redundent
                logging.warning('No srtm data found to calulate hsda, skipping calc')
            product = {
                'id': radar_id,
                'radar': radar,
                'timestamp': radar_date
            }
            self._processed_radars.append(product)
            
            # Apply MEHS
            logging.info("applying MEHS")
            
            mesh = MaximumExpectedHailSize(radar, alts)
            product = {
                'id': radar_id,
                'grid': mesh.get_grid(),
                'timestamp': radar_date
            }
            self._processed_grids.append(product)
            
            mesh, alts = None, None

    def proc_hsda(self, radar, gatefilter, srtm_file, sondes):
        ''' Method to apply HSDA to radar data '''
        hsda_meta = hsda_main(radar, sondes[0], gatefilter, srtm_file)
        radar.add_field('HCA_HSDA', hsda_meta, replace_existing=True)
        return radar

    def _gen_json_helper(self, radar, algo, collection, clevels=None):
        ''' Helper method which converts radar objects to GeoJSON then
        exports them to the db '''
        if algo == 'MESH':
            data, lats, lons = self._extract_data_lat_lon(radar['grid'], algo)
        else:
            data, lats, lons = self._extract_data_lat_lon(radar['radar'], algo)
        converter = GeoJSONConverter(
            data, lats, lons,
            algo, radar['id'], radar['timestamp'], levels=clevels)
        self._upload_product(converter, collection)

    def _gen_json(self):
        '''Converts all processed radars in self._processed_radars to
        geojson features and uploads them to the appropriate collection.'''
        ''' Prep arguments as tuples to be passed to _gen_json_helper '''
        arguments = []
        for radar in self._processed_radars:
            arguments.append((radar, 'HDR', 'algo_hdr'))
            if 'HCA_HSDA' in radar['radar'].fields.keys():
                arguments.append((radar, 'HCA_HSDA', 'algo_hsda', range(1, 14)))
        for grid in self._processed_grids:
            arguments.append((grid, 'MESH', 'algo_mehs'))
        logging.info('begin contouring')

        ''' Contour, convert, and export GeoJSONs '''
        start = time.time()
        for argument in arguments:
            logging.info(argument)
            if len(argument) > 3:
                self._gen_json_helper(argument[0], argument[1], argument[2], argument[3])
            else:
                self._gen_json_helper(argument[0], argument[1], argument[2])

        end = time.time()
        logging.info("end contouring. t={}".format(end - start))

    def _upload_product(self, converter, algo_collection):
        ''' Takes GeoJSONs from GeoJSON converter and inserts
        in to database '''
        features = converter.get_features()
        if isinstance(features, list) and len(features) > 2:
            logging.info("feature_count={}".format(len(features)))

            self._conn.hailtrace[algo_collection].insert_many(features)
            self._conn.hailtrace['log_proc_events'].insert_one(converter.get_metadata())

            logging.info('processing done for {}'.format(converter.get_relational_id()))
        else:
            logging.warning('no values to contour')

    def _extract_data_lat_lon(self, radar, algo):
        ''' Function to get the processed data and lat, lon points
        from the radar object to be used in GeoJSONConverter for contouring'''
        if algo == 'MESH':
            # radar here is actually grid, name is radar for uniformity
            radar.init_point_altitude()
            lats, lons = radar.get_point_longitude_latitude()
            data = radar.fields[algo]['data'][0]
        else:
            data = radar.get_field(0, algo, True)
            lats, lons, _ = radar.get_gate_lat_lon_alt(0, False, True)
        return data, lats, lons
