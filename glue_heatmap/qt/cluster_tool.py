from glue.config import viewer_tool
from glue.viewers.common.tool import CheckableTool, Tool
import seaborn as sns
import pandas as pd
import numpy as np

#@viewer_tool
#class UnClusterTool(Tool):
#    icon = 'glue_unlink'
#    tool_id = 'heatmap:uncluster'
#    action_text = 'Undo hierarchical clustering'
#    tool_tip = 'Undo hierarchical clustering'
#    shortcut = 'Ctrl+L'

#    def __init__(self, viewer):
#        super().__init__(viewer)

@viewer_tool
class ClusterTool(Tool):

    icon = 'glue_tree'
    tool_id = 'heatmap:cluster'
    action_text = 'Apply hierarchical clustering to matrix'
    tool_tip = 'Apply hierarchical clustering to matrix'
    shortcut = 'Ctrl+K'

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
        self.clustered = True


    def close(self):
        if self.clustered:
            self.deactivate()
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
        self.clustered = False
