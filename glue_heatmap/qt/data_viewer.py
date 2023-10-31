
from glue.utils import defer_draw, decorate_all_methods
from glue_qt.viewers.matplotlib.data_viewer import MatplotlibDataViewer
from glue_qt.viewers.image.mouse_mode import RoiClickAndDragMode

from glue_heatmap.qt.layer_style_editor import HeatmapLayerStyleEditor
from glue_heatmap.qt.layer_style_editor_subset import HeatmapLayerSubsetStyleEditor
from glue_heatmap.layer_artist import HeatmapLayerArtist, HeatmapSubsetLayerArtist
from glue_heatmap.qt.options_widget import HeatmapOptionsWidget
from glue_heatmap.state import HeatmapViewerState
from glue_heatmap.viewer import MatplotlibHeatmapMixin

__all__ = ["HeatmapViewer"]


@decorate_all_methods(defer_draw)
class HeatmapViewer(MatplotlibHeatmapMixin, MatplotlibDataViewer):
    LABEL = "Heatmap"
    _default_mouse_mode_cls = RoiClickAndDragMode
    _layer_style_widget_cls = {
        HeatmapLayerArtist: HeatmapLayerStyleEditor,
        HeatmapSubsetLayerArtist: HeatmapLayerSubsetStyleEditor,
    }
    _state_cls = HeatmapViewerState
    _options_cls = HeatmapOptionsWidget

    allow_duplicate_data = False

    # NOTE: _data_artist_cls and _subset_artist_cls are not defined - instead
    #       we override get_data_layer_artist and get_subset_layer_artist for
    #       more advanced logic.

    tools = [
        "select:rectangle",
        "select:xrange",
        "select:yrange",
        "image:contrast_bias",
    ]

    def __init__(self, session, parent=None, state=None):
        MatplotlibDataViewer.__init__(
            self, session, wcs=False, parent=parent, state=state
        )
        MatplotlibHeatmapMixin.setup_callbacks(self)
        self.state.add_callback("cluster", self._update_axes)
        self._wcs_set = False

    def closeEvent(self, *args):
        super().closeEvent(*args)
        if self.axes._composite_image is not None:
            self.axes._composite_image.remove()
            self.axes._composite_image = None
