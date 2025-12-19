"""Unit tests for the project-summary plugin."""

import argparse
import io
from datetime import datetime, timedelta

import pytz

from utt.api import _v1
from utt.plugins.project_summary import (
    ProjectSummaryHandler,
    ProjectSummaryModel,
    ProjectSummaryView,
    add_args,
    format_duration,
    project_summary_command,
)


def create_activity(
    name: str,
    start_time: datetime,
    duration_minutes: int,
    is_current: bool = False,
) -> _v1.Activity:
    """Create a test activity."""
    start = pytz.UTC.localize(start_time)
    end = start + timedelta(minutes=duration_minutes)
    return _v1.Activity(name, start, end, is_current)


class TestFormatDuration:
    def test_zero_time(self):
        assert format_duration(timedelta(hours=0)) == "0h00"

    def test_whole_hours(self):
        assert format_duration(timedelta(hours=8)) == "8h00"

    def test_hours_and_minutes(self):
        assert format_duration(timedelta(hours=6, minutes=30)) == "6h30"

    def test_minutes_only(self):
        assert format_duration(timedelta(minutes=45)) == "0h45"

    def test_large_hours(self):
        assert format_duration(timedelta(hours=40)) == "40h00"

    def test_single_digit_minutes_padded(self):
        assert format_duration(timedelta(hours=1, minutes=5)) == "1h05"


class TestProjectSummaryModel:
    def test_empty_activities(self):
        model = ProjectSummaryModel([])
        assert model.projects == []
        assert model.current_activity is None
        assert model.total_duration == timedelta()

    def test_single_project(self):
        activities = [
            create_activity("backend: api work", datetime(2024, 1, 1, 9, 0), 180),
        ]
        model = ProjectSummaryModel(activities)
        assert len(model.projects) == 1
        assert model.projects[0].name == "backend"
        assert model.projects[0].formatted == "3h00"

    def test_multiple_projects_sorted_by_duration(self):
        activities = [
            create_activity("alpha: task1", datetime(2024, 1, 1, 9, 0), 30),
            create_activity("beta: task1", datetime(2024, 1, 1, 10, 0), 90),
            create_activity("gamma: task1", datetime(2024, 1, 1, 12, 0), 60),
        ]
        model = ProjectSummaryModel(activities)

        assert len(model.projects) == 3
        assert model.projects[0].name == "beta"
        assert model.projects[1].name == "gamma"
        assert model.projects[2].name == "alpha"

    def test_activities_grouped_by_project(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 60),
            create_activity("project1: task2", datetime(2024, 1, 1, 10, 0), 60),
            create_activity("project2: task1", datetime(2024, 1, 1, 11, 0), 30),
        ]
        model = ProjectSummaryModel(activities)

        assert len(model.projects) == 2
        project1 = next(p for p in model.projects if p.name == "project1")
        assert project1.formatted == "2h00"

    def test_current_activity_extracted(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 60),
            create_activity(
                "-- Current Activity --", datetime(2024, 1, 1, 10, 0), 30, is_current=True
            ),
        ]
        model = ProjectSummaryModel(activities)

        assert model.current_activity is not None
        assert model.current_activity.name == "-- Current Activity --"
        assert model.current_activity.formatted == "0h30"

    def test_current_activity_not_in_projects(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 60),
            create_activity(
                "-- Current Activity --", datetime(2024, 1, 1, 10, 0), 30, is_current=True
            ),
        ]
        model = ProjectSummaryModel(activities)

        assert len(model.projects) == 1
        assert all(p.name != "-- Current Activity --" for p in model.projects)

    def test_total_duration_includes_current_activity(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 60),
            create_activity(
                "-- Current Activity --", datetime(2024, 1, 1, 10, 0), 30, is_current=True
            ),
        ]
        model = ProjectSummaryModel(activities)

        assert format_duration(model.total_duration) == "1h30"


