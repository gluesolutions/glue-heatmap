"""
There is a BaseImageLayerState as well which we might need to modify
"""

from glue.viewers.image.state import ImageViewerState, ImageLayerState, ImageSubsetLayerState

__all__ = ['HeatmapViewerState', 'HeatmapLayerState', 'HeatmapSubsetLayerState']

class HeatmapViewerState(ImageViewerState):
    """
    A state class that includes all the attributes for a Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__()


class HeatmapLayerState(ImageLayerState):
    """
    A state class that includes all the attributes for data layers in a Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__()

class HeatmapSubsetLayerState(ImageSubsetLayerState):
    """
    A state class that includes all the attributes for subset layers in Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__()