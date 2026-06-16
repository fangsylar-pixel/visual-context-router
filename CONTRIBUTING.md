# Contributing

Thanks for helping make visual agents cheaper and more reliable.

## Good First Contributions

- Add screenshot fixtures from real apps.
- Improve UI element classification.
- Add adapters for browser DOM or accessibility trees.
- Add benchmark cases for token savings and task accuracy.
- Improve docs for Codex, Playwright, Selenium, or desktop automation.

## Local Setup

```bash
pip install -e ".[dev]"
pytest
```

## Pull Request Expectations

- Keep the core package lightweight.
- Make heavy dependencies optional.
- Include tests for behavior changes.
- Prefer structured outputs over prose-only features.

