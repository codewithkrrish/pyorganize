"""Tests for pyorganize's core engine."""

from pyorganize.organizer import (
    apply_moves,
    category_for,
    load_rules,
    plan_moves,
    undo,
)


def _make_files(tmp_path):
    (tmp_path / "photo.jpg").write_text("x")
    (tmp_path / "song.mp3").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "weird.xyz").write_text("x")


def test_plan_groups_by_type(tmp_path):
    _make_files(tmp_path)
    moves = plan_moves(tmp_path)
    mapping = {m.src.name: m.dest.parent.name for m in moves}
    assert mapping == {
        "photo.jpg": "Images",
        "song.mp3": "Audio",
        "notes.txt": "Documents",
        "weird.xyz": "Others",
    }


def test_apply_and_undo_roundtrip(tmp_path):
    _make_files(tmp_path)
    moves = plan_moves(tmp_path)
    apply_moves(moves, tmp_path)
    assert (tmp_path / "Images" / "photo.jpg").exists()
    restored = undo(tmp_path)
    assert restored == 4
    assert (tmp_path / "photo.jpg").exists()
    assert not (tmp_path / "Images").exists()


def test_name_collision_gets_numbered(tmp_path):
    (tmp_path / "a.txt").write_text("new")
    docs = tmp_path / "Documents"
    docs.mkdir()
    (docs / "a.txt").write_text("old")
    moves = plan_moves(tmp_path)
    assert moves[0].dest.name == "a (1).txt"


def test_custom_rules(tmp_path):
    rules = load_rules(None)
    assert category_for(".py", rules) == "Code"
    custom = tmp_path / "rules.json"
    custom.write_text('{"Design": [".fig", "psd"]}')
    rules = load_rules(custom)
    assert category_for(".fig", rules) == "Design"
    assert category_for(".PSD", rules) == "Design"


def test_plan_does_not_touch_anything(tmp_path):
    _make_files(tmp_path)
    moves = plan_moves(tmp_path)
    assert len(moves) == 4
    assert (tmp_path / "photo.jpg").exists()  # planning alone moves nothing


def test_organize_by_date(tmp_path):
    _make_files(tmp_path)
    moves = plan_moves(tmp_path, by="date")
    assert len(moves) == 4
    assert all(len(m.dest.parent.name) == 7 for m in moves)  # YYYY-MM
