## Description

<!-- Provide a brief description of your changes -->

## Type of Change

<!-- Check all that apply -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to change)
- [ ] 📝 Documentation update
- [ ] 🎨 Code style update (formatting, renaming)
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update
- [ ] 🔧 Build/CI update
- [ ] 📦 Dependency update

## Related Issues

<!-- Link related issues -->

Closes #(issue number)
Relates to #(issue number)

## Changes Made

<!-- List the main changes -->

-
-
-

## Testing

<!-- Describe how you tested your changes -->

### Test Configuration

- **Python version**:
- **OS**:
- **Installation method**:

### Test Results

- [ ] All existing tests pass
- [ ] New tests added (if applicable)
- [ ] Manual testing completed
- [ ] E2E tests pass (if WeMo devices available)

**Test commands run:**
```bash
pytest tests/ -v
# Add any other test commands you ran
```

## Documentation

<!-- Check all that apply -->

- [ ] README.md updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] Copilot instructions updated (if structure/tools changed)
- [ ] Tool docstrings updated (if MCP tools changed)
- [ ] Version bumped in ALL 3 files (if releasing):
  - [ ] `pyproject.toml`
  - [ ] `src/wemo_mcp_server/__init__.py`
  - [ ] `server.json`

##  Code Quality

<!-- Check all that apply -->

- [ ] Code follows project style guidelines
- [ ] Code formatted with `black` and `isort`
- [ ] Type hints added/updated
- [ ] No linting errors (`ruff check`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Logging uses stderr only (not stdout)
- [ ] Error handling includes helpful error messages

## Security

<!-- Check all that apply -->

- [ ] No secrets or credentials in code
- [ ] No sensitive data in logs
- [ ] No new security vulnerabilities introduced
- [ ] Security scan completed:
  ```bash
  git diff --cached | grep -iE '(api[_-]?key|secret|token|password|credential)'
  ```

## Breaking Changes

<!-- If this PR includes breaking changes, describe them here -->

**Does this PR introduce breaking changes?**

- [ ] Yes (describe below)
- [ ] No

<!-- If yes, describe: -->
<!-- - What breaks? -->
<!-- - Migration path for users -->
<!-- - Version bump justification (major version) -->

## Checklist

<!-- Final checks before submission -->

- [ ] I have read [CONTRIBUTING.md](https://github.com/apiarya/wemo-mcp-server/blob/main/CONTRIBUTING.md)
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] My changes generate no new warnings
- [ ] I have tested my changes locally
- [ ] My commit messages follow the project conventions
- [ ] I have rebased on the latest main branch
- [ ] I am ready for code review

## Screenshots

<!-- If applicable, add screenshots -->

N/A

## Additional Notes

<!-- Any additional information for reviewers -->

## For Maintainers

<!-- Maintainers will check these before merging -->

- [ ] PR title follows conventions
- [ ] Labels added
- [ ] Milestone set (if applicable)
- [ ] Ready to merge
