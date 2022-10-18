from .data_viewer import HeatmapViewer  # noqa

def setup():
    from glue.config import qt_client
    qt_client.add(HeatmapViewer)
