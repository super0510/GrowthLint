"""Tests for GrowthLint CLI commands."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from growthlint.cli import app

runner = CliRunner()


class TestScanCommand:

    def test_scan_local_directory(self):
        result = runner.invoke(app, ["scan", "tests/fixtures/sample_react_site/"])
        assert result.exit_code == 0
        assert "Growth Score" in result.output or "Growth Audit" in result.output

    def test_scan_json_format(self):
        result = runner.invoke(app, ["scan", "tests/fixtures/sample_react_site/", "--format", "json"])
        assert result.exit_code == 0
        # The output should contain valid JSON somewhere
        assert '"score"' in result.output or '"violations"' in result.output

    def test_scan_csv_format(self):
        result = runner.invoke(app, ["scan", "tests/fixtures/sample_react_site/", "--format", "csv"])
        assert result.exit_code == 0
        # CSV output contains "Rule ID" header and comma-separated data
        assert "Rule ID" in result.output or "no-analytics" in result.output

    def test_scan_with_platform_override(self):
        result = runner.invoke(app, ["scan", "tests/fixtures/sample_react_site/", "--platform", "static"])
        assert result.exit_code == 0

    def test_scan_with_category_filter(self):
        result = runner.invoke(app, ["scan", "tests/fixtures/sample_react_site/", "--categories", "seo"])
        assert result.exit_code == 0


class TestCheckPRCommand:

    def test_check_pr_local(self):
        result = runner.invoke(app, ["check-pr", "tests/fixtures/sample_react_site/"])
        # Will likely fail the check (low score) but should not crash
        assert result.exit_code in (0, 1)

    def test_check_pr_with_min_score(self):
        result = runner.invoke(app, ["check-pr", "tests/fixtures/sample_react_site/", "--min-score", "0"])
        # May fail due to critical violations (fail_on_new_critical defaults True)
        assert result.exit_code in (0, 1)
        assert "CI" in result.output or "Score" in result.output


class TestVersionFlag:

    def test_version_output(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "GrowthLint" in result.output

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        # Typer returns exit code 0 for no_args_is_help
        assert result.exit_code in (0, 2)
        assert "scan" in result.output.lower() or "usage" in result.output.lower() or "growthlint" in result.output.lower()
