"""
utt Project Summary Plugin - Show projects sorted by time spent.

This plugin adds a 'project-summary' command to utt that displays all projects
grouped and sorted by total duration, with optional percentage breakdown.

Example
-------
>>> utt project-summary
>>> utt project-summary --show-perc
>>> utt project-summary --week this --show-perc
"""

from __future__ import annotations

import argparse
import itertools
from datetime import timedelta
from typing import TYPE_CHECKING

from utt.api import _v1

if TYPE_CHECKING:
    from collections.abc import Sequence


def format_duration(duration: timedelta) -> str:
    """
    Format a timedelta as 'XhYY' (e.g., '6h30' or '25h00').

    Parameters
    ----------
    duration : timedelta
        The time duration to format.

    Returns
    -------
    str
        Formatted string in hours and zero-padded minutes.
    """
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h{minutes:02d}"


def format_title(title: str) -> str:
    """
    Format a title with an underline.

    Parameters
    ----------
    title : str
        The title to format.

    Returns
    -------
    str
        Title with dashed underline.
    """
    return f"{title}\n{'-' * len(title)}"


class ProjectSummaryModel:
    """
    Model containing project summary data.

    Groups activities by project and calculates total durations.

    Parameters
    ----------
    activities : Sequence[_v1.Activity]
        List of activities to summarize.

    Attributes
    ----------
    projects : list[dict]
        List of project dictionaries with 'project', 'duration', and 'duration_obj' keys,
        sorted by duration descending.
    current_activity : dict | None
        Current activity info if present, with 'name', 'duration', and 'duration_obj' keys.
    total_duration : str
        Formatted total duration string.
    """

    def __init__(self, activities: Sequence[_v1.Activity]) -> None:
        work_activities = self._filter_work_activities(activities)
        self.projects = self._groupby_project_sorted_by_duration(work_activities)
        self.current_activity = self._get_current_activity_info(activities)
        self.total_duration = self._calculate_total_duration()

    def _filter_work_activities(self, activities: Sequence[_v1.Activity]) -> list[_v1.Activity]:
        """Filter to only WORK type activities."""
        return [act for act in activities if act.type == _v1.Activity.Type.WORK]

    def _calculate_total_duration(self) -> str:
        """Calculate and format total duration including current activity."""
        total = sum((project["duration_obj"] for project in self.projects), timedelta())
        if self.current_activity:
            total += self.current_activity["duration_obj"]
        return format_duration(total)

    def _get_current_activity_info(self, activities: Sequence[_v1.Activity]) -> dict | None:
        """Extract current activity information if present."""
        for activity in activities:
            if activity.is_current_activity:
                return {
                    "name": activity.name.name,
                    "duration": format_duration(activity.duration),
                    "duration_obj": activity.duration,
                }
        return None

    def _groupby_project_sorted_by_duration(self, activities: Sequence[_v1.Activity]) -> list[dict]:
        """Group activities by project and sort by total duration descending."""

        def key(act: _v1.Activity) -> str:
            return act.name.project

        non_current_activities = [act for act in activities if not act.is_current_activity]
        result = []
        sorted_activities = sorted(non_current_activities, key=key)

        for project, project_activities in itertools.groupby(sorted_activities, key):
            activities_list = list(project_activities)
            total_duration = sum((act.duration for act in activities_list), timedelta())
            result.append(
                {
                    "duration": format_duration(total_duration),
                    "project": project,
                    "duration_obj": total_duration,
                }
            )

        return sorted(result, key=lambda r: r["duration_obj"], reverse=True)


