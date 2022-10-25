import pandas as pd
import numpy as np
from glue.core import Data, DataCollection
from glue.app.qt import GlueApplication
from glue.core.link_helpers import JoinLink, LinkSame

from glue_heatmap.coords import HeatmapCoordinates
from glue_heatmap.qt import HeatmapViewer

def demo():
    qtl_matrix = pd.read_csv('islet_eQTL_matrix.csv').drop_duplicates(subset = 'marker.id')
    strain_names = ['A','B','C','D','E','F','G','H']
    values = qtl_matrix[strain_names].values.T
    marker_names = qtl_matrix['marker.id'].values
    
    strain_array = np.array([strain_names for x in range(values.shape[1])]).T
    marker_array = np.array([marker_names for x in range(values.shape[0])])

    heatmap_data = Data(values = values,
                        y_cats = strain_array,
                        x_cats = marker_array,
                        label = 'test',
                        coords = HeatmapCoordinates(marker_names, strain_names,
                                                   'Marker Name', 'Parent Strain'))
    strains = Data(strain = ['A','B','C'], label = 'strains')
    markers = Data(markers = ['6_125562888','9_50632541'], label = 'markers')

    dc = DataCollection([
        heatmap_data,
        strains,
        markers])

    ga = GlueApplication(dc)
    
    marker_link = LinkSame(heatmap_data.id['x_cats'], markers.id['markers'] )
    dc.add_link(marker_link)

    strain_link = LinkSame(heatmap_data.id['y_cats'], strains.id['strain'] )

    dc.add_link(strain_link)


    t = ga.new_data_viewer(HeatmapViewer)
    t.add_data(dc[0])
    ga.start()


if __name__ == "__main__":
    demo()