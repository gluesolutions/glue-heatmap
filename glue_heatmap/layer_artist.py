"""
There is also a BaseImageLayerArtist
and an ImageSubsetArray.

Do we need to modify either of these?
"""

from glue.viewers.image.layer_artist import ImageLayerArtist, ImageSubsetLayerArtist

from glue_heatmap.state import HeatmapLayerState, HeatmapSubsetLayerState


__all__ = ['HeatmapLayerArtist', 'HeatmapSubsetLayerArtist']


class HeatmapLayerArtist(ImageLayerArtist):
    """
    """
    _layer_state_cls = HeatmapLayerState

    def __init__(self, axes, viewer_state, layer_state=None, layer=None):
        super().__init__(axes, viewer_state, layer_state=layer_state, layer=layer)

class HeatmapSubsetLayerArtist(ImageSubsetLayerArtist):
    _layer_state_cls = HeatmapSubsetLayerState

    def __init__(self, axes, viewer_state, layer_state=None, layer=None):
        super().__init__(axes, viewer_state, layer_state=layer_state, layer=layer)
