# Contributing to REASSEMBLE

Thank you for your interest in contributing to REASSEMBLE!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Commit using conventional commits: `feat: add memory decay`
6. Push and create a Pull Request

## Development Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. **Never commit secrets.**

## Code Style

- Follow PEP 8
- Use type hints where practical
- Keep functions focused and small
- Add docstrings to public functions

## Commit Convention

```
feat: add new feature
fix: fix a bug
docs: documentation changes
chore: maintenance tasks
refactor: code restructuring
```

## Security

- Never commit API keys, passwords, or connection strings
- Use environment variables for all secrets
- Report security issues privately

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
