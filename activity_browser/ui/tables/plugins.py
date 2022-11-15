# -*- coding: utf-8 -*-
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Slot

from ...settings import project_settings
from ...signals import signals
from ..icons import qicons
from .delegates import CheckboxDelegate
from .models.plugins import PluginsModel
from .views import ABDataFrameView

class PluginsTable(ABDataFrameView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.verticalHeader().setVisible(False)
        self.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Maximum
        ))
        self.model = PluginsModel(parent=self)
        self._connect_signals()

    def _connect_signals(self):
        self.model.updated.connect(self.update_proxy_model)
        self.model.updated.connect(self.custom_view_sizing)

    def contextMenuEvent(self, event) -> None:
        if self.indexAt(event.pos()).row() == -1:
            return

        menu = QtWidgets.QMenu(self)
        menu.addAction(
            qicons.delete, "Remove plugin",
            lambda: signals.remove_plugin.emit(self.selected_plugin)
        )
        menu.exec_(event.globalPos())

    @property
    def selected_plugin(self) -> str:
        """ Return the plugin name of the user-selected index.
        """
        return self.model.get_plugin(self.currentIndex())