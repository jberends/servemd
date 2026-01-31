# Release Workflow Guide

## Quick Start: Creating a Release

```bash
# 1. Update version
vim src/docs_server/__init__.py  # Change __version__ = "1.0.1"

# 2. Update changelog
vim CHANGELOG.md  # Add release notes under ## [1.0.1]

# 3. Commit and tag
git add .
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags

# 4. Create GitHub release
gh release create v1.0.1 \
  --title "v1.0.1" \
  --notes-file <(sed -n '/## \[1.0.1\]/,/## \[/p' CHANGELOG.md | head -n -1)
```

That's it! GitHub Actions will automatically:
- ✅ Run tests on Python 3.11, 3.12, 3.13
- ✅ Run linter checks
- ✅ Build the package
- ✅ Publish to PyPI
- ✅ Build and publish Docker images (Docker Hub + GHCR)
- ✅ Upload artifacts to GitHub release

---

## First-Time Setup

### Docker Hub Setup (One-time)

To publish Docker images to Docker Hub:

1. **Create Docker Hub account**: https://hub.docker.com/signup
2. **Create repository**: 
   - Go to https://hub.docker.com/repositories
   - Click "Create Repository"
   - Name: `servemd`
   - Visibility: **Public**
3. **Create access token**:
   - Go to https://hub.docker.com/settings/security
   - Click "New Access Token"
   - Description: `GitHub Actions - servemd`
   - Permissions: `Read, Write, Delete`
   - Copy the token
4. **Add secrets to GitHub**:
   - Go to https://github.com/jberends/servemd/settings/secrets/actions
   - Add `DOCKERHUB_USERNAME` (your Docker Hub username)
   - Add `DOCKERHUB_TOKEN` (the access token)

After first push, the images will be available at:
- Docker Hub: https://hub.docker.com/r/jberends/servemd
- GHCR: https://github.com/jberends/servemd/pkgs/container/servemd

**Note**: GHCR packages are private by default. Make it public at the package settings after first push.

---

### Option 1: PyPI Trusted Publishing (Recommended - No tokens!)

1. **After first manual publish**, go to https://pypi.org/manage/account/publishing/

2. Click "Add a new publisher" and fill in:
   - **PyPI Project Name**: `servemd`
   - **Owner**: `jberends`
   - **Repository name**: `servemd`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi`

3. Save and you're done! Future releases will auto-publish.

### Option 2: Using API Tokens

1. Get token from https://pypi.org/manage/account/token/

2. Add to GitHub secrets:
   - Go to: https://github.com/jberends/servemd/settings/secrets/actions
   - Name: `PYPI_TOKEN`
   - Value: Your token

3. Update `.github/workflows/publish-pypi.yml`:
   ```yaml
   - name: Publish distribution to PyPI
     env:
       UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
     run: uv publish
   ```

---

## Workflow Details

### Trigger
The workflow runs when you publish a GitHub release (not just tag).

### Jobs

1. **test** - Runs tests on multiple Python versions
2. **build** - Builds wheel and source distribution
3. **publish-to-pypi** - Publishes to PyPI using OIDC
4. **publish-to-github** - Uploads artifacts to GitHub release

### Files Created
- `dist/servemd-{version}-py3-none-any.whl`
- `dist/servemd-{version}.tar.gz`

Both are uploaded to PyPI and attached to the GitHub release.

---

## Troubleshooting

### Workflow fails on "Publish to PyPI"

**Error**: `Trusted publishing exchange failure`

**Solution**: You need to configure PyPI Trusted Publisher first (see Option 1 above).

### Workflow fails on tests

The workflow will not publish if tests fail. Fix the tests and create a new release.

### How to skip publishing?

Create a draft release instead:
```bash
gh release create v1.0.1 --draft --title "v1.0.1" --notes "Draft"
```

When ready, click "Publish release" in GitHub UI.

### How to test before real release?

1. Use TestPyPI for testing
2. Or create a pre-release: `gh release create v1.0.1-rc1 --prerelease`

---

## Version Numbering

Follow semantic versioning:
- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features, backwards compatible
- **Patch** (1.0.1): Bug fixes

The version is read from `src/docs_server/__init__.py`.

---

## Complete Example Release

```bash
# 1. Update version
vim src/docs_server/__init__.py  # __version__ = "1.1.0"

# 2. Update CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'

## [1.1.0] - 2026-02-15

### Added
- Enhanced MCP search capabilities
- New semantic search features
- Fuzzy search support

### Fixed
- Better error handling in MCP endpoint
- Performance improvements in indexing

### Changed
- Updated search algorithm for better relevance
EOF

# 3. Commit and tag
git add src/docs_server/__init__.py CHANGELOG.md
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags

# 4. Create GitHub release with changelog
gh release create v1.1.0 \
  --title "v1.1.0 - MCP Enhancements" \
  --notes-file <(sed -n '/## \[1.1.0\]/,/## \[/p' CHANGELOG.md | head -n -1)

# 5. Check status
gh run list --workflow=publish-pypi.yml

# 6. View in browser
gh release view v1.1.0 --web
```

---

## Additional Resources

- **PyPI Publishing**: [PUBLISHING.md](../PUBLISHING.md)
- **Docker Publishing**: [DOCKER_PUBLISHING.md](../DOCKER_PUBLISHING.md)
- **Workflows**: 
  - [publish-pypi.yml](workflows/publish-pypi.yml)
  - [publish-docker.yml](workflows/publish-docker.yml)
- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
- Docker Hub: https://hub.docker.com/r/jberends/servemd
- GHCR: https://github.com/jberends/servemd/pkgs/container/servemd
