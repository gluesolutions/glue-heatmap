from ..data_viewer import HeatmapViewer
from glue.app.qt import GlueApplication
from glue.core.state import GlueUnSerializer
from glue.core.data import Data
import numpy as np

from glue_heatmap.coords import HeatmapCoordinates


class TestHeatmapViewer(object):
    def setup_method(self, method):
        self.app = GlueApplication()
        self.session = self.app.session
        self.hub = self.session.hub
        self.data_collection = self.session.data_collection
        values = np.array([[1, 2, 3], [4, 5, 6]])
        strain_names = ["A", "B"]
        marker_names = ["1", "2", "3"]
        strain_array = np.array([strain_names for x in range(values.shape[1])]).T
        marker_array = np.array([marker_names for x in range(values.shape[0])])
        self.data = Data(
            values=values,
            x_cats=marker_array,
            y_cats=strain_array,
            coords=HeatmapCoordinates(
                marker_names, strain_names, "Marker Name", "Parent Strain"
            ),
            label="test_data",
        )
        self.data_collection.append(self.data)
        self.viewer = self.app.new_data_viewer(HeatmapViewer)
        self.viewer.add_data(self.data)

    def test_basic(self):
        assert self.viewer is not None
        assert self.viewer.state.x_att_world is self.data.id["Marker Name"]
        assert self.viewer.state.y_att_world is self.data.id["Parent Strain"]
        assert self.viewer.state.cluster is False
        assert self.viewer.state.row_subset is None
        assert self.viewer.state.col_subset is None

    def test_save_and_restore(self, tmpdir):

        filename = tmpdir.join("test_heatmap_session.glu").strpath

        self.session.application.save_session(filename)

        with open(filename, "r") as f:
            session = f.read()

        state = GlueUnSerializer.loads(session)

        ga = state.object("__main__")

        viewer = ga.viewers[0][0]
        assert viewer.state.x_att_world.label == "Marker Name"
        ga.close()
