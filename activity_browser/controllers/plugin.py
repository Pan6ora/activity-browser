# -*- coding: utf-8 -*-
from PySide2.QtCore import QObject, Slot

from ..ui.wizards.plugin_import_wizard import PluginImportWizard
from ..signals import signals
from ..settings import project_settings, ab_settings


class PluginController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = parent
        # Currently loaded plugins objects as:
        # {plugin_name: <plugin_object>, ...}
        self.plugins = {}

        signals.import_plugin.connect(self.import_plugin_wizard)

        self.connect_signals()

    def connect_signals(self):
        signals.project_selected.connect(self.reload_plugins)
        signals.plugin_selected.connect(self.add_plugin)
        signals.plugin_deselected.connect(self.remove_plugin)

    @Slot(name="openImportWizard")
    def import_plugin_wizard(self) -> None:
        """Start the plugin importation wizard."""
        wizard = PluginImportWizard(self.window)
        wizard.show()
    
    def import_plugin(self, name):
        """ load given plugin package and return Plugin instance
        """
        try:
            plugins_dir = ab_settings.plugins_dir
            plugin_lib = importlib.import_module(name, plugins_dir)
            importlib.reload(plugin_lib)
            print("Loading plugin {}".format(name))
            return plugin_lib.Plugin()
        except:
            print("Error: Import of plugin {} failed".format(name))
            print(traceback.format_exc())

    def remove_plugin(self, name):
        # Apply plugin's remove() function
        self.plugins[name].remove()
        # Close plugin tabs
        self.close_plugin_tabs(name)
        # Remove plugin object for plugins dict
        self.plugins.pop(name)

    def add_plugin(self, name):
        """ add or reload tabs of the given plugin
        """
        self.close_plugin_tabs(name)
        plugin = self.import_plugin(name)
        plugin.load()
        self.plugins[name] = plugin
        for tab in plugin.tabs:
            self.add_tab_to_panel(tab, plugin.infos["name"], tab.panel)

    def reload_plugins(self):
        """ close all plugins tabs then import all plugins tabs
        """
        sys.path.append(ab_settings.plugins_dir)
        for name in project_settings.get_plugins_list():
            self.add_plugin(name)

    def close_plugin_tabs(self, plugin):
        for panel in (self.left_panel, self.right_panel):
            panel.close_plugin(plugin)

    def close_plugins(self):
        for plugin in self.plugins:
            plugin.close()