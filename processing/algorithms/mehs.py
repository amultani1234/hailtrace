"""@class MaximumExpectedHailSize
Implementation of MEHS (Maximum Expected Hail Size) algorithm
"""
import numpy as np
import pyart
from pyart.map import grid_mapper


class MaximumExpectedHailSize:

    def __init__(self, radar, temps):
        self._grid = self.gridify(radar)
        self.z_min = 40
        self.z_max = 50
        self.altitudes = self._grid.z['data']
        self.SHI = None
        self.weighted_heights = None
        self.weighted_reflectivity = 0
        self.reflectivity = self._grid.fields['reflectivity']['data']
        self.reflectivity_size = np.shape(self._grid.fields['reflectivity']['data'])
        self.kinetic_energy = None
        self.temps = temps
        self.g_mehs = None
        self._apply()

    def gridify(self, radar):
        xmin = np.min(radar.gate_x['data'])
        xmax = np.max(radar.gate_x['data'])
        ymin = np.min(radar.gate_y['data'])
        ymax = np.max(radar.gate_y['data'])

        gatefilter = pyart.filters.GateFilter(radar)
        gatefilter.exclude_transition()
        gatefilter.exclude_below('cross_correlation_ratio', 0.7)
        gatefilter.exclude_masked('reflectivity')

        grid = grid_mapper.grid_from_radars(
            (radar,),
            (20, 500, 500),
            ((0, 20000), (ymin, ymax), (xmin, xmax)),
            fields=('reflectivity',),
            roi_func='constant',
            gatefilters=(gatefilter,),
            constant_roi=1000,
            weighting_function="Barnes2")
        return grid

    def _apply(self):
        self._calculate_shi()
        mehs = 16.566 * self.SHI ** 0.181
        self.g_mehs = np.zeros_like(self.kinetic_energy)
        self.g_mehs[0, :, :] = mehs
        self._grid.add_field("MESH", {
            'data': self.g_mehs,
            'units': 'mm',
            'long_name': "Maximum Expected Size of Hail",
            'standard_name': 'MESH',
            'comments': 'Data is contained on Z index = 0'
        })

    def _kinetic_energy(self):
        """Transform reflectivity data to flux values
        of hail kinetic energy. Formally:
        E = (5*10^-6) * (10^(0.084*Z)) * W(z)
        """
        self.kinetic_energy = (5 * 10 ** (-6)) * 10 ** (0.084 * self.reflectivity) * self.weighted_reflectivity

    def weight_funct_reflectivity(self):
        self.weighted_reflectivity = (self.reflectivity - self.z_min) / (self.z_max - self.z_min)
        self.weighted_reflectivity[
            self.reflectivity <= self.z_min] = 0  # Reflectivity under lower bound is weighted at 0
        self.weighted_reflectivity[
            self.reflectivity >= self.z_max] = 1  # Reflectivity over upper bound is weighted at 1

    def weight_funct_altitudes(self):
        self.altitude_grid = np.tile(self.altitudes, (self.reflectivity_size[1], self.reflectivity_size[2], 1))
        self.altitude_grid = np.swapaxes(self.altitude_grid, 0, 2)

        self.weighted_heights = (self.altitude_grid - self.temps[0]) / (self.temps[1] - self.temps[0])
        self.weighted_heights[
            self.altitude_grid <= self.temps[0]] = 0  ## Any altitude under the 0 Celsius Line is weighted at 0
        self.weighted_heights[
            self.altitude_grid >= self.temps[1]] = 1  ## Any altitude over the -20 Celsius Line is weighted at 1

    def _calculate_shi(self):
        """Calculate Severe Hail Index (SHI)"""
        self.weight_funct_reflectivity()
        self.weight_funct_altitudes()
        self._kinetic_energy()
        altitude_increment = self.altitudes[1] - self.altitudes[0]
        self.SHI = 0.1 * np.sum(self.weighted_heights * self.kinetic_energy, axis=0) * altitude_increment

    def get_grid(self):
        return self._grid
