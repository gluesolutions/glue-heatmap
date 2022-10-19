from glue.viewers.image.viewer import MatplotlibImageMixin
#from glue.core.util import update_ticks

__all__ = ['MatplotlibHeatmapMixin']

from itertools import count
from functools import partial
import numpy as np

from matplotlib.ticker import AutoLocator, MaxNLocator, LogLocator
from matplotlib.ticker import LogFormatterMathtext, ScalarFormatter, FuncFormatter
from matplotlib.dates import AutoDateLocator, AutoDateFormatter
import matplotlib.ticker as mticker


def tick_linker(all_categories, pos, *args):
    # We need to take care to ignore negative indices since these would actually
    # 'work' 'when accessing all_categories, but we need to avoid that.
    if pos < 0 or pos >= len(all_categories):
        return ''
    else:
        try:
            pos = np.round(pos)
            label = all_categories[int(pos)]
            if isinstance(label, bytes):
                return label.decode('ascii')
            else:
                return label
        except IndexError:
            return ''


def update_ticks(axes, coord, kinds, is_log, categories, projection='rectilinear', radians=True, label=None):
    """
    Changes the axes to have the proper tick formatting based on the type of
    component.

    Returns `None` or the number of categories if components is Categorical.

    Parameters
    ----------
    axes : :class:`matplotlib.axes.Axes`
        A matplotlib axis object to alter
    coord : { 'x' | 'y' }
        The coordinate axis on which to update the ticks
    kinds : iterable
        A list of component kinds that are plotted along this axis
    if_log : boolean
        Whether the axis has a log-scale
    categories: iterable
        A list of the categorical values to plot
    projection: str
        The name of the matplotlib projection for the axes object. Defaults to 'rectilinear'.
        Currently only the scatter viewer supports different projections.
    """

    if projection == 'lambert' and coord == 'y':
        return

    if coord == 'x':
        axis = axes.xaxis
    elif coord == 'y':
        axis = axes.yaxis
    else:
        raise TypeError("coord must be one of x,y")

    is_cat = 'categorical' in kinds
    is_date = 'datetime' in kinds

    if is_date:
        loc = AutoDateLocator()
        fmt = AutoDateFormatter(loc)
        axis.set_major_locator(loc)
        axis.set_major_formatter(fmt)
    elif is_log:
        axis.set_major_locator(LogLocator())
        axis.set_major_formatter(LogFormatterMathtext())
    elif is_cat:
        #import ipdb; ipdb.set_trace()
        locator = MaxNLocator(20, integer=True)
        locator.view_limits(0, categories.shape[0])
        format_func = partial(tick_linker, categories)
        formatter = FuncFormatter(format_func)
        axis.set_major_locator(locator)
        axis.set_major_formatter(formatter)


class MatplotlibHeatmapMixin(MatplotlibImageMixin):


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
            update_ticks(self.axes, 'x', ['categorical'], False, x_ticks)

        if self.state.y_att_world is not None:
            self.state.y_axislabel = self.state.y_att_world.label
            y_ticks =self.state.reference_data.coords.get_tick_labels(self.state.y_axislabel)
            update_ticks(self.axes, 'y', ['categorical'], False, y_ticks)

        self.state.reset_limits()
        self.axes.figure.canvas.draw_idle()

    def _set_wcs(self, event=None, relim=True):

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