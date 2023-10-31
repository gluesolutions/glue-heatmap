import pandas as pd
from glue.core import Data, DataCollection
from glue_qt.viewers.scatter import ScatterViewer
from glue.app.qt import GlueApplication
from glue.core.link_helpers import JoinLink
from glue.core.joins import get_mask_with_key_joins

from glue_heatmap.coords import HeatmapCoordinates
from glue_heatmap.qt import HeatmapViewer
from glue.core.exceptions import IncompatibleAttribute
import traceback


def norecurse(f):
    def func(*args, **kwargs):
        if len([x[2] for x in traceback.extract_stack() if x[2] == f.__name__]) > 0:
            raise IncompatibleAttribute
        return f(*args, **kwargs)
    return func


class MatrixData(Data):
    def get_mask(self, subset_state, view=None):
        try:
            return subset_state.to_mask(self, view=view)
        except IncompatibleAttribute:
            return norecurse(get_mask_with_key_joins)(self, self._key_joins, subset_state, view=view)


def demo():
    qtl_matrix = pd.read_csv("islet_eQTL_matrix.csv").drop_duplicates(
        subset="marker.id"
    )
    strain_names = ["A", "B", "C", "D", "E", "F", "G", "H"]
    values = qtl_matrix[strain_names].values.T
    marker_names = qtl_matrix["marker.id"].values

    heatmap_data = MatrixData(
        values=values,
        label="test",
        coords=HeatmapCoordinates(
            marker_names, strain_names, "Marker Name", "Parent Strain"
        ),
    )
    strains = Data(strain=["A", "B", "C", "D", "E"], label="strains")
    markers = Data(markers=["6_125562888", "9_50632541", "16_26087386", "2_59628224"], label="markers")

    dc = DataCollection([heatmap_data, strains, markers])

    ga = GlueApplication(dc)

    # Using JoinLinks on both rows and cols causes all subsets to propagate through the matrix
    # which is not ideal. In real usage this is probably a DataAnnData object
    marker_link = JoinLink(cids1=[heatmap_data.id["Marker Name"]], cids2=[markers.id["markers"]], data1=heatmap_data, data2=markers)
    # marker_link = LinkSame(heatmap_data.id["Marker Name"], markers.id["markers"])
    dc.add_link(marker_link)

    strain_link = JoinLink(cids1=[heatmap_data.id["Parent Strain"]], cids2=[strains.id["strain"]], data1=heatmap_data, data2=strains)
    # strain_link = LinkSame(heatmap_data.id["Parent Strain"], strains.id["strain"])
    dc.add_link(strain_link)

    t = ga.new_data_viewer(HeatmapViewer)
    t.add_data(dc[0])

    u = ga.new_data_viewer(ScatterViewer)
    u.add_data(dc[1])

    v = ga.new_data_viewer(ScatterViewer)
    v.add_data(dc[2])

    ga.start()


if __name__ == "__main__":
    demo()
