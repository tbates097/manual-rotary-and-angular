# Change Log
All notable changes to this project will be documented in this file.

## 1.2.1 - 2025-01-30

### Fixed
- Fixed an issue where the hexapod "verification" plots were overwriting the accuracy plots because there was no way for the program to know that it was running a verification test.

### Added
- A more robust serial communication class
- A more robust Aerotech PDF class

## 1.1.1 - 2024-09-12

### Fixed
- Fixed an issue with importing data files to recreate plots. The logic for this shares a function with the main test path and the function was only able to handle variables from the test path.
- Relocated where the main test function calls the socket server to avoid having it called during an import data path.
- Changed overtravel to support Hexapod rotational axes

## 1.1.0 - 2024-09-12

### Changed
- Way in which the program searches the O: drive. This improved efficiency and reduced memory consumption.
- Added logic to free up memory between test runs.

### Fixed
- Fixed an issue where the live plotting would crash after the second or third run. The threads that ran the live plot and socketing were not being properly shut down after the test ended. This fix included more organized threading for the plotting animation and the socketing to prevent the server connection from getting bypassed.
- Restructured live plot to run in the main thread to avoid a potential issue.

## 1.0.0 - 2024-09-06

### Added
- Initial commit with readme and changelog.
