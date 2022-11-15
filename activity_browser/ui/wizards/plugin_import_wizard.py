# -*- coding: utf-8 -*-
from pathlib import Path
import py7zr
import importlib
import sys

import brightway2 as bw
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Signal, Slot

from ...signals import signals
from ..style import style_group_box
from ...settings import project_settings


class PluginImportWizard(QtWidgets.QWizard):
    LOCATE = 1
    CONFIRM = 2
    IMPORT = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plugin Import Wizard")
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Construct and bind pages.
        self.locate_page = LocatePage(self)
        self.confirmation_page = ConfirmationPage(self)
        self.import_page = ImportPage(self)

        self.setPage(self.LOCATE, self.locate_page)
        self.setPage(self.CONFIRM, self.confirmation_page)
        self.setPage(self.IMPORT, self.import_page)
        self.setStartId(self.LOCATE)

        # with this line, finish behaves like cancel and the wizard can be reused
        # db import is done when finish button becomes active
        self.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.cleanup)

        # thread management
        self.button(QtWidgets.QWizard.CancelButton).clicked.connect(self.cancel_thread)
        self.button(QtWidgets.QWizard.CancelButton).clicked.connect(self.cancel_extraction)

        import_signals.connection_problem.connect(self.show_info)
        import_signals.import_failure.connect(self.show_info)
        import_signals.import_failure_detailed.connect(self.show_detailed)

    def closeEvent(self, event):
        """ Close event now behaves similarly to cancel, because of self.reject.

        This allows the import wizard to be reused, ie starts from the beginning
        """
        self.cancel_thread()
        self.cancel_extraction()
        event.accept()

    def cancel_thread(self):
        print('\nPlugin import interrupted!')
        import_signals.cancel_sentinel = True
        self.cleanup()

    def cancel_extraction(self):
        process = getattr(self.extractor, "extraction_process", None)
        if process is not None:
            process.kill()
            process.communicate()

    def cleanup(self):
        if self.import_page.main_worker_thread.isRunning():
            self.import_page.main_worker_thread.exit(1)
        self.import_page.complete = False
        self.reject()

    @Slot(tuple, name="showMessage")
    def show_info(self, info: tuple) -> None:
        title, message = info
        QtWidgets.QMessageBox.information(self, title, message)

    @Slot(object, tuple, name="showDetailedMessage")
    def show_detailed(self, icon: QtWidgets.QMessageBox.Icon, data: tuple) -> None:
        title, message, *other = data
        msg = QtWidgets.QMessageBox(
            icon, title, message, QtWidgets.QMessageBox.Ok, self
        )
        if other:
            other = other[0] if len(other) == 1 else other
            msg.setDetailedText("\n\n".join(str(e) for e in other))
        msg.exec_()


class LocatePage(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.wizard: QtWidgets.QWizard = parent
        self.path = QtWidgets.QLineEdit()
        self.registerField("plugin_path*", self.path)
        self.name = QtWidgets.QLineEdit()
        self.registerField("plugin_name*", self.name)
        self.path.setReadOnly(True)
        self.path.textChanged.connect(self.changed)
        self.path_btn = QtWidgets.QPushButton("Browse")
        self.path_btn.clicked.connect(self.browse)
        self.complete = False

        option_box = QtWidgets.QGroupBox("Import plugin file:")
        grid_layout = QtWidgets.QGridLayout()
        layout = QtWidgets.QVBoxLayout()
        grid_layout.addWidget(QtWidgets.QLabel("Path to file"), 0, 0, 1, 1)
        grid_layout.addWidget(self.path, 0, 1, 1, 2)
        grid_layout.addWidget(self.path_btn, 0, 3, 1, 1)
        option_box.setLayout(grid_layout)
        option_box.setStyleSheet(style_group_box.border_title)
        layout.addWidget(option_box)
        self.setLayout(layout)

        # Register field to ensure user cannot advance without selecting file.
        self.registerField("import_path*", self.path)

    def initializePage(self):
        self.path.clear()

    def nextId(self):
        self.setField("plugin_path", self.path.text())
        # set plugin_name
        filename = Path(self.field("plugin_path")).name
        plugin_name = '.'.join(filename.split('.')[:-1])
        self.setField("plugin_name", plugin_name)
        return PluginImportWizard.CONFIRM

    @Slot(name="browseFile")
    def browse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self, caption="Select a valid .plugin file",
            filter="Plugin (*.plugin);; All Files (*.*)"
        )
        if path:
            self.path.setText(path)

    @Slot(name="pathChanged")
    def changed(self) -> None:
        path = Path(self.path.text())
        exists = path.is_file()
        valid = path.suffix.lower() in {".plugin"}
        if exists and not valid:
            import_signals.import_failure.emit(
                ("Invalid extension", "Expecting plugin file to have '.plugin' extension")
            )
        self.complete = all([exists, valid])
        self.completeChanged.emit()

    def isComplete(self):
        return self.complete


