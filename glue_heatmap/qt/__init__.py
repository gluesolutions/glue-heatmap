from .data_viewer import HeatmapViewer  # noqa
#from .subset_tool import SubsetTool  # noqa
#from ..menubar_plugin import extract_to_matrix_plugin  # noqa


def setup():
    from glue_qt.config import qt_client

    qt_client.add(HeatmapViewer)
