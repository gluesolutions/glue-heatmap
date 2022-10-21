from glue.config import viewer_tool
from glue.viewers.common.tool import CheckableTool
import seaborn as sns
import copy
import pandas as pd
import numpy as np
from glue.core.component_id import ComponentID, PixelComponentID

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
        
        #self._original_data = copy.deepcopy(data)

        g = sns.clustermap(data['values']) #This should not be hard coded... I guess it should come from state
        new_row_ind = g.dendrogram_row.reordered_ind
        new_col_ind = g.dendrogram_col.reordered_ind
        
        orig_xticks = data.coords._x_tick_names
        orig_yticks = data.coords._y_tick_names

        new_xticks = [orig_xticks[i] for i in new_col_ind]
        new_yticks = [orig_yticks[i] for i in new_row_ind]

        data.coords._x_tick_names = np.array(new_xticks)
        data.coords._y_tick_names = np.array(new_yticks)
        
        for component in data.components:
            if not isinstance(component, PixelComponentID):  # Ignore pixel components
                data.update_components({component:pd.DataFrame(data.get_data(component)).iloc[new_row_ind,new_col_ind]})
        
        self.viewer._update_axes()


    def close(self):
        if hasattr(self.viewer, 'window_closed'):
            self.viewer.window_closed.disconnect(self._do_close)
        self.viewer = None

    def deactivate(self):
        """
        """
        pass
        #self.viewer.state.reference_data 