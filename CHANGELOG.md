# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).<br/>
This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->

## [v1.0.0](https://github.com/bswck/slothy/tree/v1.0.0) (2024-07-05)


No significant changes.


## [v1.0.0b3](https://github.com/bswck/slothy/tree/v1.0.0b3) (2024-06-23)


### Changed

- Restructured and enriched the test suite

### Fixed

- Fixed erroneous cache module returning behavior


## [v1.0.0b2](https://github.com/bswck/slothy/tree/v1.0.0b2) (2024-06-21)


### Added

- New context manager for typing-only imports, i.e. [`type_importing()`][slothy._importing.type_importing].


## [v1.0.0b1](https://github.com/bswck/slothy/tree/v1.0.0b1) (2024-06-21)


No significant changes.


## [v1.0.0b0](https://github.com/bswck/slothy/tree/v1.0.0b0) (2024-06-17)


No significant changes.


## [v0.2.0](https://github.com/bswck/slothy/tree/v0.2.0) (2024-06-14)


### Changed

- Settled on stable interface: `lazy_importing`/`lazy_importing`, `lazy_importing_if`/`lazy_importing_if`.

### Fixed

- Frame offset management of `__import__` replacement function.


## [v0.2.0b2](https://github.com/bswck/slothy/tree/v0.2.0b2) (2024-06-14)


No significant changes.


## [v0.2.0b1](https://github.com/bswck/slothy/tree/v0.2.0b1) (2024-06-14)


### Changed

- Rewrote the entire library according to Jelle Zijlstra's 'special key' implementation. ([#47](https://github.com/bswck/slothy/issues/47))


## [v0.1.0-beta](https://github.com/bswck/slothy/tree/v0.1.0-beta) (2024-05-08)


### Added

- Basic functionality and documentation.
