from glue.config import viewer_tool
from glue.viewers.common.tool import Tool
from qtpy import QtWidgets
from glue.core.state_objects import State
from echo.qt import autoconnect_callbacks_to_qt
from qtpy.QtWidgets import QMessageBox
import numpy as np
from glue.utils.qt import load_ui
from glue.core.data import Data
from glue_heatmap.coords import HeatmapCoordinates
from echo import SelectionCallbackProperty, CallbackProperty
from glue.core.data_combo_helper import DataCollectionComboHelper, ComponentIDComboHelper, ComboHelper, ManualDataComboHelper
import os

__all__ = ['SubsetTool', 'SubsetToDataState', 'SubsetToDataDialog']



@viewer_tool
class SubsetTool(Tool):

    icon = 'glue_spawn'
    tool_id = 'heatmap:subset'
    action_text = 'Create a new Dataset from a Subset'
    tool_tip = 'Create a new Dataset from a Subset'
    shortcut = 'Ctrl+L'

    def __init__(self, viewer):
        super().__init__(viewer)
        self._data_collection = viewer._data
        self.data = viewer.state.reference_data

    def activate(self):
        """
        Fired when the toolbar button is activated
        """

        SubsetToDataDialog.make_subset(self.viewer.state.reference_data, self._data_collection,
                                        default=None, parent=None)

    def close(self):
        if hasattr(self.viewer, 'window_closed'):
            self.viewer.window_closed.disconnect(self._do_close)
        self.viewer = None

def dialog(title, text, icon):
    if icon=='warn':
        icon = QMessageBox.Warning
    elif icon=='info':
        icon = QMessageBox.Information
    info = QMessageBox()
    info.setIcon(icon)
    info.setText(title)
    info.setInformativeText(text)
    info.setStandardButtons(info.Ok)
    result = info.exec_()
    return True


class SubsetToDataState(State):
    subset = SelectionCallbackProperty() # Required: a subset that can be applied to data

    def __init__(self, data, data_collection):
        super().__init__()
        
        self.data = data
        self.data_collection = data_collection
        self.subset_helper = ComboHelper(self, 'subset')

        def display_func_label(subset_group):
            return subset_group.label
                
        self.subset_helper.choices = data_collection.subset_groups
        try:
            self.subset_helper.selection = data_collection.subset_groups[0]
        except IndexError:
            pass
        self.subset_helper.display = display_func_label
        

    def _on_data_change(self, *args, **kwargs):
        pass

def get_extract_method(first_comp, mask):
    mm = np.ma.MaskedArray(first_comp, mask=mask)
    comp_cols = np.ma.compress_cols(mm)
    if comp_cols.size != 0:
        return "comp_cols"
    comp_rows = np.ma.compress_rows(mm)
    if comp_rows.size != 0:
        return "comp_rows"
    return "max_extent"

def clone_subset_into_data_object(subset):
    """
    A helper function to clone a data object

    https://stackoverflow.com/questions/39206986/numpy-get-rectangle-area-just-the-size-of-mask
    """
    new_data = Data()
    old_data = subset.data


    mask = subset.to_mask()

    i,j = np.where(mask)

    first_comp = old_data.main_components[0]
    method = get_extract_method(old_data[first_comp], ~mask)

    if method == 'max_extent':
        indices = np.meshgrid(np.arange(min(i), max(i) + 1),
                              np.arange(min(j), max(j) + 1),
                              indexing='ij')
        for component in old_data.main_components:
            new_data.add_component(old_data[component][tuple(indices)],label=component.label)
    elif method == 'comp_rows':
        for component in old_data.main_components:
            mm = np.ma.MaskedArray(old_data[component], mask = ~mask)
            comp_rows = np.ma.compress_rows(mm)
            new_data.add_component(comp_rows,label=component.label)
    elif method == 'comp_cols':
        for component in old_data.main_components:
            mm = np.ma.MaskedArray(old_data[component], mask = ~mask)
            comp_cols = np.ma.compress_cols(mm)
            new_data.add_component(comp_cols,label=component.label)

    if old_data.coords:
        new_y_ticks = old_data.coords._y_tick_names[np.unique(i)]
        new_x_ticks = old_data.coords._x_tick_names[np.unique(j)]
        new_data.coords = HeatmapCoordinates(new_x_ticks, new_y_ticks, old_data.coords._x_tick_label, old_data.coords._y_tick_label)

    new_data.label = f'{old_data.label} | {subset.label}'
    return new_data

class SubsetToDataDialog(QtWidgets.QDialog):
    def __init__(self, data, collect, default=None, parent=None):
        super().__init__(parent=parent)

        self.state = SubsetToDataState(data, collect)

        self.ui = load_ui('subset_to_data.ui', self,
                          directory=os.path.dirname(__file__))
        self._connections = autoconnect_callbacks_to_qt(self.state, self.ui)

        self._collect = collect

        if default is not None:
            self.state.data = default

        self.ui.button_ok.clicked.connect(self.accept)
        self.ui.button_cancel.clicked.connect(self.reject)


    def _apply(self, do_dialog=True):
        """
        """
        if self.state.subset is not None:
            for subset in self.state.subset.subsets:
                if subset.data == self.state.data:
                    target_subset = subset

        results_data = clone_subset_into_data_object(target_subset)
        self._collect.append(results_data)
        
        if do_dialog:
            confirm = dialog('New dataset created',
                    f'The Dataset:\n'
                    f'{results_data.label}\n'
                    f'has been created.',
                    'info')

    @classmethod
    def make_subset(cls, data, collect, default=None, parent=None):
        self = cls(data, collect, parent=parent, default=default)
        value = self.exec_()

        if value == QtWidgets.QDialog.Accepted:
            self._apply()