from glue.viewers.image.viewer import MatplotlibImageMixin
#from glue.core.util import update_ticks

__all__ = ['MatplotlibHeatmapMixin']

from itertools import count
from functools import partial
import numpy as np
import math

from matplotlib.ticker import FixedLocator, FuncFormatter
from glue.core.util import tick_linker

def set_locator(axis_min, axis_max, tick_labels, axis):
    axis_range = math.ceil(axis_max) - math.floor(axis_min) #TODO: What is the axes ranges are flipped?
    max_num_cats = min(int(axis_range), 30)
    locator = FixedLocator(range(math.floor(axis_min), math.ceil(axis_max), 1), nbins=max_num_cats)
    format_func = partial(tick_linker, tick_labels)
    formatter = FuncFormatter(format_func)
    axis.set_major_locator(locator)
    axis.set_major_formatter(formatter)


class MatplotlibHeatmapMixin(MatplotlibImageMixin):

    def limits_from_mpl(self, *args, **kwargs):
        super().limits_from_mpl(*args, **kwargs)
        
        if self.state.reference_data is None:
            return

        x_ticks = self.state.reference_data.coords.get_tick_labels(self.state.x_axislabel)
        y_ticks = self.state.reference_data.coords.get_tick_labels(self.state.y_axislabel)
       
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
            x_ticks = self.state.reference_data.coords.get_tick_labels(self.state.x_axislabel) 
            set_locator(0, x_ticks.shape[0], x_ticks, self.axes.xaxis)
            # We want to rotate "long" labels and expand the margins
            self.axes.tick_params(axis='x', labelrotation=90)
            self.axes.resizer.margins = [1, 0.1, 1.2, 0.1]

        if self.state.y_att_world is not None:
            self.state.y_axislabel = self.state.y_att_world.label
            y_ticks =self.state.reference_data.coords.get_tick_labels(self.state.y_axislabel)
            set_locator(0, y_ticks.shape[0], y_ticks, self.axes.yaxis)
            # Expand the margins if the tick labels are "long"
            # self.axes.resizer.margins = [1, 0.1, 1.2, 0.1]

        self.state.reset_limits()
        self.axes.figure.canvas.draw_idle()

    def _set_wcs(self, event=None, relim=True): # TODO: Do we need a custom function here?

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