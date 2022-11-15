from PySide2 import QtCore, QtWidgets

from ..panels import ABTab
from ...signals import signals

class PluginTab(ABTab):
    """Parent class of every main plugin tab"""
    def __init__(self, plugin, panel, parent=None):
        super(PluginTab, self).__init__(parent)
        self.panel = panel
        self.plugin = plugin
        self.isPlugin = True
        self.setTabsClosable(True)