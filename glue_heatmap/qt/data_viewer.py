
# TODO: Do we need to make custom versions of these? If so, we might need to import them
# Import the mouse mode to make sure it gets registered
#from glue.viewers.image.qt.contrast_mouse_mode import ContrastBiasMode  # noqa
#from glue.viewers.image.qt.pixel_selection_mode import PixelSelectionTool  # noqa

import math

from glue.utils import defer_draw, decorate_all_methods
from glue.viewers.matplotlib.qt.data_viewer import MatplotlibDataViewer
from glue.viewers.image.qt.mouse_mode import RoiClickAndDragMode
from glue.core.subset import roi_to_subset_state, InequalitySubsetState, MultiOrState

from glue_heatmap.qt.layer_style_editor import HeatmapLayerStyleEditor
from glue_heatmap.qt.layer_style_editor_subset import HeatmapLayerSubsetStyleEditor
from glue_heatmap.layer_artist import HeatmapLayerArtist, HeatmapSubsetLayerArtist
from glue_heatmap.qt.options_widget import HeatmapOptionsWidget
from glue_heatmap.state import HeatmapViewerState
from glue_heatmap.viewer import MatplotlibHeatmapMixin

__all__ = ['HeatmapViewer']


@decorate_all_methods(defer_draw)
class HeatmapViewer(MatplotlibHeatmapMixin, MatplotlibDataViewer):

    LABEL = 'Heatmap'
    _default_mouse_mode_cls = RoiClickAndDragMode
    _layer_style_widget_cls = {HeatmapLayerArtist: HeatmapLayerStyleEditor,
                               HeatmapSubsetLayerArtist: HeatmapLayerSubsetStyleEditor,
                               }
    _state_cls = HeatmapViewerState
    _options_cls = HeatmapOptionsWidget

    allow_duplicate_data = False

    # NOTE: _data_artist_cls and _subset_artist_cls are not defined - instead
    #       we override get_data_layer_artist and get_subset_layer_artist for
    #       more advanced logic.

    tools = ['select:rectangle', 'select:xrange',
             'select:yrange', 'image:point_selection', 'image:contrast_bias',
             'heatmap:cluster'
             ]

    def __init__(self, session, parent=None, state=None):
        MatplotlibDataViewer.__init__(self, session, wcs=False, parent=parent, state=state)
        MatplotlibHeatmapMixin.setup_callbacks(self)
        self._wcs_set = False

    def closeEvent(self, *args):
        super().closeEvent(*args)
        if self.axes._composite_image is not None:
            self.axes._composite_image.remove()
            self.axes._composite_image = None

    def apply_roi(self, roi, override_mode=None):
        self.redraw()

        if len(self.layers) == 0:
            return

        if self.state.x_att is None or self.state.y_att is None or self.state.reference_data is None:
            return
        
        x_categories = self.state.reference_data.coords.get_tick_labels('x')
        y_categories = self.state.reference_data.coords.get_tick_labels('y')

        subset_state = roi_to_subset_state(roi,
                                           x_att=self.state.x_att_world, x_categories=self.state.x_categories,
                                           y_att=self.state.y_att_world, y_categories=self.state.y_categories,
                                           use_pretransform=False)
        #import ipdb; ipdb.set_trace()
        self.apply_subset_state(subset_state, override_mode=override_mode)