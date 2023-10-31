import os

from qtpy import QtWidgets

from echo.qt import autoconnect_callbacks_to_qt
from glue_qt.utils import load_ui, fix_tab_widget_fontsize
from glue_qt.viewers.image.slice_widget import MultiSliceWidgetHelper
from glue.viewers.matplotlib.state import MatplotlibDataViewerState

__all__ = ["HeatmapOptionsWidget"]


class HeatmapOptionsWidget(QtWidgets.QWidget):
    def __init__(self, viewer_state, session, parent=None):
        super().__init__(parent=parent)

        self.ui = load_ui(
            "options_widget.ui", self, directory=os.path.dirname(__file__)
        )

        fix_tab_widget_fontsize(self.ui.tab_widget)

        self._connections = autoconnect_callbacks_to_qt(viewer_state, self.ui)
        self._connections_axes = autoconnect_callbacks_to_qt(
            viewer_state, self.ui.axes_editor.ui
        )
        connect_kwargs = {"alpha": dict(value_range=(0, 1))}
        self._connections_legend = autoconnect_callbacks_to_qt(
            viewer_state.legend, self.ui.legend_editor.ui, connect_kwargs
        )

        self.viewer_state = viewer_state

        # TODO: Excise this
        self.slice_helper = MultiSliceWidgetHelper(
            viewer_state=self.viewer_state, layout=self.ui.layout_slices
        )

        self.session = session
        self.ui.axes_editor.button_apply_all.clicked.connect(self._apply_all_viewers)

    def _apply_all_viewers(self):
        for tab in self.session.application.viewers:
            for viewer in tab:
                if isinstance(viewer.state, MatplotlibDataViewerState):
                    viewer.state.update_axes_settings_from(self.viewer_state)
