import pandas as pd
from glue.core import Data, DataCollection
from glue.app.qt import GlueApplication

from glue_heatmap.coords import HeatmapCoordinates
from glue_heatmap.qt import HeatmapViewer

def demo():
    from glue_heatmap.qt import setup
    setup()
    qtl_matrix = pd.read_csv('islet_eQTL_matrix.csv').drop_duplicates(subset='marker.id')
    col_names = ['A','B','C','D','E','F','G','H']
    x = qtl_matrix[col_names].values
    heatmap_data = Data(x=x, label='test',
                        coords=HeatmapCoordinates(qtl_matrix['marker.id'].values, 
                                                    col_names, 'Marker ID',  'Parent Strain'))

    dc = DataCollection([
        heatmap_data,])

    ga = GlueApplication(dc)
    t = ga.new_data_viewer(HeatmapViewer)
    t.add_data(dc[0])
    ga.start()


if __name__ == "__main__":
    demo()