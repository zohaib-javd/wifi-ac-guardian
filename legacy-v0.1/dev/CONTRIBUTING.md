# Contributing to WiFi AC Guardian 🤝

Thank you for your interest in contributing to **WiFi AC Guardian**! We welcome bug reports, feature requests, documentation updates, and pull requests from the community.

## 🚀 Getting Started

1. **Fork the Repository**: Create a fork of `zohaibjaved/wifi-ac-guardian` on GitHub.
2. **Clone your Fork**:
   ```bash
   git clone https://github.com/<your-username>/wifi-ac-guardian.git
   cd wifi-ac-guardian
   ```
3. **Set Up Development Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   pip install pytest
   ```

## 🧪 Running Unit Tests

Before submitting any code changes, ensure all unit tests pass:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
Or with pytest:
```bash
pytest tests/
```

## 📝 Pull Request Guidelines

- Create a feature branch (`git checkout -b feature/amazing-feature`).
- Ensure code follows PEP 8 styling and includes type hints.
- Commit your changes with semantic commit messages (`feat: ...`, `fix: ...`, `docs: ...`).
- Open a Pull Request against the `main` branch.
