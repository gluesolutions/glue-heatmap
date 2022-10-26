from .data_viewer import HeatmapViewer  # noqa
from .cluster_tool import ClusterTool # noqa
from .subset_tool import SubsetTool # noqa
from ..menubar_plugin import extract_to_matrix_plugin # noqa

def setup():

    from glue.config import qt_client
    qt_client.add(HeatmapViewer)
