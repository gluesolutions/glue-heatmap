"""
There is a BaseImageLayerState as well which we might need to modify
"""

import copy
from glue.core import BaseData

from glue.viewers.image.state import ImageViewerState, ImageLayerState, ImageSubsetLayerState

__all__ = ['HeatmapViewerState', 'HeatmapLayerState', 'HeatmapSubsetLayerState']



class HeatmapViewerState(ImageViewerState):
    """
    A state class that includes all the attributes for a Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__()
        HeatmapViewerState.aspect.set_choices(self, ['auto'])

    def _set_reference_data(self):
        """
        In the case of tabular data, this is where we make
        the dataset. In the case of a 2D matrix, this
        is where we make a copy of the dataset so that
        clustering the data...

        Well, do we want clustering the data to change
        anything in the original data? Not really, it's
        cosmetic, right?
        """
        if self.reference_data is None:
            for layer in self.layers:
                if isinstance(layer.layer, BaseData):
                    self.reference_data = layer.layer
                    return


    @property
    def x_categories(self):
        return self.reference_data.coords.get_tick_labels('x')

    @property
    def y_categories(self):
        return self.reference_data.coords.get_tick_labels('y')



class HeatmapLayerState(ImageLayerState):
    """
    A state class that includes all the attributes for data layers in a Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class HeatmapSubsetLayerState(ImageSubsetLayerState):
    """
    A state class that includes all the attributes for subset layers in Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)