from glue.core import BaseData

from glue.viewers.image.state import (
    ImageViewerState,
    ImageLayerState,
    ImageSubsetLayerState,
    BaseImageLayerState
)
from glue.viewers.matplotlib.state import (DeferredDrawSelectionCallbackProperty as DDSCProperty,
                                           DeferredDrawCallbackProperty as DDCProperty)

from glue.core.data_combo_helper import ComboHelper
from glue.core.exceptions import IncompatibleDataException
from glue.utils import unbroadcast
from glue.core.fixed_resolution_buffer import bounds_for_cache
from glue.core.exceptions import IncompatibleAttribute
from echo import delay_callback
from scipy.cluster import hierarchy
import fastcluster

import numpy as np

__all__ = ["HeatmapViewerState", "HeatmapLayerState", "HeatmapSubsetLayerState"]


class HeatmapViewerState(ImageViewerState):
    """
    A state class that includes all the attributes for a Heatmap Viewer.

    A HeatmapViewer will ultimately be able to display both a 2D matrix
    of values (for a dataset with HeatmapCoordinates) and a heatmap generated
    from 1D tabular data. For now, we have focused on the 2D matrix case.
    """
#    reference_data = DDSCProperty(docstring='The dataset that is used to define the '
#                                             'available x_agg and y_agg components as '
#                                             'well as the subsets to display')
#    rows = DDSCProperty(docstring='The component ID in reference_data that will be '
#                                   'displayed as the rows of the heatmap.')
#    cols = DDSCProperty(docstring='The component ID in reference_data that will be '
#                                     'displayed as the columns of the heatmap.')
#
#    aggregation = DDSCProperty(docstring='The aggregation function to apply'
#                                             'on values to generate the heatmap.'
#                                             'Must be count if values is None.')
#    values = DDSCProperty(docstring='The component ID in reference_data that will be '
#                                     'aggregated over to generate the heatmap. If None, '
#                                     'the count of each row/col combination is used.')
    row_subset = DDSCProperty(docstring='The subset to use for filtering rows')
    col_subset = DDSCProperty(docstring='The subset to use for filtering columns')

    cluster = DDCProperty(False, docstring='Whether to cluster the histogram')

    def __init__(self, **kwargs):
        super().__init__()
        HeatmapViewerState.aspect.set_choices(self, ["auto"])
        self._heatmap_data = None
        self.row_subset_helper = ComboHelper(self, "row_subset")
        self.col_subset_helper = ComboHelper(self, "col_subset")

        def display_func(subset):
            if subset is None:
                return "None"
            else:
                return subset.label

        self.row_subset_helper.choices = [None]
        self.col_subset_helper.choices = [None]
        self.row_subset_helper.display = display_func
        self.col_subset_helper.display = display_func

        self.add_callback('row_subset', self._update_selected_subset, echo_old=True)
        self.add_callback('col_subset', self._update_selected_subset, echo_old=True)
        self.add_callback('cluster', self._do_cluster)
        self._x_categories = []
        self._y_categories = []

        if self.reference_data is not None:
            self._caculate_heatmap_data()

    @property
    def x_categories(self):
        return np.asarray(self._x_categories)

    @property
    def y_categories(self):
        return np.asarray(self._y_categories)

    def _update_selected_subset(self, before=None, after=None, **kwargs):
        """
        Callback for changing the selected subsets for filtering row/col.

        As long as the subset has actually changed, we need to recalculate
        the heatmap data.
        """
        # A callback event for row/col_subset may be triggered if the choices
        # change but the actual selection doesn't - so we avoid doing anything in
        # this case.
        if after is before:
            return
        # We make a subset not visible if it is the one that we use to subset
        # the data, because the subset mask is just the whole data in that
        # case. The user can toggle it back on if they want to.
        for layer in self.layers:
            if not isinstance(layer.layer, BaseData):
                if layer.layer is after:
                    layer.visible = False
                if layer.layer is before:
                    layer.visible = True
        self._calculate_heatmap_data()

    def _calculate_heatmap_data(self, *args, **kwargs):
        """
        Call this to recalculate the heatmap data if reference_data, row_subset, or
        col_subset changes. In the 1D case this will also be called if rows, cols,
        aggregation or values changes.

        If we are recalculating the heatmap, then we disable clustering (since the
        old clustering is not necessarily valie for the new data array and we want
        it to be obvious to the user that they need to recluster).
        """
        self.cluster = False
        self._heatmap_data = self.reference_data[self.reference_data.main_components[0]]
        self.rows_included = np.arange(self._heatmap_data.shape[0])
        self.cols_included = np.arange(self._heatmap_data.shape[1])

        if self.row_subset is not None:
            try:
                unraveled_indices = np.unravel_index(self.row_subset.to_index_list(), self.reference_data.shape)
                self.rows_included = np.unique(unraveled_indices[0])
            except IncompatibleAttribute:
                pass
        if self.col_subset is not None:
            try:
                unraveled_indices = np.unravel_index(self.col_subset.to_index_list(), self.reference_data.shape)
                self.cols_included = np.unique(unraveled_indices[1])
            except IncompatibleAttribute:
                pass

        self._x_categories = self.reference_data.coords.get_tick_labels("x")[self.cols_included]
        self._y_categories = self.reference_data.coords.get_tick_labels("y")[self.rows_included]
        self._heatmap_data = self._heatmap_data[self.rows_included, :][:, self.cols_included]

        self.reset_limits()

    def _set_reference_data(self):
        """
        Set the reference data for the viewer and calculate
        the heatmap and available subsets.
        """
        if self.reference_data is None:
            for layer in self.layers:
                if isinstance(layer.layer, BaseData):
                    self.reference_data = layer.layer
                    self._calculate_heatmap_data()
                    self._sync_subsets()

                    return
        elif self._heatmap_data is None:
            self._calculate_heatmap_data()
            self._sync_subsets()

    def _sync_subsets(self):
        """
        Generate a list of subsets to display as options for filtering.

        Currently, this just takes all subsets in the data collection,
        but in theory we could try to be smart and only show subsets
        that are defined on reference_data and/or show subsets that
        are meaningful for filtering rows/cols (though this is not
        necessarily well-defined).
        """
        if self.reference_data is None:
            return
        # Perhaps we should filter this list of subsets
        # in some "smart" way to be really row/col things?
        subsets = [None] + list(self.reference_data.subsets)
        self.row_subset_helper.choices = subsets
        self.col_subset_helper.choices = subsets

    def reset_limits(self):

        if self._heatmap_data is None or self.x_att is None or self.y_att is None:
            return

        nx = self._heatmap_data.shape[self.x_att.axis]
        ny = self._heatmap_data.shape[self.y_att.axis]

        with delay_callback(self, 'x_min', 'x_max', 'y_min', 'y_max'):
            self.x_min = -0.5
            self.x_max = nx - 0.5
            self.y_min = -0.5
            self.y_max = ny - 0.5
            # We need to adjust the limits in here to avoid triggering all
            # the update events then changing the limits again.
            self._adjust_limits_aspect()

    def _do_cluster(self, *args):
        """
        Apply hierarchical clustering to the heatmap data.

        We preserve the unclustered data and coordinates so that we can
        revert to the original data if the user toggles clustering off.
        """
        if self.cluster:
            data = self._heatmap_data
            orig_xticks = self._x_categories
            orig_yticks = self._y_categories

            self.orig_coords = (orig_xticks, orig_yticks)
            self.orig_data = data

            row_linkage = fastcluster.linkage_vector(data, method='ward', metric='euclidean')
            row_dendro = hierarchy.dendrogram(row_linkage, no_plot=True)
            col_linkage = fastcluster.linkage_vector(data.T, method='ward', metric='euclidean')
            col_dendro = hierarchy.dendrogram(col_linkage, no_plot=True)
            new_row_ind = row_dendro['leaves']
            new_col_ind = col_dendro['leaves']

            new_xticks = [orig_xticks[i] for i in new_col_ind]
            new_yticks = [orig_yticks[i] for i in new_row_ind]

            new_data = data[new_row_ind, :][:, new_col_ind]
            self._x_categories = np.array(new_xticks)
            self._y_categories = np.array(new_yticks)
            self.orig_included = (self.rows_included, self.cols_included)
            self.rows_included = self.rows_included[new_row_ind]
            self.cols_included = self.cols_included[new_col_ind]

            self._heatmap_data = new_data
        else:
            self._x_categories = self.orig_coords[0]
            self._y_categories = self.orig_coords[1]
            self.rows_included = self.orig_included[0]
            self.cols_included = self.orig_included[1]

            self._heatmap_data = self.orig_data


