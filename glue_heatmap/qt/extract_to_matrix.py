import os
import numpy as np
from qtpy.QtWidgets import QDialog, QListWidgetItem
from qtpy.QtCore import Qt

from echo.qt import autoconnect_callbacks_to_qt
from glue.utils.qt import load_ui
from glue.core import Data, BaseData
from glue.core.state_objects import State
from echo import SelectionCallbackProperty, CallbackProperty
from glue.viewers.matplotlib.state import DeferredDrawCallbackProperty
from glue.core.data_combo_helper import DataCollectionComboHelper, ComponentIDComboHelper, ComboHelper, ManualDataComboHelper
from echo import ChoiceSeparator
from glue_heatmap.coords import HeatmapCoordinates

from glue.core.link_helpers import JoinLink, LinkSame

class ExtractToMatrixState(State):

    data = SelectionCallbackProperty()
    subset = SelectionCallbackProperty()
    component = SelectionCallbackProperty()
    row = SelectionCallbackProperty()
    col_names = DeferredDrawCallbackProperty("columns")

    def __init__(self, data_collection):

        super().__init__()
        self.dc = data_collection
        self.data_helper = DataCollectionComboHelper(self, 'data', data_collection)
        self.component_helper = ComponentIDComboHelper(self, 'component',
                                                       data_collection=data_collection)
        self.row_helper = ComponentIDComboHelper(self, 'row',
                                                       data_collection=data_collection)
        self.add_callback('data', self._on_data_change)
        self._on_data_change()

    def _on_data_change(self, event=None):
        self.component_helper.set_multiple_data([] if self.data is None else [self.data])
        self.row_helper.set_multiple_data([] if self.data is None else [self.data])

        self._sync_subsets()

    def _sync_subsets(self):

        def display_func(subset):
            if subset is None:
                return "All data (no subsets applied)"
            else:
                return subset.label

        subsets = [None] + list(self.data.subsets)

        ExtractToMatrixState.subset.set_choices(self, subsets)
        ExtractToMatrixState.subset.set_display_func(self, display_func)

class ExtractToMatrixDialog(QDialog):

    def __init__(self, collect,
                default_data=None,
                default_components=None,
                default_row=None,
                default_col_names=None,
                parent=None):

        super().__init__(parent=parent)

        self.state = ExtractToMatrixState(collect)

        self.ui = load_ui('extract_to_matrix.ui', self,
                          directory=os.path.dirname(__file__))
        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)

        if default_data is not None:
            self.state.data = default_data
        if default_components is not None:
            self.default_components = default_components
        if default_row is not None:
            self.state.row = default_row
        if default_col_names is not None:
            self.state.col_names = default_col_names

        self.ui.button_ok.clicked.connect(self.accept)
        self.ui.button_cancel.clicked.connect(self.reject)
        self.ui.button_select_none.clicked.connect(self.select_none)
        self.ui.button_select_all.clicked.connect(self.select_all)

        self.ui.list_component.itemChanged.connect(self._on_check_change)

        self.state.add_callback('component', self._on_data_change)

        self._on_data_change()


    def _on_data_change(self, *event):

        components = getattr(type(self.state), 'component').get_choices(self.state)

        self.ui.list_component.clear()

        for component in components:

            if isinstance(component, ChoiceSeparator):
                item = QListWidgetItem(str(component))
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                item.setForeground(Qt.gray)
            else:
                item = QListWidgetItem(component.label)
                if self.default_components is not None:
                    if component in self.default_components:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            self.ui.list_component.addItem(item)

    def _on_check_change(self, *event):

        any_checked = False

        for idx in range(self.ui.list_component.count()):
            item = self.ui.list_component.item(idx)
            if item.checkState() == Qt.Checked:
                any_checked = True
                break

        self.button_ok.setEnabled(any_checked)

    def select_none(self, *event):
        self._set_all_checked(False)

    def select_all(self, *event):
        self._set_all_checked(True)

    def _set_all_checked(self, check_state):
        for idx in range(self.ui.list_component.count()):
            item = self.ui.list_component.item(idx)
            item.setCheckState(Qt.Checked if check_state else Qt.Unchecked)

    def _apply(self, do_dialog=True):
        components = []
        for idx in range(self.ui.list_component.count()):
            item = self.ui.list_component.item(idx)
            if item.checkState() == Qt.Checked:
                components.append(self.state.data.id[item.text()])
        if self.state.subset is None:
            data = self.state.data
        else:
            data = self.state.subset
        self.extract_data(data, self.state.dc, components=components,
                          rows=self.state.row, col_title=self.state.col_names)

    def extract_data(self, data, data_collection, components=[], rows=[], col_title=""):

        column_names = [x.label for x in components]
        row_names = data[rows]
        values = np.vstack([data[comp] for comp in components])
        y_cats = np.array([column_names for x in range(values.shape[1])]).T
        x_cats = np.array([row_names for x in range(values.shape[0])])
        new_data = Data(values=values,
                        y_cats=y_cats,
                        x_cats=x_cats,
                        label=f'Matrix from {data.label}',
                        coords=HeatmapCoordinates(row_names, column_names, 
                           rows.label, col_title))
        data_collection.append(new_data)

        #row_link = LinkSame(new_data.id['x_cats'], data.id[rows] )
        if isinstance(data, BaseData):
            pass
        else:
            data = data.data
        row_link = JoinLink(cids1=[new_data.id['x_cats']], cids2=[data.id[rows]],
                            data1=new_data, data2=data)
        data_collection.add_link(row_link)


    @classmethod
    def create_matrix(cls, collect, default_data=None, default_components=None,
                      default_row=None, default_col_names=None, parent=None):
        self = cls(collect, parent=parent, default_data=default_data,
                   default_components=default_components, default_row=default_row, default_col_names=default_col_names)
        value = self.exec_()

        if value == QDialog.Accepted:
            self._apply()

if __name__ == "__main__":

    from glue.core import DataCollection, Data
    from glue.utils.qt import get_qapp

    data1 = Data(genes=['g1','g2','g3','g4'], A=[1, 2, 3, 4], B=[2, 3, 4, 5], C=[4, 5, 6, 7], label='data1')
    data2 = Data(a=[1, 2, 3], b=[2, 3, 4], label='data2')

    dc = DataCollection([data1, data2])
    
    state1 = data1.id['genes'] == 'g2'
    state2 = data1.id['genes'] == 'g3'
    state = state1 | state2
    subset_group = dc.new_subset_group('g2|g3', state)
    app = get_qapp()

    dialog = ExtractToMatrixDialog(dc, default=data1)
    value = dialog.exec_()
    if value == QDialog.Accepted:
        dialog._apply()
