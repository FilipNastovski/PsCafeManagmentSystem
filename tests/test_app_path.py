"""Tests for utils/app_path."""
import os
import sys
import pytest

from utils.app_path import _is_frozen, get_data_path, get_resource_path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestIsFrozen:
    def test_not_frozen_in_dev(self):
        assert _is_frozen() is False

    def test_frozen_when_sys_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        assert _is_frozen() is True


class TestGetDataPath:
    def test_dev_mode_returns_project_root(self):
        result = get_data_path("pscafe.db")
        expected = os.path.join(PROJECT_ROOT, "pscafe.db")
        assert result == expected

    def test_dev_mode_log_path(self):
        result = get_data_path("pscafe.log")
        expected = os.path.join(PROJECT_ROOT, "pscafe.log")
        assert result == expected

    def test_dev_mode_creates_dir_for_platformdirs(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

        fake_data_dir = str(tmp_path / "data")
        monkeypatch.setattr("platformdirs.user_data_dir", lambda app: fake_data_dir)

        result = get_data_path("pscafe.db")
        expected = os.path.join(fake_data_dir, "pscafe.db")
        assert result == expected
        assert os.path.isdir(fake_data_dir)


class TestGetResourcePath:
    def test_dev_mode_icon(self):
        result = get_resource_path("resources/icon.png")
        expected = os.path.join(PROJECT_ROOT, "resources", "icon.png")
        assert result == expected
        assert os.path.exists(result)

    def test_dev_mode_alert(self):
        result = get_resource_path("resources/alert.wav")
        expected = os.path.join(PROJECT_ROOT, "resources", "alert.wav")
        assert result == expected
        assert os.path.exists(result)

    def test_frozen_mode_uses_meipass(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        meipass = str(tmp_path / "_internal")
        os.makedirs(meipass)
        monkeypatch.setattr(sys, "_MEIPASS", meipass, raising=False)

        result = get_resource_path("resources/icon.png")
        expected = os.path.join(meipass, "resources", "icon.png")
        assert result == expected

    def test_frozen_mode_nested_path(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        meipass = str(tmp_path / "extracted")
        os.makedirs(meipass)
        monkeypatch.setattr(sys, "_MEIPASS", meipass, raising=False)

        result = get_resource_path("some/deep/file.txt")
        expected = os.path.join(meipass, "some", "deep", "file.txt")
        assert result == expected
