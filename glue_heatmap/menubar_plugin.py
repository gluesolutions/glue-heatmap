from glue.config import menubar_plugin

from glue_heatmap.qt.extract_to_matrix import ExtractToMatrixDialog

@menubar_plugin("Extract colums/rows of a table to a 2D matrix")
def extract_to_matrix_plugin(session, data_collection):
    ExtractToMatrixDialog.create_matrix(data_collection,
                                    default=None, parent=None)
    return
