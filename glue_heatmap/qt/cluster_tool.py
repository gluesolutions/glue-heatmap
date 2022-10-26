from glue.config import viewer_tool
from glue.viewers.common.tool import CheckableTool
from glue.viewers.common.qt.toolbar import BasicToolbar
import seaborn as sns
import pandas as pd
import numpy as np


class ClusterToolbar(BasicToolbar):
    def __init__(self, parent, default_mouse_mode_cls=None):
        super().__init__(parent, default_mouse_mode_cls)

    def deactivate_tool(self, tool):
        if isinstance(tool, CheckableTool):
            if not isinstance(tool, ClusterTool):
                tool.deactivate()
        if self._default_mouse_mode is not None:
            self._default_mouse_mode.activate()

    @property
    def active_tool(self):
        return self._active_tool

    @active_tool.setter
    def active_tool(self, new_tool):

        if isinstance(new_tool, str):
            if new_tool in self.tools:
                new_tool = self.tools[new_tool]
            else:
                raise ValueError("Unrecognized tool '{0}', should be one of {1}"
                                 .format(new_tool, ", ".join(sorted(self.tools))))

        old_tool = self._active_tool

        # If the tool is as before, we don't need to do anything
        if old_tool is new_tool:
            return

        # Otheriwse, if the tool changes, then we need to disable the previous
        # tool...
        if old_tool is not None:
            self.deactivate_tool(old_tool)
            if isinstance(old_tool, CheckableTool) and not isinstance(old_tool, ClusterTool):
                button = self.actions[old_tool.tool_id]
                if button.isChecked():
                    button.blockSignals(True)
                    button.setChecked(False)
                    button.blockSignals(False)

        # We need to then set that no tool is set so that if the next tool
        # opens a viewer that needs to check whether a tool is active, we
        # know that it isn't.
        self._active_tool = None

        # ... and enable the new one
        if new_tool is not None:
            self.activate_tool(new_tool)
            if isinstance(new_tool, CheckableTool):
                button = self.actions[new_tool.tool_id]
                if not button.isChecked():
                    button.blockSignals(True)
                    button.setChecked(True)
                    button.blockSignals(False)

        if isinstance(new_tool, CheckableTool):
            self._active_tool = new_tool
            self.parent().set_status(new_tool.status_tip)
            self.tool_activated.emit()
        else:
            self.parent().set_status('')
            self.tool_deactivated.emit()


@viewer_tool
class ClusterTool(CheckableTool):

    icon = 'glue_tree'
    tool_id = 'heatmap:cluster'
    action_text = 'Apply hierarchical clustering to matrix'
    tool_tip = 'Apply hierarchical clustering to matrix'
    shortcut = 'Ctrl+K'

    def __init__(self, viewer):
        super().__init__(viewer)


    def activate(self):
        """
        We use seaborn.clustermap to cluster the data and then
        use the indices returned from this method to update the
        dataset
        """
        data = self.viewer.state.reference_data
        orig_xticks = data.coords._x_tick_names
        orig_yticks = data.coords._y_tick_names
        
        self.original_components = {}
        for component in data.main_components:
            self.original_components[component.label] = data.get_data(component)
        self.orig_coords = (orig_xticks, orig_yticks)

        g = sns.clustermap(data['values']) #This should not be hard coded... I guess it should come from state
        new_row_ind = g.dendrogram_row.reordered_ind
        new_col_ind = g.dendrogram_col.reordered_ind
        

        new_xticks = [orig_xticks[i] for i in new_col_ind]
        new_yticks = [orig_yticks[i] for i in new_row_ind]

        data.coords._x_tick_names = np.array(new_xticks)
        data.coords._y_tick_names = np.array(new_yticks)
        
        for component in data.main_components:
            data.update_components({component:pd.DataFrame(data.get_data(component)).iloc[new_row_ind,new_col_ind]})
        
        self.viewer._update_axes()


    def close(self):
        if hasattr(self.viewer, 'window_closed'):
            self.viewer.window_closed.disconnect(self._do_close)
        self.viewer = None

    def deactivate(self):
        """
        On deactivate restore the dataset to how it was before.
        This is a little fragile because we could have multiple Heatmap viewers
        of the same dataset.
        """
        data = self.viewer.state.reference_data
        for label, component in self.original_components.items():
            data.update_components({data.id[label]:component})
        data.coords._x_tick_names = self.orig_coords[0]
        data.coords._y_tick_names = self.orig_coords[1]
        self.viewer._update_axes()

        #self.viewer.state.reference_data 