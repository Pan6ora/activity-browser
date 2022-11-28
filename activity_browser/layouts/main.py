# -*- coding: utf-8 -*-
import importlib.util
import traceback
import sys
import shutil

import brightway2 as bw
from PySide2 import QtCore, QtGui, QtWidgets

from ..ui.icons import qicons
from ..ui.menu_bar import MenuBar
from ..ui.statusbar import Statusbar
from ..ui.style import header
from ..ui.utils import StdRedirector
from .panels import LeftPanel, RightPanel
from ..settings import project_settings
from ..signals import signals


class MainWindow(QtWidgets.QMainWindow):
    DEFAULT_NO_METHOD = 'No method selected yet'

    def __init__(self):
        super(MainWindow, self).__init__(None)

        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        # Window title
        self.setWindowTitle("Activity Browser")

        # Background Color
        # self.setAutoFillBackground(True)
        # p = self.palette()
        # p.setColor(self.backgroundRole(), QtGui.QColor(148, 143, 143, 127))
        # self.setPalette(p)

        # Small icon in main window titlebar
        self.icon = qicons.ab
        self.setWindowIcon(self.icon)

        # Layout
        # The top level element is `central_widget`.
        # Inside is a vertical layout `vertical_container`.
        # Inside the vertical layout is a horizontal layout `main_horizontal_box` with two elements and a
        # The enclosing element is `main_horizontal_box`, which contains the
        # left and right panels `left_panel` and `right_panel`.
        # Left (0) and right (1) panels have a default screen division, set by the setStretchfactor() commands
        # the last argument is the proportion of screen it takes up from total (so 1 and 3 gives 1/4 and 3/4)

        self.main_horizontal_box = QtWidgets.QHBoxLayout()

        self.left_panel = LeftPanel(self)
        self.right_panel = RightPanel(self)

        #Sets the minimum width for the right panel so scaling on Mac Screens doesnt go out of bounds
        self.right_panel.setMinimumWidth(100)

        self.splitter_horizontal = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter_horizontal.addWidget(self.left_panel)
        self.splitter_horizontal.addWidget(self.right_panel)
        self.splitter_horizontal.setStretchFactor(0, 1)
        self.splitter_horizontal.setStretchFactor(1, 3)
        self.main_horizontal_box.addWidget(self.splitter_horizontal)

        self.vertical_container = QtWidgets.QVBoxLayout()
        self.vertical_container.addLayout(self.main_horizontal_box)

        self.main_widget = QtWidgets.QWidget()
        self.main_widget.icon = qicons.main_window
        self.main_widget.name = "&Main Window"
        self.main_widget.setLayout(self.vertical_container)

        # Debug/working... stack
        self.log = QtWidgets.QTextEdit(self)
        sys.stdout = StdRedirector(self.log, sys.stdout, None)
        sys.stderr = StdRedirector(self.log, sys.stderr, "blue")

        working_layout = QtWidgets.QVBoxLayout()
        working_layout.addWidget(header("Program output:"))
        working_layout.addWidget(self.log)

        self.debug_widget = QtWidgets.QWidget()
        self.debug_widget.icon = qicons.debug
        self.debug_widget.name = "&Debug Window"
        self.debug_widget.setLayout(working_layout)

        self.stacked = QtWidgets.QStackedWidget()
        self.stacked.addWidget(self.main_widget)
        self.stacked.addWidget(self.debug_widget)
        self.setCentralWidget(self.stacked)

        # Layout: extra items outside main layout
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.status_bar = Statusbar(self)
        self.setStatusBar(self.status_bar)

        self.plugins = {}

        self.connect_signals()

    def closeEvent(self,event):
        for plugin in self.plugins.keys():
            print("Closing plugin {}".format(plugin))
            self.plugins[plugin].close()

    def connect_signals(self):
        # Keyboard shortcuts
        self.shortcut_debug = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+D"), self)
        self.shortcut_debug.activated.connect(self.toggle_debug_window)
        signals.reload_plugins.connect(self.reload_plugins)
        signals.project_selected.connect(self.reload_plugins)
        signals.remove_plugin.connect(self.remove_plugin)
        signals.add_plugin.connect(self.add_plugin)

    def remove_plugin(self, name):
        # Apply plugin's remove() function
        self.plugins[name].remove()
        # Close plugin tabs
        self.close_plugin_tabs(name)
        # Remove plugin object for plugins dict
        self.plugins.pop(name)
        # Remove plugin folder
        plugin_dir = bw.projects.request_directory("plugins/{}".format(name))
        shutil.rmtree(plugin_dir)
    
    def import_plugin(self, name):
        """ load given plugin package and return Plugin instance
        """
        try:
            plugins_dir = bw.projects.request_directory("plugins")
            plugin_lib = importlib.import_module(name, plugins_dir)
            importlib.reload(plugin_lib)
            print("Loading plugin {}".format(name))
            return plugin_lib.Plugin()
        except:
            print("Error: Import of plugin {} failed".format(name))
            print(traceback.format_exc())

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
        sys.path.append(bw.projects.request_directory("plugins"))
        for name in project_settings.get_plugins_list():
            self.add_plugin(name)

    def toggle_debug_window(self):
        """Toggle between any window and the debug window."""
        if self.stacked.currentWidget() != self.debug_widget:
            self.last_widget = self.stacked.currentWidget()
            self.stacked.setCurrentWidget(self.debug_widget)
            # print("Switching to debug window")
        else:
            # print("Switching back to last widget")
            if self.last_widget:
                try:
                    self.stacked.setCurrentWidget(self.last_widget)
                except:
                    print("Previous Widget has been deleted in the meantime. Switching to main window.")
                    self.stacked.setCurrentWidget(self.main_widget)
            else:  # switch to main window
                self.stacked.setCurrentWidget(self.main_widget)

    def add_tab_to_panel(self, obj, label, side):
        panel = self.left_panel if side == 'left' else self.right_panel
        panel.add_tab(obj, label)
        
    def close_plugin_tabs(self, plugin):
        for panel in (self.left_panel, self.right_panel):
            panel.close_plugin(plugin)

    def select_tab(self, obj, side):
        panel = self.left_panel if side == 'left' else self.right_panel
        panel.setCurrentIndex(panel.indexOf(obj))

    def dialog(self, title, label):
        value, ok = QtWidgets.QInputDialog.getText(self, title, label)
        if ok:
            return value

    def info(self, label):
        QtWidgets.QMessageBox.information(
            self,
            "Information",
            label,
            QtWidgets.QMessageBox.Ok,
        )

    def warning(self, title, text):
        QtWidgets.QMessageBox.warning(self, title, text)

    def confirm(self, label):
        response = QtWidgets.QMessageBox.question(
            self,
            "Confirm Action",
            label,
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )
        return response == QtWidgets.QMessageBox.Yes
