# utt-project-summary

[![CI - Test](https://github.com/loganthomas/utt-project-summary/actions/workflows/unit-tests.yml/badge.svg?branch=main)](https://github.com/loganthomas/utt-project-summary/actions/workflows/unit-tests.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/utt-project-summary.svg)](https://pypi.org/project/utt-project-summary/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/utt-project-summary.svg?label=PyPI%20downloads)](https://pypi.org/project/utt-project-summary/)
[![License - GPL-3.0](https://img.shields.io/pypi/l/utt-project-summary.svg)](https://github.com/loganthomas/utt-project-summary/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/utt-project-summary.svg)](https://pypi.org/project/utt-project-summary/)

A [`utt`](https://github.com/larose/utt) plugin that shows projects sorted by time spent.

## Why utt-project-summary?

This plugin provides a quick overview of how your time is distributed across different projects. It groups all activities by project and displays them sorted by total duration, giving you instant visibility into where your time is going.

**Key features:**

- 📊 **Project Breakdown** — See all projects sorted by time spent (highest to lowest)
- 📈 **Percentage View** — Optionally show percentage of total time for each project
- ⏱️ **Current Activity** — Shows your current activity and includes it in totals
- 📅 **Flexible Date Ranges** — Report by day, week, month, or custom date ranges

## Features

- 📊 **Project-Based View** - Activities grouped by project, sorted by duration
- 🔢 **Optional Percentages** - Add `--show-perc` to see time distribution percentages
- 📅 **Date Range Support** - Use `--from`, `--to`, `--week`, or `--month` flags
- 🔌 **Native `utt` Integration** - Uses `utt`'s plugin API for seamless integration

## Installation

### Step 1: Install `utt`

First, install [`utt` (Ultimate Time Tracker)](https://github.com/larose/utt):

```bash
pip install utt
```

Verify the installation:

```bash
utt --version
```

### Step 2: Install utt-project-summary

Install the plugin:

```bash
pip install utt-project-summary
```

That's it! The plugin is automatically discovered by `utt`. No additional configuration needed.

### Verify Installation

Confirm the `project-summary` command is available:

```bash
utt project-summary --help
```

**Requirements:**
- Python 3.10+
- `utt` >= 1.0

## Usage

After installation, a new `project-summary` command is available in `utt`:

```bash
utt project-summary
```

### Example Output

```
Project Summary
---------------

backend : 4h30
frontend: 2h15
meetings: 1h45
docs    : 0h30

Total   : 9h00
```

### With Percentages

```bash
utt project-summary --show-perc
```

```
Project Summary
---------------

backend : 4h30 ( 50.0%)
frontend: 2h15 ( 25.0%)
meetings: 1h45 ( 19.4%)
docs    : 0h30 (  5.6%)

Total   : 9h00 (100.0%)
```

### Options

| Option              | Default | Description                                    |
|---------------------|---------|------------------------------------------------|
| `--show-perc`       | false   | Show percentage of total time for each project |
| `--from`            | none    | Inclusive start date for the report            |
| `--to`              | none    | Inclusive end date for the report              |
| `--week`            | none    | Report for a specific week (`this`, `prev`, or week number) |
| `--month`           | none    | Report for a specific month (`this`, `prev`, `2024-10`, `Oct`) |
| `--project`         | none    | Filter to show only a specific project         |
| `--current-activity`| `-- Current Activity --` | Set the current activity name |
| `--no-current-activity` | false | Do not display the current activity        |

### Examples

**Default usage** (today's activities):
```bash
utt project-summary
```

**Show with percentages**:
```bash
utt project-summary --show-perc
```

**This week's summary**:
```bash
utt project-summary --week this
```

**Last month's summary**:
```bash
utt project-summary --month prev
```

**Custom date range**:
```bash
utt project-summary --from 2024-01-01 --to 2024-01-31
```

## How It Works

This plugin uses `utt`'s native plugin API to:
1. Access your time entries directly (no subprocess calls)
2. Filter activities based on date range arguments
3. Group activities by project name
4. Sort projects by total duration (descending)
5. Optionally calculate percentages of total time

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Development

### Running Tests

To run the test suite, first install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then run the tests with pytest:

```bash
pytest
```

For coverage reporting:

```bash
pytest --cov=utt_project_summary --cov-report=term-missing
```

### Linting & Formatting

**Run ruff** (linter, formatter, and import sorting):
```bash
# Check for linting errors
ruff check .

# Auto-fix linting errors (including import sorting)
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

**Run ty** (type checker):
```bash
ty check src/
```

### Run All Checks

```bash
ruff check --fix . && ruff format . && ty check src/ && pytest
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run checks before each commit:

```bash
pre-commit install
```

Run hooks manually on all files:

```bash
pre-commit run --all-files
```

## Contributing

Contributions are welcome! Here's how to get started:

### Setting Up for Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/loganthomas/utt-project-summary.git
   cd utt-project-summary
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in editable mode with dev dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### Submitting Changes

1. Create a new branch for your feature or fix
2. Make your changes following the code style guidelines
3. Ensure all tests pass: `pytest`
4. Ensure code passes linting: `ruff check . && ruff format --check .`
5. Submit a pull request with a clear description of your changes

### Code Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints for all function signatures
- Write docstrings in [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html)
- Keep functions focused and single-purpose
- Prefer explicit over implicit

## Related

- [`utt` (Ultimate Time Tracker)](https://github.com/larose/utt) - The time tracking tool this plugin extends
- [`utt` Plugin Documentation](https://github.com/larose/utt/blob/master/docs/PLUGINS.md) - How to create `utt` plugins
- [`utt-balance`](https://github.com/loganthomas/utt-balance) - Another `utt` plugin for checking work-life balance
