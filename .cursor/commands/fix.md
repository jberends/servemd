# fix

**Description:** Fix bugs or test errors in the ServeM project following best practices

**Prompt:**

I need to fix bugs or test errors in the ServeM documentation server. Please follow this systematic workflow:

Context provided: {{input}}

**Workflow Steps:**

1. **Analyze and Group Failures**
   - Identify which tests are failing from the provided context
   - Group failures by test file and test function/class
   - List failures in an organized manner with error types

2. **Check Test Fixtures and Setup** first
   - If failures occur in pytest fixtures or setup, fix those before retesting
   - Examine fixture definitions for any issues
   - Look for missing dependencies or incorrect test data
   - Check for scope issues (function, module, session)

3. **Verify Mocking** is applied correctly
   - Check if mocking is interfering with test logic
   - Ensure mocks are properly scoped and not affecting other tests
   - Prefer using pytest-mock or unittest.mock appropriately
   - Minimize use of mocking - prefer real implementations when possible

4. **Check for Moved Resources**
   - Search for relocated files (templates, markdown, assets) in recent commits
   - Use grep/search to find if resources have been moved
   - Verify paths in config.py match actual file locations

5. **Fix Tests, Not Codebase**
   - Adjust test expectations rather than changing application logic
   - UNLESS the codebase is actually broken or has bugs
   - If codebase changes are needed, explain the issue and propose changes clearly

6. **Run Tests Properly**
   - Use uv to run tests: `uv run pytest tests/ -v`
   - For specific test file: `uv run pytest tests/test_specific.py -v`
   - For specific test: `uv run pytest tests/test_file.py::test_function -v`
   - Use `-x` flag to stop on first failure: `uv run pytest tests/ -v -x`
   - Use `--lf` to run only last failed tests: `uv run pytest tests/ -v --lf`

7. **Check Common ServeM Issues**
   - Verify DOCS_ROOT points to valid documentation directory
   - Check that required files exist: index.md, sidebar.md, topbar.md
   - Verify cache directory permissions (CACHE_ROOT)
   - Check FastAPI routes and dependencies are properly configured
   - Ensure markdown rendering extensions are correctly configured

8. **Ask When Uncertain**
   - Don't guess at fixes, clarify requirements first
   - If the issue is unclear, ask specific questions
   - Provide clear explanation of what was found and what needs to change

**Important Reminders:**
- Prefer altering tests rather than code when fixing test failures
- Use `uv run` for all test execution to ensure proper environment
- Minimize use of mocking - prefer real file system and HTTP client testing
- Follow the principle: fix tests, not codebase (unless codebase is broken)
- Check linter errors after fixes: `uv run ruff check src/ tests/`
- Format code if needed: `uv run ruff format src/ tests/`
- Never commit code changes - leave that to the developer

**ServeM-Specific Testing Notes:**
- Tests use pytest with asyncio support (pytest-asyncio)
- HTTP testing uses FastAPI TestClient or httpx
- File system tests should use temporary directories or fixtures
- Check pyproject.toml for test configuration and dependencies

Please analyze the failures and propose fixes following this workflow.

**Arguments:**
- `input` (string, required): Context about the bug or test error (e.g., test output, error messages, file paths)

