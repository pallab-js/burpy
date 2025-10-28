# Contributing to Burpy

Thank you for your interest in contributing to Burpy! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Add tests for your changes
6. Run the test suite to ensure everything passes
7. Submit a pull request

## Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

2. Run tests:
```bash
python -m pytest tests/
```

3. Run with coverage:
```bash
python -m pytest tests/ --cov=burpy
```

## Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and small
- Add type hints where appropriate

## Testing

- All new features must include tests
- Tests should cover both success and failure cases
- Aim for high test coverage
- Use descriptive test names

## Pull Request Process

1. Ensure your code passes all tests
2. Update documentation if needed
3. Add a clear description of your changes
4. Reference any related issues
5. Request review from maintainers

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any error messages or logs

## Security

If you discover a security vulnerability, please:
- Do not open a public issue
- Email the maintainers directly
- Include detailed information about the vulnerability

## License

By contributing to Burpy, you agree that your contributions will be licensed under the same MIT License that covers the project.