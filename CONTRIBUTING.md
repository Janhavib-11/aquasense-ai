# Contributing to AquaSense AI

Thank you for considering a contribution. This is a focused, academic/demo project — keep changes minimal and purposeful.

## Workflow

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Make your changes with clear, focused commits.
4. Open a pull request against `main`.

## Code Standards

### Backend (Python)
- Follow PEP 8. Use `ruff` or `flake8` for linting.
- All new routes must have docstrings and proper exception handling.
- Never commit credentials or `.env` files.

### Frontend (HTML/JS)
- Vanilla JS only — no frameworks, no bundlers.
- Keep all API calls in the API layer section of `index.html`.
- All user-visible strings must be sanitised with `esc()` before DOM insertion.

## Reporting Issues

Open a GitHub Issue with:
- Steps to reproduce
- Expected vs actual behaviour
- Python version, OS, and browser (for frontend issues)
