import numpy as np
from glue.core.coordinates import IdentityCoordinates


class HeatmapCoordinates(IdentityCoordinates):
    def __init__(self, x_tick_names, y_tick_names, x_tick_label, y_tick_label, *args, **kwargs):
        super().__init__(n_dim=2)
        self._x_tick_names = np.array(x_tick_names).astype(str)
        self._y_tick_names = np.array(y_tick_names).astype(str)
        self._names = [self._x_tick_names, self._y_tick_names]
        self._x_tick_label = x_tick_label
        self._y_tick_label = y_tick_label

    def get_tick_labels(self, axis_name):
        if axis_name == "x":
            return self._x_tick_names
        elif axis_name == "y":
            return self._y_tick_names

    def pixel_to_world_values(self, *args):
        return tuple([self._names[i][np.round(x)] for i, x in enumerate(args)])

    def world_to_pixel_values(self, *args):
        return tuple([self._names[i].index(x) for i, x in enumerate(args)])

    @property
    def world_axis_names(self):
        # Returns an iterable of strings given the names of the world
        # coordinates for each axis.
        return [self._x_tick_label, self._y_tick_label]

    def __gluestate__(self, context):
        return dict(x_tick_names=context.do(self._x_tick_names),
                    y_tick_names=context.do(self._y_tick_names),
                    x_tick_label=self._x_tick_label,
                    y_tick_label=self._y_tick_label)

    @classmethod
    def __setgluestate__(cls, rec, context):
        return cls(context.object(rec['x_tick_names']),
                   context.object(rec['y_tick_names']),
                   x_tick_label=rec['x_tick_label'],
                   y_tick_label=rec['y_tick_label'])
