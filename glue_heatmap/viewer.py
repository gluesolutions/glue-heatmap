from glue.viewers.image.viewer import MatplotlibImageMixin
from functools import partial
import math

from matplotlib.ticker import FixedLocator, FuncFormatter
from glue.core.util import tick_linker
from glue.core.subset import roi_to_subset_state

from glue_heatmap.layer_artist import HeatmapLayerArtist, HeatmapSubsetLayerArtist

__all__ = ["MatplotlibHeatmapMixin"]


def set_locator(axis_min, axis_max, tick_labels, axis):
    axis_range = math.ceil(axis_max) - math.floor(
        axis_min
    )  # TODO: What is the axes ranges are flipped?
    max_num_cats = min(int(axis_range), 30)
    locator = FixedLocator(
        range(math.floor(axis_min), math.ceil(axis_max), 1), nbins=max_num_cats
    )
    format_func = partial(tick_linker, tick_labels)
    formatter = FuncFormatter(format_func)
    axis.set_major_locator(locator)
    axis.set_major_formatter(formatter)


class MatplotlibHeatmapMixin(MatplotlibImageMixin):
    def limits_from_mpl(self, *args, **kwargs):
        super().limits_from_mpl(*args, **kwargs)

        if self.state.reference_data is None:
            return

        x_ticks = self.state.x_categories
        y_ticks = self.state.y_categories

        set_locator(self.state.x_min, self.state.x_max, x_ticks, self.axes.xaxis)
        set_locator(self.state.y_min, self.state.y_max, y_ticks, self.axes.yaxis)

    def update_x_ticklabel(self, *event):
        # Original image viewer calls this functions assuming
        # we are using a WCSAxes object, which we are not in the Heatmap
        self.axes.tick_params(axis="x", labelsize=self.state.x_ticklabel_size)
        self.axes.xaxis.get_offset_text().set_fontsize(self.state.x_ticklabel_size)
        self.redraw()

    def update_y_ticklabel(self, *event):
        # Original image viewer calls this functions assuming
        # we are using a WCSAxes object, which we are not in the Heatmap
        self.axes.tick_params(axis="y", labelsize=self.state.y_ticklabel_size)
        self.axes.yaxis.get_offset_text().set_fontsize(self.state.y_ticklabel_size)
        self.redraw()

    def _update_axes(self, *args):
        if self.state.x_att_world is not None:
            self.state.x_axislabel = self.state.x_att_world.label
            x_ticks = self.state.x_categories
            set_locator(0, x_ticks.shape[0], x_ticks, self.axes.xaxis)
            # We want to rotate "long" labels and expand the margins
            self.axes.tick_params(axis="x", labelrotation=90)
            self.axes.resizer.margins = [1, 0.1, 1.2, 0.1]

        if self.state.y_att_world is not None:
            self.state.y_axislabel = self.state.y_att_world.label
            y_ticks = self.state.y_categories
            set_locator(0, y_ticks.shape[0], y_ticks, self.axes.yaxis)
            # Expand the margins if the tick labels are "long"
            # self.axes.resizer.margins = [1, 0.1, 1.2, 0.1]

        self.state.reset_limits()
        self.axes.figure.canvas.draw_idle()

    def _set_wcs(self, event=None, relim=True):  # TODO: Do we really need this?
        if (
            self.state.x_att is None
            or self.state.y_att is None
            or self.state.reference_data is None
        ):
            return

        _ = getattr(self.state.reference_data, "coords", None)

        # Reset the axis labels to match the fact that the new axes have no labels
        self.state.x_axislabel = ""
        self.state.y_axislabel = ""

        self._update_appearance_from_settings()
        self._update_axes()

        if relim:
            self.state.reset_limits()

        self._wcs_set = True

    def get_data_layer_artist(self, layer=None, layer_state=None):
        if layer.ndim == 1:
            pass
            # cls = self._scatter_artist
        else:
            cls = HeatmapLayerArtist
        return self.get_layer_artist(cls, layer=layer, layer_state=layer_state)

    def get_subset_layer_artist(self, layer=None, layer_state=None):
        if layer.ndim == 1:
            pass
            # cls = self._scatter_artist
        else:
            cls = HeatmapSubsetLayerArtist
        return self.get_layer_artist(cls, layer=layer, layer_state=layer_state)

    def apply_roi(self, roi, override_mode=None):
        self.redraw()

        if len(self.layers) == 0:
            return

        if (
            self.state.x_att is None
            or self.state.y_att is None
            or self.state.reference_data is None
        ):
            return

        subset_state = roi_to_subset_state(
                roi,
                x_att=self.state.x_att_world,
                x_categories=self.state.x_categories,
                y_att=self.state.y_att_world,
                y_categories=self.state.y_categories)
        self.apply_subset_state(subset_state, override_mode=override_mode)

    def _add_subset(self, subset):
        super()._add_subset(subset)
        self.state._sync_subsets()

    def _remove_subset(self, subset):
        super()._remove_subset(subset)
        self.state._sync_subsets()

    def _update_subset(self, subset):
        super()._update_subset(subset)
        self.state._sync_subsets()
        if subset.subset is self.state.row_subset or subset.subset is self.state.col_subset:
            self.state._calculate_heatmap_data()
            self._update_axes()
