# Changelog

## [Unreleased]

## [2.7.5+pm2.0.0] - 2023-03-23

### Added

- Github deployement action to Anaconda

### Changed

- Plugins are installed through conda as packages
- Better versioning
- Better branching

### Removed

- Plugins installation buttons and wizard

### Fixed

- Plugins lib importation errors

## [2.7.5+pm1.0.0] - 2023-03-21

### Changed

- Update to Activity Browser 2.7.5

## [2.6.9+pm1.0.0] - 2022-11-30

### Added

- Confirm box when deleting/removing plugins

### Fixed

- Fix plugins reloading when switching project

### Changed

- Plugins code is now managed at Software instead of projects scope
- Plugins are still selected by project
- `Import plugin` button moved to Menu Bar
- Small UI improvements

### Removed

- Removed initialize() plugin method
    It is up to load() to check whether everything is already setup or not
- Cleaned up useless code

## [2.6.9+pm0.3.0] - 2022-11-14

### Added

- Added load() method to plugin class

### Fixed

- Fix the segfault on plugin import
- Fix Python 3.8 support

## [2.6.9+pm0.2.0] - 2022-11-08

### Added

- Added an error trace in log when plugin import failed
- Added initialize() and remove() methods to plugin class
- Added a dict containing plugins in main.py
- Added plugin folder removal when removing a plugin

### Changed

- Import plugins modules using absolute path

### Fixed

- Fix the crash when re-importing plugin
- Fix panel.close_plugin() close all plugins tabs
- Reload libraries on dynamic import

## [2.6.9+pm0.2.0] - 2022-07-22

### Added

- First plugin-manager version