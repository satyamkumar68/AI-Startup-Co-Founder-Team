# Contributing to AI Startup Co-Founder Team

Thank you for your interest in contributing to **AI Startup Co-Founder Team**! We welcome contributions from developers, designers, prompt engineers, and startup enthusiasts.

---

## 🛠️ Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/ai-startup-co-founder-team.git
   cd ai-startup-co-founder-team
   ```

2. **Configure your environment**:
   ```bash
   copy .env.example .env     # Windows
   # cp .env.example .env      # macOS/Linux
   ```
   *By default, the project runs locally with [Ollama](https://ollama.com/) with zero required API keys.*

3. **Install Backend Dependencies**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r backend/requirements.txt
   ```

4. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

---

## 🧪 Testing & Validation

Before submitting a Pull Request, verify that all test suites pass:

```bash
# Run unit test suite (45 tests)
pytest tests/unit/ -v

# Run API & WebSocket integration tests (12 tests)
pytest tests/integration/test_api.py -v

# Run frontend build check
cd frontend && npm run build
```

---

## 📝 Coding Standards

- **Python**: Follow PEP 8 guidelines. All Pydantic models must use strict type hints.
- **TypeScript**: Strict type checking with zero `any` declarations where possible.
- **CSS**: Follow the design system tokens in `frontend/src/index.css`. Do not add ad-hoc utility classes.
- **Security**: Never hardcode API keys, secrets, or write unescaped inputs into ReportLab or CSV templates. All user inputs must be properly validated and sanitized.

---

## 🚀 Submitting a Pull Request

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(agent): add enhanced financial unit economics modeling"
   ```
3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Open a Pull Request on GitHub against `main`. Fill in the PR template details.

---

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
