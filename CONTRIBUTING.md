# CONTRIBUTING

## Git Hooks

The project includes a git_hooks directory with a pre-push hook that verifies that all code is 
linted and tests pass. To have git use the hooks in this directory, run:

```bash
git config core.hooksPath git_hooks
```