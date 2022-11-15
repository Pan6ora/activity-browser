# -*- coding: utf-8 -*-
import datetime
import functools
import os

import arrow
import brightway2 as bw
from bw2data.utils import natural_sort
import numpy as np
import pandas as pd
from PySide2.QtCore import Qt, QModelIndex, Slot
from PySide2.QtWidgets import QApplication

from activity_browser.bwutils import AB_metadata, commontasks as bc
from activity_browser.settings import project_settings
from activity_browser.signals import signals
from .base import PandasModel, DragPandasModel

class PluginsModel(PandasModel):
    HEADERS = ["name", "author", "version"]

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.plugins_list = []
        signals.project_selected.connect(self.sync)
        signals.parameters_changed.connect(self.sync)
        signals.plugins_changed.connect(self.sync)      

    def get_plugin(self, proxy: QModelIndex) -> str:
        idx = self.proxy_to_source(proxy)
        return self._plugins.iat[idx.row(), 0]

    def sync(self):
        plugins = [p for p in project_settings.get_plugins().keys()]
        data = [p for p in project_settings.get_plugins().values()]
        self._plugins = pd.DataFrame(plugins, columns=["plugin"])
        self._dataframe = pd.DataFrame(data, columns=self.HEADERS)
        self.updated.emit()