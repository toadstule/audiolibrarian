# Contributing to audiolibrarian

We welcome contributions from the community! Whether it's bug reports, feature requests, or code
contributions, we appreciate your help in making audiolibrarian better.

## How to Contribute

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** for your changes
4. **Commit** your changes
5. **Push** to your fork
6. Submit a **Pull Request**

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/toadstule/audiolibrarian.git
   cd audiolibrarian
   ```

2. Install development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

## Running Tests

```bash
pytest
```

## Code Style

We use `ruff` for code formatting and linting. Please ensure your code passes all checks:

```bash
ruff check .
```

## Documentation

To build the documentation locally:

```bash
mkdocs serve
```

Then open `http://127.0.0.1:8000` in your browser.

## Reporting Issues

When reporting issues, please include:

- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your operating system and Python version
- Any relevant error messages

## Feature Requests

We welcome feature requests! Please open an issue and describe:

- The feature you'd like to see
- Why this feature would be useful
- Any suggestions for implementation

## Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.
