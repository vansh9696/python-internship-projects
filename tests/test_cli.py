import json
import pytest
from unittest.mock import patch
from devcheck.cli import main
from devcheck.inspector import check_disk_space, check_developer_tools

def test_check_disk_space_pass():
    res = check_disk_space(".", min_free_gb=0.001)
    assert res["status"] == "PASS"
    assert res["free_gb"] > 0

def test_missing_developer_tool():
    res = check_developer_tools(["this_executable_should_never_exist_xyz123"])
    assert res["status"] == "FAIL"
    assert res["tools"]["this_executable_should_never_exist_xyz123"]["found"] is False

def test_cli_json_success(capsys):
    with patch("devcheck.inspector.check_developer_tools") as mock_tools:
        mock_tools.return_value = {"tools": {}, "status": "PASS"}
        code = main(["--json"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["overall_status"] == "PASS"

def test_cli_missing_dependency_exit_code(capsys):
    with patch("devcheck.inspector.DEFAULT_REQUIRED_TOOLS", ["non_existent_binary_xyz"]):
        code = main([])
        assert code == 1

def test_cli_missing_config_path(capsys):
    code = main(["--config", "non_existent_file.txt"])
    assert code == 2
    captured = capsys.readouterr()
    assert "Configuration Error" in captured.err

def test_cli_malformed_config_path(tmp_path, capsys):
    empty_cfg = tmp_path / "empty.txt"
    empty_cfg.write_text("# only comments\n\n")
    code = main(["--config", str(empty_cfg)])
    assert code == 3
    captured = capsys.readouterr()
    assert "Malformed Configuration" in captured.err