Clear: I'll read pyproject.toml and provide the same novice-level walkthrough explaining what it does and why it matters. 

Read [](file:///c%3A/Users/henley/Documents/Dev/mypy/ticmymail/pyproject.toml)

## ✅ What pyproject.toml does (novice explanation)

Perfect: this is a **project configuration file** that tells Python tools how to install and build your package.  
Think of it as a "recipe card" that lists what ingredients (dependencies) your project needs and how to package it for others to use.

### The 3 main sections

#### 1. `[project]` — Project Metadata
- `name = "ticmymail"` — package name (what you `pip install ticmymail`)
- `version = "0.1.0"` — current version (semantic versioning: major.minor.patch)
- `description = "..."` — one-line summary
- `readme = "README.md"` — which file shows on PyPI (package hub)
- `requires-python = ">=3.11"` — minimum Python version required
- `dependencies = [...]` — **list of packages this app needs to run**
  - `fastapi>=0.115` — web framework
  - `uvicorn>=0.24` — ASGI server (runs FastAPI)
  - `pydantic>=2.7` — data validation
  - `python-multipart>=0.0.6` — handles form data
  - `PyYAML>=6.0` — reads YAML config files
  - `azure-storage-blob>=12.18` — connects to Azure Blob Storage

#### 2. `[project.optional-dependencies]` — Extra packages for development
- `test = [...]` — packages needed **only for testing**
  - `pytest>=8.4` — test framework
  - `httpx>=0.28` — mock HTTP requests
  - `pytest-asyncio>=0.23` — async test support
  - `pytest-cov>=4.1` — coverage reports
  - `log4python>=0.6.1` — logging
- When developers do `pip install -e .[test]`, they get these **plus** the main dependencies

#### 3. `[build-system]` — How to package your app
- `requires = ["setuptools>=65.0", "wheel"]` — tools needed to build
- `build-backend = "setuptools.build_meta"` — which tool actually builds (setuptools)
- This tells Python: "use setuptools to create .whl (wheel) files"

---

## 🤔 Why this file matters

1. **Dependency management**: lists everything needed so `pip install` knows what to fetch
2. **Reproducibility**: anyone running your app gets the same versions
3. **Distribution**: when you upload to PyPI, this file is used
4. **Development vs Production**: `[project.optional-dependencies]` keeps test tools separate
5. **Python version check**: ensures Python 3.11+ before installation

---

## 📍 Why is it named pyproject.toml?

- **TOML** = Tom's Obvious, Minimal Language (human-readable config format)
- `pyproject.` = Python standard (PEP 518 / PEP 517 spec)
- **location**: root of repository (same level as src, `README.md`)
- **standard name**: all Python tools look for this exact filename

---

## 🔄 How it connects to workflows

| Workflow | Uses pyproject.toml |
|----------|---------------------|
| ci.yml | ✅ `pip install -e .[test]` reads this file to get test deps |
| `cd-develop.yml` | ✅ `python -m build` reads this to create wheel + Docker image |
| cd-main.yml | ✅ Docker build (from Dockerfile) may reference this |

When workflows run `pip install`, Python reads pyproject.toml to know what to fetch.

---

## 💡 Novice example flow

1. Developer clones repo
2. Runs: `pip install -e .[test]`
3. Python reads pyproject.toml:
   - Installs `fastapi, uvicorn, pydantic,` etc. (main deps)
   - Installs `pytest, httpx, pytest-asyncio,` etc. (test deps)
4. Developer runs tests: `pytest`
5. CI workflow (` ci.yml`) does same: `pip install -e .[test]` then `pytest`
6. Build workflow (`cd-develop.yml`) reads version `"0.1.0"` to tag containers

---

## 📝 Next steps

- Update `version` when you release (0.1.0 → 0.2.0, etc.)
- Add new dependencies to `dependencies = [...]` if you add imports
- Add test tools to `[project.optional-dependencies]` if needed
- Never edit `[build-system]` unless changing build tooling (rare)

---

**Key takeaway**: pyproject.toml is your **project's manifest**—it tells Python (and other tools):
- what your package is called and versioned
- what it needs to run
- what extras are needed for development
- how to build and distribute it

Compare to workflows:
- workflows = *how* to test/deploy
- pyproject.toml = *what* to install before testing/deploying


# Understanding `pyproject.toml`

## What is `pyproject.toml`?

`pyproject.toml` is a **project configuration file** that tells Python tools how to install and build your package.  
Think of it as a "recipe card" listing what ingredients (dependencies) your project needs and how to package it for others to use.

## The 3 Main Sections

### 1. `[project]` — Project Metadata

This section describes your package:

- `name = "ticmymail"` — package name (what you `pip install ticmymail`)
- `version = "0.1.0"` — current version (semantic versioning: major.minor.patch)
- `description = "..."` — one-line summary shown on PyPI
- `readme = "README.md"` — which file displays on PyPI (Python Package Index)
- `requires-python = ">=3.11"` — minimum Python version required to run this package
- `dependencies = [...]` — **list of packages this app needs to run**

#### Current Dependencies
- `fastapi>=0.115` — web framework for building APIs
- `uvicorn>=0.24` — ASGI server that runs FastAPI
- `pydantic>=2.7` — data validation and parsing
- `python-multipart>=0.0.6` — handles form data in HTTP requests
- `PyYAML>=6.0` — reads YAML configuration files
- `azure-storage-blob>=12.18` — connects to Azure Blob Storage

### 2. `[project.optional-dependencies]` — Extra Packages for Development

These packages are only needed during **development and testing**, not in production:

- `pytest>=8.4` — test framework
- `httpx>=0.28` — mock HTTP requests
- `pytest-asyncio>=0.23` — async test support
- `pytest-cov>=4.1` — coverage reports
- `log4python>=0.6.1` — logging

When developers run `pip install -e .[test]`, they get both main dependencies **plus** these test tools.

### 3. `[build-system]` — How to Package Your App

This section tells Python which tools to use for packaging:

- `requires = ["setuptools>=65.0", "wheel"]` — tools needed to build the package
- `build-backend = "setuptools.build_meta"` — which tool actually performs the build

This tells Python: "use setuptools to create `.whl` (wheel) files for distribution"

---

## Why This File Matters

1. **Dependency Management**: Lists everything needed so `pip install` knows what to fetch
2. **Reproducibility**: Anyone running your app gets the same versions
3. **Distribution**: When you upload to PyPI, this file is used
4. **Development vs Production**: test dependencies stay separate from production code
5. **Python Version Check**: ensures Python 3.11+ is installed before attempting installation

---

## Location and Naming

- **Filename**: `pyproject.toml` (standard Python name, PEP 518 / PEP 517 spec)
- **Location**: Repository root (same level as `src/`, `README.md`, `Dockerfile`)
- **Format**: TOML (Tom's Obvious, Minimal Language — human-readable config format)
- **Standard name**: All Python tools automatically look for this exact filename

---

## Installation Flow Example

1. Developer clones repo
2. Runs: `pip install -e .[test]`
3. Python reads `pyproject.toml`:
   - Installs `fastapi, uvicorn, pydantic`, etc. (main dependencies)
   - Installs `pytest, httpx, pytest-asyncio`, etc. (test dependencies)
4. Developer runs tests: `pytest`
5. Everything works because dependencies are installed

---

## Updating `pyproject.toml`

- **Version bumps**: Update `version = "0.1.0"` → `"0.2.0"` when releasing
- **New dependencies**: Add to `dependencies = [...]` if you add new imports
- **New test tools**: Add to `[project.optional-dependencies]` if needed
- **Never edit build-system** unless changing build tooling (very rare)

---

## Key Takeaway

`pyproject.toml` is your **project's manifest**—it tells Python:
- what your package is called and versioned
- what it needs to run
- what extras are needed for development
- how to build and distribute it

Anyone (including CI/CD pipelines) reading this file will know exactly how to set up and use your project.
