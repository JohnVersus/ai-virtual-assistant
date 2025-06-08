# AI Virtual Assistant

This is a desktop AI virtual assistant for macOS that listens for a wake word and responds using AI services.

## Project Setup and Running the App

This guide will walk you through setting up the project and running the application in both development and production (as a standalone app) using `uv`.

### 1. Initial Setup

Set up the project's virtual environment and install the dependencies.

```bash
# 1. Create the virtual environment in the project directory
uv venv

# 2. Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# 3. Sync the environment with the dependencies in pyproject.toml
uv sync
```

### 2. Running in Development Mode

To run the application directly for development or testing, use the `uv run` command. This will launch the UI and start the background listening service.

```bash
# Run the main application script
uv run -m src.app
```

You should see "Now listening in the background..." printed in your terminal, and the application window will appear.

### 3. Building for Production (Creating the `.app`)

To create a standalone, launchable macOS application (`.app` bundle), we use `py2app`.

```bash
# 1. Ensure your environment is active and synced.
# 2. Run the build command using uv.
uv run setup.py py2app
```

This command will create a `dist` folder in your project root. Inside `dist`, you will find `AI Virtual Assistant.app`. You can run this file like any other macOS application or drag it to your `/Applications` folder.

---

# UV Commands Cheatsheet

A quick reference for using the `uv` package manager.

## 🔧 Python Version & Project Setup

- `uv python install <version>`
  Installs a specific Python version using UV.

- `uv init`
  Initializes a new Python project with a `pyproject.toml` file.

---

## 📦 Package & Dependency Management

- `uv add <package>`
  Adds a package to the project and installs it, updating `pyproject.toml`.

- `uv sync`
  Syncs dependencies from the `pyproject.toml` file with the virtual environment.

- `uv remove <package>`
  Removes a package from the project and updates `pyproject.toml` accordingly.

---

## 🌐 Virtual Environment

- `uv venv`
  Creates a virtual environment in the `.venv` directory.

---

## 🚀 Running Code

- `uv run <command>`
  Runs a command (e.g., `python my_script.py`) using the project's virtual environment.
