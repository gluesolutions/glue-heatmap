from glue.config import viewer_tool
from glue.viewers.common.tool import CheckableTool
from glue_qt.viewers.common.toolbar import BasicToolbar
import seaborn as sns
import numpy as np


@viewer_tool
class ToggleTool(CheckableTool):
    """
    A tool that sets some persistant property of a viewer
    that persists until explicitly unchecked.
    """


class ToggleToolbar(BasicToolbar):
    """
    A toolbar that allows for ToggleTool buttons
    """

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
            self.deactivate_tool(old_tool) # This only disables CheckableTools
            if isinstance(old_tool, CheckableTool):
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
            if isinstance(new_tool, ToggleTool):
                button = self.actions[new_tool.tool_id]
                if not button.isChecked():
                    button.blockSignals(True)
                    button.setChecked(True)
                    button.blockSignals(False)

        if isinstance(new_tool, CheckableTool):
            self._active_tool = new_tool
            self.parent().set_status(new_tool.status_tip)
            self.tool_activated.emit()
        elif isinstance(new_tool, ToggleTool):
            self._active_tool = new_tool
            self.parent().set_status(new_tool.status_tip)
            self.tool_activated.emit()
        else:
            self.parent().set_status('')
            self.tool_deactivated.emit()



# @viewer_tool
# class UnClusterTool(Tool):
#    icon = 'glue_unlink'
#    tool_id = 'heatmap:uncluster'
#    action_text = 'Undo hierarchical clustering'
#    tool_tip = 'Undo hierarchical clustering'
#    shortcut = 'Ctrl+L'

#    def __init__(self, viewer):
#        super().__init__(viewer)


@viewer_tool
class ClusterTool(ToggleTool):
    icon = "glue_tree"
    tool_id = "heatmap:cluster"
    action_text = "Apply hierarchical clustering to matrix"
    tool_tip = "Apply hierarchical clustering to matrix"
    shortcut = "Ctrl+K"

    def __init__(self, viewer):
        super().__init__(viewer)
        self.clustered = False

    def activate(self):
        """
        We use seaborn.clustermap to cluster the data and then
        use the indices returned from this method to update the
        dataset
        """
        if self.clustered:
            self.deactivate()
            return
        data = self.viewer.state._heatmap_data
        orig_xticks = self.viewer.state._x_categories
        orig_yticks = self.viewer.state._y_categories

        self.orig_coords = (orig_xticks, orig_yticks)
        self.orig_data = data
        g = sns.clustermap(data)
        new_row_ind = g.dendrogram_row.reordered_ind
        new_col_ind = g.dendrogram_col.reordered_ind

        new_xticks = [orig_xticks[i] for i in new_col_ind]
        new_yticks = [orig_yticks[i] for i in new_row_ind]

        new_data = data[new_row_ind, :][:, new_col_ind]
        self.viewer.state._heatmap_data = new_data
        self.viewer.state._x_categories = np.array(new_xticks)
        self.viewer.state._y_categories = np.array(new_yticks)

        self.viewer._update_axes()
        self.clustered = True

    def close(self):
        if self.clustered:
            self.deactivate()
        if hasattr(self.viewer, "window_closed"):
            self.viewer.window_closed.disconnect(self._do_close)
        self.viewer = None

    def deactivate(self):
        """
        On deactivate restore the dataset to how it was before.
        This is a little fragile because we could have multiple Heatmap viewers
        of the same dataset.
        """
        print("Calling deactivate...")
        #import pdb; pdb.set_trace()
        #data = self.viewer.state.reference_data
        #for label, component in self.original_components.items():
        #    data.update_components({data.id[label]: component})
        self.viewer.state._heatmap_data = self.orig_data
        self.viewer.state._x_categories = self.orig_coords[0]
        self.viewer.state._y_categories = self.orig_coords[1]
        self.viewer._update_axes()
        self.clustered = False
