import json

from claude_kit.storage import KitState, VersionStatus, read_state, write_state


def test_a_state_round_trips(tmp_path):
    path = tmp_path / "state.json"
    state = KitState(
        checked_at="2026-09-01T12:00:00+00:00",
        message="claude-kit 0.2.0 is out",
        versions={"claude-kit": VersionStatus(installed="0.1.0", available="0.2.0", behind_by=1)},
        announced={"claude-kit": "0.2.0"},
    )
    write_state(path, state)
    assert read_state(path) == state


def test_writing_leaves_no_temporary_file(tmp_path):
    path = tmp_path / "state.json"
    write_state(path, KitState())
    assert [entry.name for entry in tmp_path.iterdir()] == ["state.json"]


def test_empty_values_are_left_out_of_the_file(tmp_path):
    path = tmp_path / "state.json"
    write_state(path, KitState(versions={"claude-kit": VersionStatus(installed="0.1.0")}))
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["versions"]["claude-kit"] == {"installed": "0.1.0"}
    assert "message" not in written


def test_a_missing_file_reads_as_the_default(tmp_path):
    assert read_state(tmp_path / "absent.json") == KitState()


def test_unparsable_json_reads_as_the_default(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")
    assert read_state(path) == KitState()


def test_json_that_is_not_an_object_reads_as_the_default(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert read_state(path) == KitState()


def test_fields_of_the_wrong_type_fall_back_one_by_one(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(
        json.dumps(
            {
                "notice_version": "two",
                "check_interval_hours": None,
                "checked_at": 17,
                "versions": "not a mapping",
                "announced": {"claude-kit": 2},
            }
        ),
        encoding="utf-8",
    )
    default = KitState()
    read = read_state(path)
    assert read.notice_version == default.notice_version
    assert read.check_interval_hours == default.check_interval_hours
    assert read.checked_at == "17"
    assert read.versions == {}
    assert read.announced == {"claude-kit": "2"}


def test_a_boolean_is_not_an_integer_for_behind_by(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(
        json.dumps({"versions": {"claude-kit": {"behind_by": True}}}), encoding="utf-8"
    )
    assert read_state(path).versions["claude-kit"].behind_by is None


def test_a_version_that_is_not_an_object_is_dropped(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(
        json.dumps({"versions": {"claude-kit": "0.1.0"}}), encoding="utf-8"
    )
    assert read_state(path).versions == {}
