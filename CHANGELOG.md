# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [v0.2.0] - 2022-05-30

### Added

- Bumping `gns3fy` tp `1.0.0-rc.2`
- Support for reading environment variables as values in the `labby.toml` configuration. But only some.
- Render option for `labby run node bootstrap --render` and `--render-output` to show configuration on demand.
- Changed references from `lock_file` to `state_file` to better reflect the purpose of the module.
- Added `labby.commands.common` module with method to automatically generate Labby objects. This is to improve DRY on the labby commands.
- Added `timeout` and `retries` options to general `ProviderSettings`.

### Fixed

- Deletion of nodes, links and projects attributes when specified.

## [v0.1.0] - 2022-05-25

Initial release.
