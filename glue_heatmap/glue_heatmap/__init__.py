def setup():
    from .qt.viewer import HeatmapViewer # noqa
    from glue.config import qt_client
    qt_client.add(HeatmapViewer)