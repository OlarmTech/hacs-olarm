# Contributing to Olarm Integration

Thank you for your interest in contributing to the Olarm integration for Home Assistant!

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Home Assistant development environment
- Git

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/olarmtech/hacs-olarm.git
   cd hacs-olarm
   ```

2. Link to your Home Assistant installation for testing:
   ```bash
   # In your Home Assistant config directory
   ln -s /path/to/hacs-olarm/custom_components/olarm custom_components/olarm
   ```

3. Restart Home Assistant to load the integration

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for all functions and methods
- Write descriptive docstrings for classes and functions
- Keep functions focused and single-purpose

## Testing Changes

Before submitting a pull request:

1. Test the integration with a real Olarm device
2. Verify OAuth2 flow works correctly
3. Check that all entities are created properly
4. Test MQTT connection and real-time updates
5. Ensure no errors in Home Assistant logs

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Commit with clear messages: `git commit -m "Add feature: description"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a Pull Request

### Pull Request Guidelines

- Describe what your PR does and why
- Reference any related issues
- Include screenshots for UI changes
- Update README if adding new features
- Increment version in `manifest.json` if applicable

## Reporting Issues

When reporting issues, please include:

- Home Assistant version
- Integration version
- Full error logs (check Developer Tools > Logs)
- Steps to reproduce
- Expected vs actual behavior

## Code of Conduct

- Be respectful and constructive
- Help create a welcoming environment
- Focus on what's best for the community

## Questions?

Feel free to open an issue for questions or discussions about:
- Feature requests
- Bug reports
- Development questions
- Documentation improvements

## Syncing with Home Assistant Core

This HACS version is temporary while the official integration is being reviewed for Home Assistant core. Contributors should be aware that:

- Changes should be compatible with the core PR
- We may deprecate this repository once core integration is merged
- Focus on bug fixes and minor improvements rather than major new features

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

