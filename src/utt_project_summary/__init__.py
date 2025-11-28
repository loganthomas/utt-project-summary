"""
utt-project-summary: A utt plugin to show projects sorted by time spent.

This plugin adds a 'project-summary' command to utt that shows:

- All projects sorted by time spent (highest to lowest)
- Optional percentage breakdown of time per project
- Current activity included in totals
- Support for various date range filters

Installation
------------
Install via pip::

    pip install utt-project-summary

Usage
-----
After installation, the project-summary command is available via utt::

    utt project-summary [--show-perc] [--from DATE] [--to DATE] [--week WEEK] [--month MONTH]

Examples
--------
Show today's project summary::

    utt project-summary

Show with percentages::

    utt project-summary --show-perc

Show this week's summary::

    utt project-summary --week this

For more information, see: https://github.com/loganthomas/utt-project-summary
"""

__version__ = "0.1.0-rc.1"

__all__ = ["__version__"]
