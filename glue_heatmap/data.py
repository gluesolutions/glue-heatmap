from glue.core.data import Data


class HeatmapData(Data):
    def __init__(self, label='', coords=None, **kwargs):
        super().__init__(label=label, coords=coords, **kwargs)

    def get_mask(self, subset_state, view=None):
        """
        This is a bit of a hack. Because we have join_on_keys on both
        dimensions of the main array, Data.get_mask() will normally
        default to trying get_mask_with_key_joins. By not 
        allowing that we prevent subsets on one axis traveling
        through the array
        """
        return subset_state.to_mask(self,view=view)
