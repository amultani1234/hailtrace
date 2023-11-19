"""@class Implementation of Hail Differential Reflectivity (HDR) algorithm
Refernce Hail Detection with a Differential Reflectivity Radar (Bringi, 1984)
"""
import logging


class HailDifferentialReflectivity:
    _HDR_MIN = 27  # dB
    _HDR_MAX = 60  # dB

    def __init__(self, radar=None):
        if radar is not None:
            self._radar = radar
            self._apply()
        else:
            self._radar = None
            logging.warning("Radar must be set before calculation")

    def _apply(self):
        """Calculate and append HDR values to pyart.core.radar.Radar object"""
        if self._radar is None:
            logging.error("Radar must be set before calculation")
            return

        def _calculate(zdr):
            """Calculate the altered differential reflectivity.
            gzdr is the corrected data accounting for lower reflectivity of hail."""
            gzdr = (19 * zdr) + 27
            gzdr[zdr <= 0] = 27
            gzdr[zdr > 1.74] = 60
            return gzdr

        z = self._radar.fields['reflectivity']['data']
        zdr = self._radar.fields['differential_reflectivity']['data']
        gzdr = _calculate(zdr)
        hdr = (z - gzdr)
        self._radar.add_field(
            'HDR',
            {
                'units': 'dB',
                'standard_name': 'HDR',
                'long_name': 'Hail Differential Reflectivity',
                'valid_max': self._HDR_MAX,
                'valid_min': self._HDR_MIN,
                'coordinates': 'elevation azimuth range',
                '_FillValue': -9999.,
                'data': hdr
            }
        )

    def get_radar(self):
        if self._radar is None:
            logging.error("Radar must be set before calculation")
            return None
        else:
            return self._radar

    def set_radar(self, radar):
        self._radar = radar
        self._apply()
