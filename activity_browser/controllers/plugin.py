# -*- coding: utf-8 -*-
from PySide2.QtCore import QObject, Slot

from ..ui.wizards.plugin_import_wizard import PluginImportWizard
from ..signals import signals


class PluginController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent

        signals.import_plugin.connect(self.import_plugin_wizard)

    @Slot(name="openImportWizard")
    def import_plugin_wizard(self) -> None:
        """Start the plugin importation wizard."""
        wizard = PluginImportWizard(self.window)
        wizard.show()

