# Python Internship - CLI Diagnostics Tool and Devloper environment health inspector CLI

Inspects workstation status and yields a deterministic developer-environment health report.

### Exit Codes
- `0`: All requirements and dependencies passed.
- `1`: Environment degraded (one or more checks failed).
- `2`: Configuration file not found.
- `3`: Malformed configuration.
- `4`: Unhandled runtime exception.

### Installation & Execution
```bash
# 1. Create and activate isolated environment
python3 -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows

# 2. Install package in editable mode with test dependencies
pip install -e ".[dev]"

# 3. Run standard text report
devcheck

# 4. Run JSON report
devcheck --json

# 5. Execute test suite
pytest -v