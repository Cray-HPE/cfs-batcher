# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Dependencies
- CSM 1.6 moved to Kubernetes 1.24, so use client v24.x to ensure compatibility
- CASMPET-7065 - update to cray-services:11.0.0 base chart

## [1.11.0] - 08/16/2024
### Added
- Add code to heartbeat thread that causes it to bail if the main thread is no longer alive.

### Fixed
- Perform a retry when CFS fails to retrieve session data.

### Dependencies
- Use `requests_retry_session` module instead of duplicating the code.

## [1.10.0] - 02/22/2024
### Dependencies
- Bump `kubernetes` from 9.0.1 to 22.6.0 to match CSM 1.6 Kubernetes version

## [1.9.2] - 01/10/2024
### Fixed
- Improved error handling during the rebuild state phase of startup

## [1.9.1] - 10/05/2023
### Fixed
- When specifying a configuration limit field for a session, use commas to delimit the
  layers (as per the API spec)

## [1.9.0] - 8/18/2023
### Changed
- Disabled concurrent Jenkins builds on same branch/commit
- Added build timeout to avoid hung builds

### Removed
- Removed defunct files leftover from previous versioning system
- Removed spec file for RPM no longer being built

### Dependencies
Bumped dependency patch versions:
| Package                  | From     | To       |
|--------------------------|----------|----------|
| `kubernetes`             | 9.0.0    | 9.0.1    |
| `rsa`                    | 4.7      | 4.7.2    |
| `urllib3`                | 1.25.9   | 1.25.11  |

### Changed
- Updated to the v3 CFS api for paging and memory improvements

### Fixed
- Fixed handling of unknown session success

## [1.8.0] - 1/12/2023
### Added
- Added an option to disable batcher
- Added artifactory authentication in the Jenkinsfile

### Changed
- Pending session timeout is now configurable using an option
- Logging level is now controlled by a CFS option
- Enabled building of unstable artifacts
- Updated header of update_versions.conf to reflect new tool options

### Fixed
- Spelling corrections.
- Update Chart with correct image and chart version strings during builds.

## [1.7.37] - 2023-01-10
### Fixed
- Update Chart with correct image and chart version strings during builds.
- Enabled building of unstable artifacts
- Updated header of update_versions.conf to reflect new tool options
### Added
- Converted to Gitflow

## [1.7.36] - 2022-12-20
### Added artifactory authentication in the Jenkinsfile

## [1.7.35] 2022-03-15
### Changed
- Update base image to alpine 3.15
