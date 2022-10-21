import numpy as np
from glue.core.coordinates import IdentityCoordinates

class HeatmapCoordinates(IdentityCoordinates):
    def __init__(self, x_tick_names, y_tick_names, x_tick_label, y_tick_label):
        super().__init__(n_dim=2)
        self._x_tick_names = np.array(x_tick_names)
        self._y_tick_names = np.array(y_tick_names)
        self._x_tick_label = x_tick_label
        self._y_tick_label = y_tick_label

    def get_tick_labels(self, axis_name):
        if (axis_name == 'x'):
            return self._x_tick_names
        elif (axis_name == 'y'):
            return self._y_tick_names

    @property
    def world_axis_names(self):
        # Returns an iterable of strings given the names of the world
        # coordinates for each axis.
        return [self._x_tick_label, self._y_tick_label]