# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
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

## [1.7.36] - 2022-12-20
### Added artifactory authentication in the Jenkinsfile

## [1.7.35] 2022-03-15
### Changed
- Update base image to alpine 3.15