class BaseHeatmapLayerState(BaseImageLayerState):
    """
    To reuse most of the ImageViewer we simply override the get_sliced_data
    method here to return the heatmap data. We can dramatically simplify this
    to remove all the slicing stuff, although the name needs to stay the same.
    """

    def get_sliced_data(self, view=None, bounds=None):
        """
        Override BaseImageLayerState.get_sliced_data to return just the
        underlying heatmap array.
        """
        if self.viewer_state._heatmap_data is None:
            return

        full_view, agg_func, transpose = self.viewer_state.numpy_slice_aggregation_transpose

        x_axis = self.viewer_state.x_att.axis
        y_axis = self.viewer_state.y_att.axis

        # For this method, we make use of Data.compute_fixed_resolution_buffer,
        # which requires us to specify bounds in the form (min, max, nsteps).
        # We also allow view to be passed here (which is a normal Numpy view)
        # and, if given, translate it to bounds. If neither are specified,
        # we behave as if view was [slice(None), slice(None)].

        def slice_to_bound(slc, size):
            min, max, step = slc.indices(size)
            n = (max - min - 1) // step
            max = min + step * n
            return (min, max, n + 1)

        if bounds is None:

            # The view should be that which should just be applied to the data
            # slice, not to all the dimensions of the data - thus it should have at
            # most two dimensions

            if view is None:
                view = [slice(None), slice(None)]
            elif len(view) == 1:
                view = view + [slice(None)]
            elif len(view) > 2:
                raise ValueError('view should have at most two elements')

            full_view[x_axis] = view[1]
            full_view[y_axis] = view[0]

        else:

            full_view[x_axis] = bounds[1]
            full_view[y_axis] = bounds[0]

        for i in range(self.viewer_state.reference_data.ndim):
            if isinstance(full_view[i], slice):
                full_view[i] = slice_to_bound(full_view[i], self.viewer_state.reference_data.shape[i])

        # We now get the fixed resolution buffer

        if isinstance(self.layer, BaseData):
            image = compute_fixed_resolution_buffer(self.viewer_state._heatmap_data, full_view)
        else:
            image = compute_fixed_resolution_buffer(self.viewer_state._heatmap_data,
                                                    full_view, subset_state=self.layer.subset_state,
                                                    ref_state=self.viewer_state)

        # We apply aggregation functions if needed

        if agg_func is None:
            if image.ndim != 2:
                raise IncompatibleDataException()
        else:
            if image.ndim != len(agg_func):
                raise ValueError("Sliced image dimensions ({0}) does not match "
                                 "aggregation function list ({1})"
                                 .format(image.ndim, len(agg_func)))
            for axis in range(image.ndim - 1, -1, -1):
                func = agg_func[axis]
                if func is not None:
                    image = func(image, axis=axis)
            if image.ndim != 2:
                raise ValueError("Image after aggregation should have two dimensions")

        # And finally we transpose the data if the order of x/y is different
        # from the native order.

        if transpose:
            image = image.transpose()

        return image


