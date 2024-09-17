# Change Log
All notable changes to this project will be documented in this file.

## 1.0.0 - 2024-09-06
### Added
- Initial commit with readme and changelog
### Changed

### Deprecated

### Removed

### Fixed

## 1.1.0 - 2024-09-12
### Added

### Changed
- Way in which the program searches the O: drive. This improved efficiency and reduced memory consumption.
- Added logic to free up memory between test runs
### Deprecated

### Removed

### Fixed
- Fixed a issue where the live plotting would crash after the second or third run. The threads that ran the live plot and socketing were not being properly shut down after the test ended. This fix included more organized threading for the plotting animation and the socketing to prevent the server connection from getting bypassed.
- Restructured live plot to run in the main thread to avoid a potential issue.

## 1.1.1 - 2024-09-12
### Added

### Changed

### Deprecated

### Removed

### Fixed
- Changed the method of searching through the O drive for the customer folder. It now searches the entire folder more efficiently.
