'''
All test scripts will be run from this file.
Scripts themselves will be in subfolder /scripts/, and calls to functions will be done ffrom this file
Tester can comment out or uncomment tests as desired to test only the
requested functionalities
'''
import random
import pytest

import pyart

from datetime import datetime, timedelta

''' NEXRAD and Radiosonde Stations Lists '''
from processing.utils.nexrad_stations import _radar_stations as station_list
from processing.utils.radiosonde_mappings import _radiosonde_station as _stations

''' Downloaders and Data Resources '''
from processing.downloaders.nexrad_downloader import RadarDownloader
from processing.downloaders.sonde_downloader import SondeDownloader
from processing.utils.srtm.srtm import srtm

''' Algorithms '''
from processing.algorithms.hdr import HailDifferentialReflectivity
from processing.algorithms.mehs import MaximumExpectedHailSize
from processing.algorithms.hsda import main as hsda



''' Test Configuration '''
NEXRAD_DOWNLOADER_TESTS = True
HAIL_DIFFERENTIAL_REFLECTIVITY_TESTS = True
MAXIMUM_EXPECTED_HAIL_SIZE_TESTS = True
HAIL_SIZE_DISCRIMINATION_ALGORITHM_TESTS = True


''' NEXRAD Downloader Tests '''
if NEXRAD_DOWNLOADER_TESTS:
    print("Beginning Unit Test Subpackage: NEXRAD_DOWNLOADER_TESTS")

    def downloader_initialization_with_single_station_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        assert(isinstance(downloader, RadarDownloader))
        assert(downloader._scans)
        assert(downloader._radars)
        downloader._clean_downloads()
        print("Test \'downloader_initialization_with_single_station_success\' Passed Assertions")

    def downloader_initialization_with_several_stations_success():
        # First Generate a random list of a random number of nexrad stations
        # greater than 2
        random_num = random.randrange(
            2, (5 if len(station_list) > 5 else len(station_list)))
        stations = []
        for num in range(random_num):
            stations.append(random.choice(station_list))

        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader(stations, start, end)

        assert(isinstance(downloader, RadarDownloader))
        assert(downloader._scans)
        assert(downloader._radars)
        downloader._clean_downloads()
        print("Test \'downloader_initialization_with_several_stations_success\' Passed Assertions")

    def downloading_files_from_nexrad_success():
        import os
        path = os.path.join(os.getcwd(), '.data')
        dir = os.listdir(path)
        o_len = len(dir)

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        dir = os.listdir(path)
        new_len = len(dir)

        assert(new_len == o_len + len(downloader._scans))

        downloader._clean_downloads()

        print("Test \'downloading_files_from_nexrad_success\' Passed Assertions")

    def nexrad_downloader_set_new_date_range_success():
        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        start_temp, end_temp = downloader._start_date, downloader._end_date

        start = start - timedelta(days=3, hours=2, minutes=1)
        end = start + timedelta(hours=1)
        downloader.set_date_range(start, end)

        assert(downloader._start_date == start)
        assert(downloader._end_date == end)

        print("Test \'nexrad_downloader_set_new_date_range_success\' Passed Assertions")

    def nexrad_downloader_set_new_station_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        new_station = random.choice(station_list)
        # This ensures the new station is not the same as the original station,
        # just in case the random function returns the same seed.
        while (new_station == station):
            new_station = random.choice(station_list)

        downloader.set_stations((new_station,))

        assert(downloader._stations == (new_station,))

        print("Test \'nexrad_downloader_set_new_station_success\' Passed Assertions")

    def nexrad_downloader_retrieve_radar_object():
        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        radar = downloader.get_radar()

        assert(isinstance(radar, pyart.core.radar.Radar))

        print("Test \'nexrad_downloader_retrieve_radar_object\' Passed Assertions")

    def nexrad_downloader_get_radar_file_count_success():
        random_num = random.randrange(
            2, (5 if len(station_list) > 5 else len(station_list)))
        stations = []
        for num in range(random_num):
            stations.append(random.choice(station_list))

        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader(stations, start, end)

        assert(isinstance(downloader.get_count(), int))
        assert(downloader.get_count() > 0)
        downloader._clean_downloads

        print("Test \'nexrad_downloader_get_radar_file_count_success\' Passed Assertions")

    def nexrad_downloader_get_collection_time_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        assert(isinstance(downloader.get_collection_time(0), datetime))

        print("Test \'nexrad_downloader_get_collection_time_success\' Passed Assertions")

    def nexrad_downloader_get_radar_station_id_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station

        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        assert(isinstance(downloader.get_radar_id(0), str))
        assert(downloader.get_radar_id(0) in station_list)

        print("Test \'nexrad_downloader_get_radar_station_id_success\' Passed Assertions")

    def nexrad_downloader_retrieve_metadata_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station

        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        assert(isinstance(downloader.get_metadata(0), dict))
        assert(isinstance(downloader.get_metadata(
            0)['collectiontime'], datetime))
        assert(isinstance(downloader.get_metadata(0)['station'], str))
        assert(downloader.get_metadata(0)['station'] in station_list)

        print("Test \'nexrad_downloader_retrieve_metadata_success\' Passed Assertions")

    def nexrad_downloader_clean_download_folder_success():
        import os

        station = random.choice(station_list)  # Chooses random NEXRAD station

        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        path = os.path.join(os.getcwd(), '.data')
        dir = os.listdir(path)

        assert(len(dir) > 0)

        downloader._clean_downloads()

        with pytest.raises(FileNotFoundError) as test:
            os.listdir(path)
        assert test.type is FileNotFoundError

        print("Test \'nexrad_downloader_clean_download_folder_success\' Passed Assertions")

    downloader_initialization_with_single_station_success()
    downloader_initialization_with_several_stations_success()
    downloading_files_from_nexrad_success()
    nexrad_downloader_set_new_date_range_success()
    nexrad_downloader_set_new_station_success()
    nexrad_downloader_retrieve_radar_object()
    nexrad_downloader_get_radar_file_count_success()
    nexrad_downloader_get_collection_time_success()
    nexrad_downloader_get_radar_station_id_success()
    nexrad_downloader_retrieve_metadata_success()
    nexrad_downloader_clean_download_folder_success()