class HeatmapLayerState(BaseHeatmapLayerState, ImageLayerState):
    """
    A state class that includes all the attributes for data layers in a Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class HeatmapSubsetLayerState(BaseHeatmapLayerState, ImageSubsetLayerState):
    """
    A state class that includes all the attributes for subset layers in Heatmap Viewer
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Is there a problem with having this here?
ARRAY_CACHE = {}
PIXEL_CACHE = {}


def compute_fixed_resolution_buffer(data, bounds, subset_state=None, ref_state=None, cache_id=None):
    """
    Get a fixed-resolution buffer for a 2D array.

    This is a replacement for glue.core.fixed_resolution_buffer.compute_fixed_resolution_buffer
    which works on a 2D numpy array and subsets associated with HeatmapViewerState objects.

    Parameters
    ----------
    data : np.ndarray
        The data array to extract a fixed-resolution buffer from.
    bounds : list
        The list of bounds for the fixed resolution buffer. This list should
        have as many items as there are dimensions in ``data``. Each
        item should either be a scalar value, or a tuple of ``(min, max, nsteps)``.
    subset_state : `~glue.core.subset.SubsetState`, optional
        If specified, a subset state to apply to the data before extracting
        the fixed resolution buffer.
    ref_state : State object,  optional
        If specified, a state object that allows us to convert a subset state
        into a mask on the heatmap
    """
    for bound in bounds:
        if isinstance(bound, tuple) and bound[2] < 1:
            raise ValueError(f"Number of steps in bounds should be >=1 but got bound={bound}")

    # If cache_id is specified, we keep a cached version of the resulting array
    # indexed by cache_id as well as a hash formed of the call arguments to this
    # function. We then check if the resulting array already exists in the cache.

    if cache_id is not None:

        # Use uuid for component ID since otherwise component IDs don't return
        # False when comparing two different CIDs (instead they return a subset state).
        # For bounds we use a special wrapper that can identify wildcards.
        current_array_hash = (data, bounds)
        current_pixel_hash = (data)

        if cache_id in ARRAY_CACHE:
            if ARRAY_CACHE[cache_id]['hash'] == current_array_hash:
                return ARRAY_CACHE[cache_id]['array']

        # To save time later, if the pixel cache doesn't match at the level of the
        # data and target_data, we just reset the cache.
        if cache_id in PIXEL_CACHE:
            if PIXEL_CACHE[cache_id]['hash'] != current_pixel_hash:
                PIXEL_CACHE.pop(cache_id)

    # Start off by generating arrays of coordinates in the original dataset
    pixel_coords = [np.linspace(*bound) if isinstance(bound, tuple) else bound for bound in bounds]
    pixel_coords = np.meshgrid(*pixel_coords, indexing='ij', copy=False)

    # Keep track of the original shape of these arrays
    original_shape = pixel_coords[0].shape

    # Now loop through the dimensions of 'data' to find the corresponding
    # coordinates in the frame of view of this dataset.

    translated_coords = []

    invalid_all = np.zeros(original_shape, dtype=bool)

    for ipix in range(data.ndim):

        # At this point, if cache_id is in PIXEL_CACHE, we know that data and
        # target_data match so we just check the bounds. Note that the bounds
        # include the AnyScalar wildcard for any dimensions that don't impact
        # the pixel coordinates here. We do this so that we don't have to
        # recompute the pixel coordinates when e.g. slicing through cubes.

        if cache_id in PIXEL_CACHE and ipix in PIXEL_CACHE[cache_id] and PIXEL_CACHE[cache_id][ipix]['bounds'] == bounds:

            translated_coord = PIXEL_CACHE[cache_id][ipix]['translated_coord']
            dimensions = PIXEL_CACHE[cache_id][ipix]['dimensions']
            invalid = PIXEL_CACHE[cache_id][ipix]['invalid']

        else:

            # The returned coordinates may often be a broadcasted array. To convert
            # the coordinates to integers and check which ones are within bounds, we
            # thus operate on the un-broadcasted array, before broadcasting it back
            # to the original shape.
            translated_coord = np.round(unbroadcast(pixel_coords[ipix])).astype(int)
            invalid = (translated_coord < 0) | (translated_coord >= data.shape[ipix])

            # Since we are going to be using these coordinates later on to index an
            # array, we need the coordinates to be within the array, so we reset
            # any invalid coordinates and keep track of which pixels are invalid
            # to reset them later.
            translated_coord[invalid] = 0

            # We now populate the cache
            if cache_id is not None:

                if cache_id not in PIXEL_CACHE:
                    PIXEL_CACHE[cache_id] = {'hash': current_pixel_hash}

                PIXEL_CACHE[cache_id][ipix] = {'translated_coord': translated_coord,
                                               'dimensions': dimensions,
                                               'invalid': invalid,
                                               'bounds': bounds_for_cache(bounds, dimensions)}

        invalid_all |= invalid

        # Broadcast back to the original shape and add to the list
        translated_coords.append(np.broadcast_to(translated_coord, original_shape))

    translated_coords = tuple(translated_coords)

    if subset_state is None:
        array = data[translated_coords].astype(float)
        invalid_value = -np.inf
    else:
        og_mask = ref_state.reference_data.get_mask(subset_state)  # This is the mask on the original data
        mask_red = og_mask[ref_state.rows_included, :][:, ref_state.cols_included]  # convert from full size to heatmap
        array = mask_red[translated_coords]  # Downsample
        invalid_value = False

    if np.any(invalid_all):
        if not array.flags.writeable:
            array = np.array(array, dtype=type(invalid_value))
        array[invalid_all] = invalid_value

    # Drop dimensions for which bounds were scalars
    slices = []
    for bound in bounds:
        if isinstance(bound, tuple):
            slices.append(slice(None))
        else:
            slices.append(0)

    array = array[tuple(slices)]

    if cache_id is not None:

        # For the bounds, we use a special wildcard for bounds that don't affect
        # the result. This will allow the cache to match regardless of the
        # value for those bounds. However, we only do this for scalar bounds.

        cache_bounds = bounds_for_cache(bounds, [0, 1])

        current_array_hash = current_array_hash[:1] + (cache_bounds,) + current_array_hash[2:]

        ARRAY_CACHE[cache_id] = {'hash': current_array_hash, 'array': array}

    return array
