# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-28

### Added
- Initial release of Burpy CLI web security testing tool
- HTTP proxy server for intercepting and modifying traffic
- Vulnerability scanner with support for:
  - SQL injection detection
  - Cross-site scripting (XSS) detection
  - Directory traversal vulnerability checks
  - Sensitive file discovery
  - Security header analysis
  - HTTP method enumeration
- Request repeater for manual testing and request modification
- Intruder module for automated attacks:
  - Parameter fuzzing
  - Authentication brute forcing
  - Directory brute forcing
  - SQL injection testing
- History logger for tracking and searching request/response history
- Configuration management system
- Comprehensive CLI interface with help system
- Cross-platform support (Windows, macOS, Linux)
- Comprehensive test suite with 150+ tests
- Documentation and examples

### Features
- Lightweight and fast
- No cloud dependencies
- Easy installation and setup
- Professional CLI interface
- Extensive logging and history management
- Configurable settings
- Multi-threaded operations for performance
- Error handling and recovery

### Technical Details
- Python 3.8+ support
- MIT License
- Comprehensive test coverage (87%)
- Professional code structure and documentation