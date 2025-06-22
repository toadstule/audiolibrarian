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

2. Install dependencies using the Makefile:

   ```bash
   make dep
   ```

   This will install all required dependencies in a virtual environment.

## Development Workflow

### Running Tests

Run the test suite:

```bash
make test
```

For tests with coverage report:

```bash
make test-coverage
```

### Code Style and Linting

We use `ruff` for code formatting and linting. The Makefile provides these helpful commands:

```bash
make format    # Format the code and sort imports
make lint      # Run all linters and type checking
```

### Building Documentation

To build and serve the documentation locally:

```bash
make docs
```

This will start a local server at `http://127.0.0.1:8000` where you can preview the documentation.

### Building the Package

To build the package:

```bash
make build
```

### Updating Dependencies

To upgrade all dependencies:

```bash
make dep-upgrade
```

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

## Available Make Commands

For a complete list of available commands, run:

```bash
make help
```