class ProjectSummaryView:
    """
    View for rendering project summary output.

    Parameters
    ----------
    model : ProjectSummaryModel
        The model containing project summary data.
    show_perc : bool, optional
        Whether to show percentages, by default False.
    """

    def __init__(self, model: ProjectSummaryModel, show_perc: bool = False) -> None:
        self._model = model
        self._show_perc = show_perc

    def render(self, output: _v1.Output) -> None:
        """
        Render the project summary to the output stream.

        Parameters
        ----------
        output : _v1.Output
            Output stream to write to.
        """
        print(file=output)
        print(format_title("Project Summary"), file=output)
        print(file=output)

        max_project_length = max((len(p["project"]) for p in self._model.projects), default=0)

        total_seconds = sum(
            (p["duration_obj"] for p in self._model.projects), timedelta()
        ).total_seconds()
        if self._model.current_activity:
            total_seconds += self._model.current_activity["duration_obj"].total_seconds()

        max_duration_length = 0
        if self._show_perc:
            durations = [len(p["duration"]) for p in self._model.projects]
            durations.append(len(self._model.total_duration))
            max_duration_length = max(durations, default=0)

        for project in self._model.projects:
            duration_str = project["duration"]
            if self._show_perc and total_seconds > 0:
                perc = (project["duration_obj"].total_seconds() / total_seconds) * 100
                duration_str = f"{duration_str:<{max_duration_length}} ({perc:5.1f}%)"
            print(f"{project['project']:<{max_project_length}}: {duration_str}", file=output)

        if self._model.current_activity:
            name = self._model.current_activity["name"]
            duration_str = self._model.current_activity["duration"]
            if self._show_perc and total_seconds > 0:
                perc = (
                    self._model.current_activity["duration_obj"].total_seconds() / total_seconds
                ) * 100
                duration_str = f"{duration_str} ({perc:5.1f}%)"
            print(f"{name:<{max_project_length}}: {duration_str}", file=output)

        print(file=output)
        total_str = self._model.total_duration
        if self._show_perc:
            total_str = f"{total_str:<{max_duration_length}} (100.0%)"
        print(f"{'Total':<{max_project_length}}: {total_str}", file=output)

        print(file=output)


class ProjectSummaryHandler:
    """
    Handler for the project-summary command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    filtered_activities : _v1.Activities
        Activities filtered by the report date range.
    output : _v1.Output
        Output stream for rendering results.
    """

    def __init__(
        self,
        args: argparse.Namespace,
        filtered_activities: _v1.Activities,
        output: _v1.Output,
    ) -> None:
        self._args = args
        self._activities = filtered_activities
        self._output = output

    def __call__(self) -> None:
        """Execute the project-summary command and display results."""
        model = ProjectSummaryModel(self._activities)
        view = ProjectSummaryView(model, show_perc=self._args.show_perc)
        view.render(self._output)


def add_args(parser: argparse.ArgumentParser) -> None:
    """
    Add command-line arguments for the project-summary command.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The argument parser to add arguments to.
    """
    parser.add_argument("report_date", metavar="date", type=str, nargs="?")

    # Set defaults for report_args attributes that project-summary doesn't use
    # but are required by the ReportArgs component
    parser.set_defaults(csv_section=None, comments=False, details=False, per_day=False)

    parser.add_argument(
        "--show-perc",
        action="store_true",
        default=False,
        help="Show percentage of total time for each project",
    )

    parser.add_argument(
        "--current-activity",
        default="-- Current Activity --",
        type=str,
        help="Set the current activity",
    )

    parser.add_argument(
        "--no-current-activity",
        action="store_true",
        default=False,
        help="Do not display the current activity",
    )

    parser.add_argument(
        "--from",
        default=None,
        dest="from_date",
        type=str,
        help="Specify an inclusive start date to report.",
    )

    parser.add_argument(
        "--to",
        default=None,
        dest="to_date",
        type=str,
        help=(
            "Specify an inclusive end date to report. "
            "If this is a day of the week, then it is the next occurrence "
            "from the start date of the report, including the start date "
            "itself."
        ),
    )

    parser.add_argument(
        "--project",
        default=None,
        type=str,
        help="Show activities only for the specified project.",
    )

    parser.add_argument(
        "--month",
        default=None,
        nargs="?",
        const="this",
        type=str,
        help=(
            "Specify a month. "
            "Allowed formats include, '2019-10', 'Oct', 'this' 'prev'. "
            "The report will start on the first day of the month and end "
            "on the last.  '--from' or '--to' if present will override "
            "start and end, respectively.  If the month is the current "
            "month, 'today' will be the last day of the report."
        ),
    )

    parser.add_argument(
        "--week",
        default=None,
        nargs="?",
        const="this",
        type=str,
        help=(
            "Specify a week. "
            "Allowed formats include, 'this' 'prev', or week number. "
            "The report will start on the first day of the week (Monday) "
            "and end on the last (Sunday).  '--from' or '--to' if present "
            "will override start and end, respectively.  If the week is "
            "the current week, 'today' will be the last day of the report."
        ),
    )


# Register the project-summary command with utt
project_summary_command = _v1.Command(
    name="project-summary",
    description="Show projects sorted by time spent",
    handler_class=ProjectSummaryHandler,  # type: ignore[arg-type]
    add_args=add_args,
)

_v1.register_command(project_summary_command)
