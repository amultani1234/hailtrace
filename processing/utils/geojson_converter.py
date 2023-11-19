"""@class GeoJSONConverter
This class is responsible for taking a radar object, and creating
a GeoJSON file which holds spatial information corresponding to a field
of data in the radar (i.e. hail_differential_reflectivity).

Works by extracting the field values, latitudes and longitudes, creating a
surface mesh of those points, applying the correct color to each cell of the
surface mesh based on the field value at that given point, and then finally
putting the spatial information of the cells and the colors in a GeoJSON
FeatureCollection.
"""
import logging
import queue
import threading

import matplotlib.pyplot as plt
import numpy as np

from geojson import Polygon, Feature
from matplotlib.colors import rgb2hex
from scipy.ndimage.filters import gaussian_filter


class GeoJSONConverter:
    """Class to help convert from radar object with hail size
    information to geojson object which can be plotted on the maps in
    the user interface
    """
    _NUM_THREADS = 15

    def __init__(self, data, lats, lons, algorithm, station, date, levels=None):
        self._data = data
        self._lats = lats
        self._lons = lons

        """Check dimensions of data so the contours line up"""
        if self._lats.shape[0] != self._data.shape[0]:
            self._data = self._data[:self._lats.shape[0]]

        if levels is not None:
            self._contour_levels = levels
        else:
            self._contour_levels = []

        self._features = []
        self._contours = None
        self._data_mappings = {}

        """Initialize metadata"""
        self._date = date
        self._station = station
        self._algorithm = algorithm

        """Attributes to uniquely identify a hail reading in database"""
        self._id = None
        self._id_doc = None

        """Call sequence of methods to generate GeoJSON information"""
        self._pre_process()
        self._set_id()

        if self._contour_levels[0] == self._contour_levels[-1]:
            self._features = [-1]
        else:
            self._find_contours()
            self._gen_feature_collection()
            self._set_doc_id()

    def _pre_process(self):
        """Prepare the hail and spatial data for contouring.

        Converts data in to np.array filling in the masked fields,
        and apply a gaussian filter to reduce the radar noise. Splits
        the range of the data in to 20 bins which mark where the contour
        lines will be, in terms of the data value being split.
        """
        if len(self._contour_levels) == 0:
            self._contour_levels = np.linspace(self._data.min(), self._data.max(), 5)
        self._data = np.ma.filled(self._data, 9999)
        self._data = gaussian_filter(self._data, sigma=2)

    def _find_contours(self):
        """Find contours given the hail and spatial data.

        Works by making a surface mesh using Delaunay triangulation and
        assigning fill value at each cell corresponding to field value,
        which results in visible contours of values divided in to n regions.
        """
        try:
            """Find contours using the datapoints and grid surface"""
            self._contours = plt.contourf(
                self._lats, self._lons, self._data,
                levels=self._contour_levels,
                vmin=min(self._contour_levels), vmax=max(self._contour_levels)
            )
            """Assign contour value to each color for legend in ui"""
            colors = [collection.get_facecolor() for collection in self._contours.collections]
            for color_idx in enumerate(colors):
                color = color_idx[1][0]
                if not isinstance(color, str):
                    color = rgb2hex(color)
                self._data_mappings[color] = self._contour_levels[color_idx[0]]
        except Exception as e:
            """Set features to -1 as a flag that contours where not
            able to be found"""
            logging.warning("No contours found in data")
            self._features = [-1]

    def _init_featureproc_threads(self):
        threads = []
        running = threading.Event()
        to_proc = queue.Queue()
        running.set()
        for i in range(1, self._NUM_THREADS):
            thread = threading.Thread(
                target=self._proc_feature,
                args=(to_proc, running)
            )
            thread.start()
            threads.append(thread)
        return threads, running, to_proc

    def _gen_feature_collection(self):
        """Extract polygons from contours to generate feature collection.

        The feature collection will be split and inserted as individual
        GeoJSON docs for the db; however, it is easier to keep them together
        in a Feature Collection while being staged.
        """
        threads, running, jobs = self._init_featureproc_threads()
        for collection in self._contours.collections:
            color = collection.get_facecolor()
            for path in collection.get_paths():
                feature_data = (path, color)
                jobs.put(feature_data)
        running.clear()
        for thread in threads:
            thread.join()

    def _proc_feature(self, to_proc, running):
        """Add info fields to the feature (a hail contour)

        Each feature must have a 'id' field as this is the relational
        link between all the hail contours for a given station and time.
        The other attributes may or may not be set and could change overtime.
        """
        while True:
            try:
                feature = to_proc.get(True, 1)
                path = feature[0]
                color = feature[1][0]
                if not isinstance(color, str):
                    color = rgb2hex(color)
                for coord in path.to_polygons():
                    polygon_coords = np.around(coord, 3)
                    value = round(self._data_mappings[color], 2)
                    feature_polygon = Polygon(
                        coordinates=polygon_coords.tolist()
                    )
                    feature = Feature(
                        geometry=feature_polygon,
                        properties={'color': color}
                    )
                    feature['properties']['id'] = self._id
                    feature['properties']['elevation'] = 0.5
                    feature['properties']['sweep'] = 0
                    feature['properties']['value'] = value
                    feature['station'] = self._station
                    feature['collectiontime'] = self._date
                    self._features.append(feature)
                to_proc.task_done()
            except queue.Empty:
                if not running.is_set():
                    break

    def _set_id(self):
        """Set the unique identifying information for hail contours.

        Each feature of the GeoJSON will be a seperate doc in the db,
        linked by this id tag as one of the fields.

        Id format = "S<station-code>C<collection-time-of-radar>":
            S serves as a delimiter for the <station-code> and
            C serves as a delimiter for the <collection-time-of-radar>
        """
        self._id = 'S{}C{}'.format(self._station, self._date.strftime('%m%d%Y%H%M'))

    def _set_doc_id(self):
        """Set the unique identifying information for doc.

        This will be stored in a related collection, to make
        querying for parts of the hail contours more efficient.
        """
        self._id_doc = {
            'id': self._id,
            'station': self._station,
            'algorithm': self._algorithm,
            'collectiontime': self._date,
            'featurecount': len(self._features)
        }

    def get_relational_id(self):
        """Unique identifier in a doc used to query for the parts
        of hail contours in the database.
        return Unique identifier for docs (stored in related collection)
        """
        return self._id_doc

    def get_id(self):
        """Unique identifier for the radar processed
        return Unique identifier for docs
        """
        return self._id

    def get_features(self):
        """return list of GeoJSON Features"""
        return self._features

    def get_metadata(self):
        """return dict with identifying information"""
        return {
            'station': self._station,
            'algorithm': self._algorithm,
            'collectiontime': self._date
        }
