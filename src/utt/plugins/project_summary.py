"""utt project-summary plugin: Show projects sorted by time spent."""

from __future__ import annotations

import argparse
import itertools
from datetime import timedelta
from typing import TYPE_CHECKING, NamedTuple

from utt.api import _v1

DEFAULT_CURRENT_ACTIVITY_NAME = "-- Current Activity --"

if TYPE_CHECKING:
    from collections.abc import Sequence


class ProjectDuration(NamedTuple):
    """Project with its total duration."""

    name: str
    duration: timedelta

    @property
    def formatted(self) -> str:
        """Return duration as 'XhYY' string."""
        return format_duration(self.duration)


class CurrentActivity(NamedTuple):
    """Current activity info."""

    name: str
    duration: timedelta

    @property
    def formatted(self) -> str:
        """Return duration as 'XhYY' string."""
        return format_duration(self.duration)


def format_duration(duration: timedelta) -> str:
    """Format timedelta as 'XhYY' (e.g., '6h30')."""
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h{minutes:02d}"


class ProjectSummaryModel:
    """
    Aggregate activities by project and calculate durations.

    Parameters
    ----------
    activities : Sequence[_v1.Activity]
        Activities to summarize.

    Attributes
    ----------
    projects : list[ProjectDuration]
        Projects sorted by duration (descending).
    current_activity : CurrentActivity | None
        Current activity if present.
    total_duration : timedelta
        Sum of all durations including current activity.
    """

    def __init__(self, activities: Sequence[_v1.Activity]) -> None:
        work_activities = [a for a in activities if a.type == _v1.Activity.Type.WORK]
        non_current = [a for a in work_activities if not a.is_current_activity]

        self.projects = self._aggregate_projects(non_current)
        self.current_activity = self._extract_current(activities)
        self.total_duration = self._compute_total()

    def _aggregate_projects(self, activities: Sequence[_v1.Activity]) -> list[ProjectDuration]:
        """Group activities by project and sort by total duration descending."""
        sorted_acts = sorted(activities, key=lambda a: a.name.project)
        result = []

        for project, group in itertools.groupby(sorted_acts, key=lambda a: a.name.project):
            total = sum((a.duration for a in group), timedelta())
            result.append(ProjectDuration(project, total))

        return sorted(result, key=lambda p: p.duration, reverse=True)

    def _extract_current(self, activities: Sequence[_v1.Activity]) -> CurrentActivity | None:
        """Extract current activity if present."""
        return next(
            (CurrentActivity(a.name.name, a.duration) for a in activities if a.is_current_activity),
            None,
        )

    def _compute_total(self) -> timedelta:
        """Sum all project durations plus current activity."""
        total = sum((p.duration for p in self.projects), timedelta())
        if self.current_activity:
            total += self.current_activity.duration
        return total


class ProjectSummaryView:
    """Render project summary output."""

    def __init__(
        self,
        model: ProjectSummaryModel,
        show_perc: bool = False,
        show_current: bool = True,
        current_activity_name: str = DEFAULT_CURRENT_ACTIVITY_NAME,
    ) -> None:
        self._model = model
        self._show_perc = show_perc
        self._show_current = show_current
        self._current_activity_name = current_activity_name

    def render(self, output: _v1.Output) -> None:
        """Render the project summary to output stream."""
        print(file=output)
        print("Project Summary", file=output)
        print("---------------", file=output)
        print(file=output)

        max_name_len = max((len(p.name) for p in self._model.projects), default=0)
        total_secs = self._model.total_duration.total_seconds()

        max_dur_len = 0
        if self._show_perc:
            durations = [len(p.formatted) for p in self._model.projects]
            durations.append(len(format_duration(self._model.total_duration)))
            max_dur_len = max(durations, default=0)

        for project in self._model.projects:
            dur_str = project.formatted
            if self._show_perc and total_secs > 0:
                perc = (project.duration.total_seconds() / total_secs) * 100
                dur_str = f"{dur_str:<{max_dur_len}} ({perc:5.1f}%)"
            print(f"{project.name:<{max_name_len}}: {dur_str}", file=output)

        if self._show_current and self._model.current_activity:
            ca = self._model.current_activity
            dur_str = ca.formatted
            if self._show_perc and total_secs > 0:
                perc = (ca.duration.total_seconds() / total_secs) * 100
                dur_str = f"{dur_str:<{max_dur_len}} ({perc:5.1f}%)"
            print(f"{self._current_activity_name:<{max_name_len}}: {dur_str}", file=output)

        print(file=output)
        total_str = format_duration(self._model.total_duration)
        if self._show_perc:
            total_str = f"{total_str:<{max_dur_len}} (100.0%)"
        print(f"{'Total':<{max_name_len}}: {total_str}", file=output)
        print(file=output)


class ProjectSummaryHandler:
    """Handler for the project-summary command."""

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
        """Execute command."""
        model = ProjectSummaryModel(self._activities)
        view = ProjectSummaryView(
            model,
            show_perc=self._args.show_perc,
            show_current=not self._args.no_current_activity,
            current_activity_name=self._args.current_activity,
        )
        view.render(self._output)


def add_args(parser: argparse.ArgumentParser) -> None:
    """Add command-line arguments for project-summary."""
    parser.add_argument("report_date", metavar="date", type=str, nargs="?")
    parser.set_defaults(csv_section=None, comments=False, details=False, per_day=False)

    parser.add_argument(
        "--show-perc",
        action="store_true",
        default=False,
        help="Show percentage of total time for each project",
    )
    parser.add_argument(
        "--current-activity",
        default=DEFAULT_CURRENT_ACTIVITY_NAME,
        type=str,
        help="Set the current activity name",
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
        help="Inclusive start date for the report",
    )
    parser.add_argument(
        "--to",
        default=None,
        dest="to_date",
        type=str,
        help="Inclusive end date for the report",
    )
    parser.add_argument(
        "--project",
        default=None,
        type=str,
        help="Show activities only for the specified project",
    )
    parser.add_argument(
        "--month",
        default=None,
        nargs="?",
        const="this",
        type=str,
        help="Report for a specific month (e.g., '2024-10', 'Oct', 'this', 'prev')",
    )
    parser.add_argument(
        "--week",
        default=None,
        nargs="?",
        const="this",
        type=str,
        help="Report for a specific week (e.g., 'this', 'prev', or week number)",
    )


# Note: type: ignore needed because _v1.Command expects a specific handler protocol
# that differs from our implementation's signature (uses filtered_activities vs activities)
project_summary_command = _v1.Command(
    name="project-summary",
    description="Show projects sorted by time spent",
    handler_class=ProjectSummaryHandler,  # type: ignore[arg-type]
    add_args=add_args,
)

_v1.register_command(project_summary_command)