if HAIL_DIFFERENTIAL_REFLECTIVITY_TESTS:
    print("Beginning Unit Test Subpackage: HAIL_DIFFERENTIAL_REFLECTIVITY_TESTS")

    def HDR_object_initialization_with_default_parameters_success():

        hdr = HailDifferentialReflectivity()

        assert(isinstance(hdr, HailDifferentialReflectivity))

        print("Test \'HDR_object_initialization_with_default_parameters_success\' Passed Assertions")

    def HDR_object_initialization_with_nondefault_radars_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        radar = downloader.get_radar(0)

        hdr = HailDifferentialReflectivity(radar)

        assert(isinstance(hdr, HailDifferentialReflectivity))
        assert(hdr._radar.fields['HDR'])

        print("Test \'HDR_object_initialization_with_nondefault_radars_success\' Passed Assertions")

    def HDR_object_apply_algorithm_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        radar = downloader.get_radar(0)

        hdr = HailDifferentialReflectivity()

        hdr.set_radar(radar)
        hdr._radar.fields.pop('HDR')
        hdr._apply()

        assert(isinstance(hdr, HailDifferentialReflectivity))
        assert(hdr._radar.fields['HDR'])

        print("Test \'HDR_object_apply_algorithm_success\' Passed Assertions")

    def HDR_object_set_radars_success():
        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        radar = downloader.get_radar(0)

        hdr = HailDifferentialReflectivity()
        assert(hdr._radar is None)

        hdr.set_radar(radar)

        assert(hdr._radar)

        print("Test \'HDR_object_set_radars_success\' Passed Assertions")

    def HDR_object_retrieve_processed_radar_success():

        station = random.choice(station_list)  # Chooses random NEXRAD station
        start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                           seconds=0)  # Set as current time minus 24 hours
        end = start + timedelta(minutes=30)

        downloader = RadarDownloader((station,), start, end)

        radar = downloader.get_radar(0)

        hdr = HailDifferentialReflectivity(radar)
        new_radar = hdr.get_radar()

        assert(isinstance(new_radar, pyart.core.radar.Radar))

        print("Test \'HDR_object_retrieve_processed_radar_success\' Passed Assertions")

    HDR_object_initialization_with_default_parameters_success()
    HDR_object_initialization_with_nondefault_radars_success()
    HDR_object_apply_algorithm_success()
    HDR_object_set_radars_success()
    HDR_object_retrieve_processed_radar_success()