class ConfirmationPage(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wizard = parent
        self.setCommitPage(True)
        self.setButtonText(QtWidgets.QWizard.CommitButton, 'Import Plugin')
        self.current_project_label = QtWidgets.QLabel('empty')
        self.plugin_name_label = QtWidgets.QLabel('empty')
        self.path_label = QtWidgets.QLabel('empty')

        layout = QtWidgets.QVBoxLayout()
        box = QtWidgets.QGroupBox("Import Summary:")
        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addWidget(self.current_project_label)
        box_layout.addWidget(self.plugin_name_label)
        box_layout.addWidget(self.path_label)
        box.setLayout(box_layout)
        box.setStyleSheet(style_group_box.border_title)
        layout.addWidget(box)
        self.setLayout(layout)

    def initializePage(self):
        self.current_project_label.setText(
            'Current Project: <b>{}</b>'.format(bw.projects.current))
        self.plugin_name_label.setText(
            'Name of the plugin: <b>{}</b>'.format(
                self.field('plugin_name')))
        self.path_label.setText(
            'Path to .plugin file:<br><b>{}</b>'.format(
                self.field('plugin_path')))

    def validatePage(self):
        """
        while a worker thread is running, it's not possible to proceed to the import page.
        this is required because there is only one sentinel value for canceled imports
        """
        running = self.wizard.import_page.main_worker_thread.isRunning()
        return not running

    def nextId(self):
        return PluginImportWizard.IMPORT


class ImportPage(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFinalPage(True)
        self.wizard = parent
        self.complete = False
        self.relink_data = {}

        layout = QtWidgets.QVBoxLayout()

        self.unarchive_label = QtWidgets.QLabel('Decompressing the 7z archive:')
        self.unarchive_progressbar = QtWidgets.QProgressBar()
        self.finalizing_label = QtWidgets.QLabel('Finalizing:')
        self.finalizing_progressbar = QtWidgets.QProgressBar()
        self.finished_label = QtWidgets.QLabel('')

        layout.addWidget(self.unarchive_label)
        layout.addWidget(self.unarchive_progressbar)
        layout.addWidget(self.finalizing_label)
        layout.addWidget(self.finalizing_progressbar)
        layout.addStretch(1)
        layout.addWidget(self.finished_label)
        layout.addStretch(1)

        self.setLayout(layout)

        # progress signals
        import_signals.unarchive_finished.connect(self.update_unarchive)
        import_signals.unarchive_failed.connect(self.report_failed_unarchive)
        import_signals.finalizing.connect(self.update_finalizing)
        import_signals.finished.connect(self.update_finished)

        # Threads
        self.main_worker_thread = MainWorkerThread(self)

    def reset_progressbars(self) -> None:
        self.finalizing_progressbar.reset()
        self.unarchive_progressbar.reset()
        self.finished_label.setText('')

    def isComplete(self):
        return self.complete

    def init_progressbars(self) -> None:
        self.unarchive_label.setVisible(1)
        self.unarchive_progressbar.setVisible(1)
        self.unarchive_progressbar.setRange(0, 0)

    def initializePage(self):
        self.reset_progressbars()
        self.init_progressbars()
        self.main_worker_thread.update(plugin_name=self.field('plugin_name'),
                                       plugin_path=self.field('plugin_path'))
        self.main_worker_thread.start()

    @Slot()
    def update_unarchive(self) -> None:
        self.unarchive_progressbar.setMaximum(1)
        self.unarchive_progressbar.setValue(1)

    @Slot()
    def update_finalizing(self) -> None:
        self.finalizing_progressbar.setRange(0, 0)

    @Slot()
    def update_finished(self, plugin, name) -> None:
        """Plugin import was successful, quit the thread and the wizard."""
        if self.main_worker_thread.isRunning():
            self.main_worker_thread.quit()
        self.finalizing_progressbar.setMaximum(1)
        self.finalizing_progressbar.setValue(1)
        self.finished_label.setText('<b>Finished!</b>')
        self.complete = True
        self.completeChanged.emit()
        signals.plugin_imported.emit(plugin, name)

    @Slot(str, name="handleUnzipFailed")
    def report_failed_unarchive(self, file: str) -> None:
        """Handle the issue where the 7z file is in some way corrupted.
         """
        self.main_worker_thread.exit(1)

        error = (
            "Corrupted (.7z) archive",
            "The archive '{}' is corrupted, please remove and re-download it.".format(file),
        )
        import_signals.import_failure_detailed.emit(
            QtWidgets.QMessageBox.Warning, error
        )
        return


class MainWorkerThread(QtCore.QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plugin_name = None
        self.plugin_path = None

    def update(self, plugin_name: str, plugin_path=None, relink=None) -> None:
        self.plugin_name = plugin_name
        self.plugin_path = plugin_path

    def run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_path:
            self.run_extract(self.plugin_path, temp_path+"/temp_plugin")
            try:
                # Import code of plugin
                sys.path.append(temp_path+"/temp_plugin")
                metadata = importlib.import_module("metadata")
                plugin_name = metadata.infos['name']
                print("NAME ="+plugin_name)
                # create plugins folder if necessary
                target_dir = bw.projects.request_directory("plugins/{}".format(plugin_name))
                # empty plugin directory
                for files in os.listdir(target_dir):
                    path = os.path.join(target_dir, files)
                    try:
                        shutil.rmtree(path)
                    except OSError:
                        os.remove(path)
                # copy plugin content into folder
                copy_tree(temp_path+"/temp_plugin", target_dir)
                # setup plugin
                sys.path.append(bw.projects.request_directory("plugins"))
                plugin_lib = importlib.import_module(plugin_name)
                self.plugin = plugin_lib.Plugin()
            except:
                import_signals.loading_failed.emit()
                import_signals.cancel_sentinel = True

        if not import_signals.cancel_sentinel:
            import_signals.import_finished.emit(self.plugin)
    
    def run_extract(self, plugin_path, target_dir) -> None:
        """Extract the given .7z archive."""
        archive = py7zr.SevenZipFile(plugin_path, mode='r')
        archive.extractall(path=target_dir)
        archive.close()
        import_signals.unarchive_finished.emit()


class ImportSignals(QtCore.QObject):
    extraction_progress = Signal(int, int)
    strategy_progress = Signal(int, int)
    finalizing = Signal()
    finished = Signal(object, str)
    unarchive_finished = Signal()
    unarchive_failed = Signal(str)
    download_complete = Signal()
    import_failure = Signal(tuple)
    import_failure_detailed = Signal(object, tuple)
    cancel_sentinel = False
    login_success = Signal(bool)
    connection_problem = Signal(tuple)
    links_required = Signal(object, object)


import_signals = ImportSignals()
