from glue.viewers.image.viewer import MatplotlibImageMixin
from itertools import count
from functools import partial
import numpy as np
import math

from matplotlib.ticker import FixedLocator, FuncFormatter
from glue.core.util import tick_linker
from glue.core.data import BaseData, Data

from glue_heatmap.layer_artist import HeatmapLayerArtist, HeatmapSubsetLayerArtist
from glue_heatmap.coords import HeatmapCoordinates

__all__ = ['MatplotlibHeatmapMixin']


def set_locator(axis_min, axis_max, tick_labels, axis):
    axis_range = math.ceil(axis_max) - math.floor(axis_min) #TODO: What is the axes ranges are flipped?
    max_num_cats = min(int(axis_range), 30)
    locator = FixedLocator(range(math.floor(axis_min), math.ceil(axis_max), 1), nbins=max_num_cats)
    format_func = partial(tick_linker, tick_labels)
    formatter = FuncFormatter(format_func)
    axis.set_major_locator(locator)
    axis.set_major_formatter(formatter)


def clone_subset_into_data_object(subset):
    """
    A helper function to clone a data object

    https://stackoverflow.com/questions/39206986/numpy-get-rectangle-area-just-the-size-of-mask
    """
    new_data = Data()
    old_data = subset.data
    i,j = np.where(subset.to_mask())
    indices = np.meshgrid(np.arange(min(i), max(i) + 1),
                          np.arange(min(j), max(j) + 1),
                          indexing='ij')
    for component in old_data.main_components:
        new_data.add_component(old_data[component][tuple(indices)],label=component.label)

    if old_data.coords:
        new_y_ticks = old_data.coords._y_tick_names[np.unique(i)]
        new_x_ticks = old_data.coords._x_tick_names[np.unique(j)]
        new_data.coords = HeatmapCoordinates(new_x_ticks, new_y_ticks, old_data.coords._x_tick_label, old_data.coords._y_tick_label)

    new_data.label = f'{old_data.label} | {subset.label}'
    return new_data

class MatplotlibHeatmapMixin(MatplotlibImageMixin):

    def add_data(self, data):
        """
        Heatmap Viewers work a little different because we need to create specific data
        
        """
        if isinstance(data, BaseData) and data.ndim == 2: # This is a matrix object all set to go
            print("Adding a BaseData with data.ndim == 2")
            super().add_data(data)
        elif isinstance(data, BaseData) and data.ndim == 1: # This is a table object
            # Really we want to do something different here
            super().add_data(data)
        else: # Fallback
            super().add_data(data)

    def add_subset(self, subset):
        if len(self.layers) == 0: #If we have just a subset all by itself we need to create a dataset
            print("Adding just a subset, special logic applies")
            new_data = clone_subset_into_data_object(subset)
            self.session.data_collection.append(new_data)
            super().add_data(new_data)
        else:
            super().add_subset(subset)


    def limits_from_mpl(self, *args, **kwargs):
        super().limits_from_mpl(*args, **kwargs)
        
        if self.state.reference_data is None:
            return

        x_ticks = self.state.reference_data.coords.get_tick_labels('x')#self.state.x_axislabel)
        y_ticks = self.state.reference_data.coords.get_tick_labels('y')#self.state.y_axislabel)
       
        set_locator(self.state.x_min, self.state.x_max, x_ticks, self.axes.xaxis)
        set_locator(self.state.y_min, self.state.y_max, y_ticks, self.axes.yaxis)

    def update_x_ticklabel(self, *event):
        # Original image viewer calls this functions assuming
        # we are using a WCSAxes object, which we are not in the Heatmap
        self.axes.tick_params(axis='x', labelsize=self.state.x_ticklabel_size)
        self.axes.xaxis.get_offset_text().set_fontsize(self.state.x_ticklabel_size)
        self.redraw()

    def update_y_ticklabel(self, *event):
        # Original image viewer calls this functions assuming
        # we are using a WCSAxes object, which we are not in the Heatmap
        self.axes.tick_params(axis='y', labelsize=self.state.y_ticklabel_size)
        self.axes.yaxis.get_offset_text().set_fontsize(self.state.y_ticklabel_size)
        self.redraw()

    def _update_axes(self, *args):

        if self.state.x_att_world is not None:
            self.state.x_axislabel = self.state.x_att_world.label
            x_ticks = self.state.reference_data.coords.get_tick_labels('x')
            set_locator(0, x_ticks.shape[0], x_ticks, self.axes.xaxis)
            # We want to rotate "long" labels and expand the margins
            self.axes.tick_params(axis='x', labelrotation=90)
            self.axes.resizer.margins = [1, 0.1, 1.2, 0.1]

        if self.state.y_att_world is not None:
            self.state.y_axislabel = self.state.y_att_world.label
            y_ticks =self.state.reference_data.coords.get_tick_labels('y')
            set_locator(0, y_ticks.shape[0], y_ticks, self.axes.yaxis)
            # Expand the margins if the tick labels are "long"
            # self.axes.resizer.margins = [1, 0.1, 1.2, 0.1]

        self.state.reset_limits()
        self.axes.figure.canvas.draw_idle()

    def _set_wcs(self, event=None, relim=True): # TODO: Do we really need this?

        if self.state.x_att is None or self.state.y_att is None or self.state.reference_data is None:
            return

        ref_coords = getattr(self.state.reference_data, 'coords', None)

        # Reset the axis labels to match the fact that the new axes have no labels
        self.state.x_axislabel = ''
        self.state.y_axislabel = ''

        self._update_appearance_from_settings()
        self._update_axes()

        if relim:
            self.state.reset_limits()

        self._wcs_set = True

    def get_data_layer_artist(self, layer=None, layer_state=None):
        if layer.ndim == 1:
            pass
            #cls = self._scatter_artist
        else:
            cls = HeatmapLayerArtist
        return self.get_layer_artist(cls, layer=layer, layer_state=layer_state)

    def get_subset_layer_artist(self, layer=None, layer_state=None):
        if layer.ndim == 1:
            pass
            #cls = self._scatter_artist
        else:
            cls = HeatmapSubsetLayerArtist
        return self.get_layer_artist(cls, layer=layer, layer_state=layer_state)