if MAXIMUM_EXPECTED_HAIL_SIZE_TESTS:
    print("Beginning Unit Test Subpackage: MAXIMUM_EXPECTED_HAIL_SIZE_TESTS")

    station = random.choice(station_list)  # Chooses random NEXRAD station
    start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                       seconds=0)  # Set as current time minus 24 hours
    end = start + timedelta(minutes=30)

    downloader = RadarDownloader((station,), start, end)

    radar = downloader.get_radar(0)

    usmo = int(_stations[station.upper()])
    sonde_downloader = SondeDownloader(start)
    all_sondes = sonde_downloader.get_data()
    sondes = all_sondes[usmo][list(all_sondes[usmo].keys())[0]]
    alts = sondes[1]

    def MESH_initialization_with_correct_inputs_success():
        mesh = MaximumExpectedHailSize(radar, alts)

        assert(isinstance(mesh, MaximumExpectedHailSize))
        assert(mesh._grid.fields['MESH'])

        print("Test \'MESH_initialization_with_correct_inputs_success\' Passed Assertions")

    def MESH_initialization_with_no_radar_inputs_failure():

        with pytest.raises(AttributeError) as test:
            mesh = MaximumExpectedHailSize(None, alts)
        assert test.type is AttributeError

        print("Test \'MESH_initialization_with_no_radar_inputs_failure\' Passed Assertions")

    def MESH_initialization_with_no_temps_input_failure():

        with pytest.raises(TypeError) as test:
            mesh = MaximumExpectedHailSize(radar, None)

        assert test.type is TypeError

        print("Test \'MESH_initialization_with_no_temps_input_failure\' Passed Assertions")

    def MESH_gridify_radar_success():

        mesh = MaximumExpectedHailSize(radar, alts)
        mesh._grid = None
        assert(mesh._grid is None)

        mesh._grid = mesh.gridify(radar)
        assert(mesh._grid)

        print("Test \'MESH_gridify_radar_success\' Passed Assertions")

    def MESH_apply_algorithm_success():

        mesh = MaximumExpectedHailSize(radar, alts)

        assert(mesh._grid.fields['MESH'])

        mesh._grid.fields.pop('MESH')

        mesh._apply()
        assert(mesh._grid.fields['MESH'])

        print("Test \'MESH_apply_algorithm_success\' Passed Assertions")

    def MESH_retrieve_grid_success():

        mesh = MaximumExpectedHailSize(radar, alts)

        grid = mesh.get_grid()

        assert(isinstance(grid, pyart.core.grid.Grid))

        print("Test \'MESH_retrieve_grid_success\' Passed Assertions")

    MESH_initialization_with_correct_inputs_success()
    MESH_initialization_with_no_radar_inputs_failure()
    MESH_initialization_with_no_temps_input_failure()
    MESH_gridify_radar_success()
    MESH_apply_algorithm_success()
    MESH_retrieve_grid_success()

if HAIL_SIZE_DISCRIMINATION_ALGORITHM_TESTS:
    print("Beginning Unit Test Subpackage: HAIL_SIZE_DISCRIMINATION_ALGORITHM_TESTS")

    # random.choice(station_list)  ## Chooses random NEXRAD station
    station = 'KOHX'
    start = datetime.now() - timedelta(days=0, hours=24, minutes=0,
                                       seconds=0)  # Set as current time minus 24 hours
    end = start + timedelta(minutes=30)

    downloader = RadarDownloader((station,), start, end)

    radar = downloader.get_radar(0)

    usmo = int(_stations[station.upper()])
    sonde_downloader = SondeDownloader(start)
    all_sondes = sonde_downloader.get_data()
    sondes = all_sondes[usmo][list(all_sondes[usmo].keys())[0]][0]

    srtm_file = srtm(station)

    gatefilter = pyart.filters.GateFilter(radar)
    gatefilter.exclude_transition()
    gatefilter.exclude_masked("reflectivity")

    def HSDA_run_main_with_correct_inputs_success():
        hsda_meta = hsda(radar, sondes, gatefilter, srtm_file)

        assert(isinstance(hsda_meta, dict))
        assert(hsda_meta['standard_name'] == 'Hydrometeor_ID_HSDA')

        print("Test \'HSDA_run_main_with_correct_inputs_success\' Passed Assertions")

    def HSDA_run_main_with_missing_inputs_failure():

        with pytest.raises(AttributeError) as error:
            hsda_meta = hsda(None, sondes, gatefilter, srtm_file)
        assert(error.type is AttributeError)

        with pytest.raises(TypeError) as error:
            hsda_meta = hsda(radar, None, gatefilter, srtm_file)
        assert(error.type is TypeError)

        with pytest.raises(AttributeError) as error:
            hsda_meta = hsda(radar, sondes, None, srtm_file)
        assert(error.type is AttributeError)

        print("Test HSDA_run_main_with_missing_inputs_failure\' Passed Assertions")

    HSDA_run_main_with_correct_inputs_success()
    HSDA_run_main_with_missing_inputs_failure()