class TestProjectSummaryView:
    def test_output_with_aligned_colons(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 240),
            create_activity("project2: task1", datetime(2024, 1, 1, 13, 0), 165),
            create_activity("project3: task1", datetime(2024, 1, 1, 16, 0), 30),
            create_activity("project4: task1", datetime(2024, 1, 1, 17, 0), 30),
            create_activity("project5: task1", datetime(2024, 1, 1, 18, 0), 15),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        assert "Project Summary" in lines[1]
        assert "project1: 4h00" in lines[4]
        assert "project2: 2h45" in lines[5]
        assert "project3: 0h30" in lines[6]
        assert "project4: 0h30" in lines[7]
        assert "project5: 0h15" in lines[8]
        assert "Total   : 8h00" in lines[10]

    def test_output_with_current_activity(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 240),
            create_activity("project2: task1", datetime(2024, 1, 1, 13, 0), 165),
            create_activity("project3: task1", datetime(2024, 1, 1, 16, 0), 30),
            create_activity("project4: task1", datetime(2024, 1, 1, 17, 0), 30),
            create_activity("project5: task1", datetime(2024, 1, 1, 18, 0), 15),
            create_activity(
                "-- Current Activity --", datetime(2024, 1, 1, 19, 0), 220, is_current=True
            ),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        assert "project1: 4h00" in lines[4]
        assert "project2: 2h45" in lines[5]
        assert "project3: 0h30" in lines[6]
        assert "project4: 0h30" in lines[7]
        assert "project5: 0h15" in lines[8]
        assert "-- Current Activity --: 3h40" in lines[9]
        assert "Total   : 11h40" in lines[11]

    def test_colons_aligned_with_varying_project_lengths(self):
        activities = [
            create_activity("a: task1", datetime(2024, 1, 1, 9, 0), 60),
            create_activity("medium-name: task1", datetime(2024, 1, 1, 10, 0), 120),
            create_activity("very-long-project-name: task1", datetime(2024, 1, 1, 12, 0), 30),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        colon_positions = []
        for line in lines[4:7]:
            if ":" in line and "---" not in line:
                colon_positions.append(line.index(":"))

        assert len(set(colon_positions)) == 1, "All colons should be at the same position"

    def test_empty_activities(self):
        model = ProjectSummaryModel([])
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        assert "Project Summary" in result
        assert "Total: 0h00" in result

    def test_single_project(self):
        activities = [
            create_activity("backend: api work", datetime(2024, 1, 1, 9, 0), 180),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        assert "backend: 3h00" in result
        assert "Total  : 3h00" in result

    def test_projects_without_names(self):
        activities = [
            create_activity("standalone task", datetime(2024, 1, 1, 9, 0), 60),
            create_activity("another task", datetime(2024, 1, 1, 10, 0), 30),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        assert ": 1h30" in lines[4]
        assert "Total: 1h30" in lines[6]

    def test_sorting_by_duration(self):
        activities = [
            create_activity("alpha: task1", datetime(2024, 1, 1, 9, 0), 30),
            create_activity("beta: task1", datetime(2024, 1, 1, 10, 0), 90),
            create_activity("gamma: task1", datetime(2024, 1, 1, 12, 0), 60),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = [
            line
            for line in result.split("\n")
            if ":" in line and "Project Summary" not in line and "---" not in line
        ]
        project_lines = [line for line in lines if "Total" not in line]

        assert "beta" in project_lines[0]
        assert "gamma" in project_lines[1]
        assert "alpha" in project_lines[2]

    def test_large_durations(self):
        activities = [
            create_activity("marathon: task1", datetime(2024, 1, 1, 9, 0), 1500),
            create_activity("sprint: task1", datetime(2024, 1, 2, 10, 0), 600),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        assert "marathon: 25h00" in result
        assert "sprint  : 10h00" in result
        assert "Total   : 35h00" in result

    def test_mixed_named_and_unnamed_projects(self):
        activities = [
            create_activity("asd: A-526", datetime(2024, 1, 1, 9, 0), 195),
            create_activity("qwer: b-73", datetime(2024, 1, 1, 12, 15), 45),
            create_activity("hard work", datetime(2024, 1, 1, 13, 0), 60),
            create_activity("A: z-8", datetime(2024, 1, 1, 14, 0), 30),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        assert "asd : 3h15" in lines[4]
        assert "    : 1h00" in lines[5]
        assert "qwer: 0h45" in lines[6]
        assert "A   : 0h30" in lines[7]
        assert "Total: 5h30" in lines[9]

    def test_with_percentages(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 240),
            create_activity("project2: task1", datetime(2024, 1, 1, 13, 0), 120),
            create_activity("project3: task1", datetime(2024, 1, 1, 15, 0), 60),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model, show_perc=True)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        assert "project1: 4h00 ( 57.1%)" in lines[4]
        assert "project2: 2h00 ( 28.6%)" in lines[5]
        assert "project3: 1h00 ( 14.3%)" in lines[6]
        assert "Total   : 7h00 (100.0%)" in lines[8]

    def test_with_percentages_and_current_activity(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 240),
            create_activity("project2: task1", datetime(2024, 1, 1, 13, 0), 120),
            create_activity(
                "-- Current Activity --", datetime(2024, 1, 1, 15, 0), 60, is_current=True
            ),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model, show_perc=True)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        lines = result.split("\n")
        assert "project1: 4h00 ( 57.1%)" in lines[4]
        assert "project2: 2h00 ( 28.6%)" in lines[5]
        assert "-- Current Activity --: 1h00 ( 14.3%)" in lines[6]
        assert "Total   : 7h00 (100.0%)" in lines[8]

    def test_percentages_without_flag(self):
        activities = [
            create_activity("project1: task1", datetime(2024, 1, 1, 9, 0), 240),
            create_activity("project2: task1", datetime(2024, 1, 1, 13, 0), 120),
        ]
        model = ProjectSummaryModel(activities)
        view = ProjectSummaryView(model, show_perc=False)
        output = io.StringIO()

        view.render(output)
        result = output.getvalue()

        assert "%" not in result
        assert "project1: 4h00" in result
        assert "project2: 2h00" in result


class TestAddArgs:
    def test_show_perc_default_false(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args([])
        assert args.show_perc is False

    def test_show_perc_enabled(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--show-perc"])
        assert args.show_perc is True

    def test_current_activity_default(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args([])
        assert args.current_activity == "-- Current Activity --"

    def test_custom_current_activity(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--current-activity", "Working"])
        assert args.current_activity == "Working"

    def test_no_current_activity_default_false(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args([])
        assert args.no_current_activity is False

    def test_no_current_activity_enabled(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--no-current-activity"])
        assert args.no_current_activity is True

    def test_from_date(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--from", "2024-01-01"])
        assert args.from_date == "2024-01-01"

    def test_to_date(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--to", "2024-01-31"])
        assert args.to_date == "2024-01-31"

    def test_project_filter(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--project", "backend"])
        assert args.project == "backend"

    def test_month_with_value(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--month", "2024-01"])
        assert args.month == "2024-01"

    def test_month_defaults_to_this(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--month"])
        assert args.month == "this"

    def test_week_with_value(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--week", "prev"])
        assert args.week == "prev"

    def test_week_defaults_to_this(self):
        parser = argparse.ArgumentParser()
        add_args(parser)
        args = parser.parse_args(["--week"])
        assert args.week == "this"


class TestProjectSummaryHandler:
    def test_handler_renders_output(self):
        activities = [
            create_activity("backend: task1", datetime(2024, 1, 1, 9, 0), 120),
            create_activity("frontend: task1", datetime(2024, 1, 1, 11, 0), 60),
        ]
        args = argparse.Namespace(
            show_perc=False,
            no_current_activity=False,
            current_activity="-- Current Activity --",
        )
        output = io.StringIO()

        handler = ProjectSummaryHandler(args, activities, output)
        handler()

        result = output.getvalue()
        assert "backend : 2h00" in result
        assert "frontend: 1h00" in result
        assert "Total   : 3h00" in result


class TestProjectSummaryCommand:
    def test_command_name(self):
        assert project_summary_command.name == "project-summary"

    def test_command_description(self):
        assert "project" in project_summary_command.description.lower()

    def test_command_handler_class(self):
        assert project_summary_command.handler_class == ProjectSummaryHandler

    def test_command_add_args(self):
        assert project_summary_command.add_args == add_args
