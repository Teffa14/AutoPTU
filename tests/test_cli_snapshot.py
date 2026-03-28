from __future__ import annotations

from typer.testing import CliRunner

from auto_ptu.cli import app


def test_snapshot_command_outputs_turn_info() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["snapshot", "--team-size", "1", "--seed", "1"])
    assert result.exit_code == 0
    assert "Current turn:" in result.stdout
