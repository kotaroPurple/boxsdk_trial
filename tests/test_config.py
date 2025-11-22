import os
from pathlib import Path

import pytest

from boxsdk_trial.config import BoxSettings, build_client


def test_from_env_accepts_user_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BOX_CLIENT_ID", "cid")
    monkeypatch.setenv("BOX_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("BOX_JWT_KEY_ID", "kid")
    monkeypatch.setenv("BOX_JWT_PRIVATE_KEY", "dummy")
    monkeypatch.setenv("BOX_JWT_PASSPHRASE", "pass")
    monkeypatch.setenv("BOX_UPLOAD_FOLDER_ID", "fid")
    monkeypatch.setenv("BOX_APP_USER_ID", "user123")
    # BOX_ENTERPRISE_ID intentionally unset

    settings = BoxSettings.from_env()
    assert settings.enterprise_id is None
    assert settings.app_user_id == "user123"


def test_build_client_requires_one_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOX_CLIENT_ID", "cid")
    monkeypatch.setenv("BOX_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("BOX_JWT_KEY_ID", "kid")
    monkeypatch.setenv("BOX_JWT_PRIVATE_KEY", "dummy")
    monkeypatch.setenv("BOX_JWT_PASSPHRASE", "pass")
    monkeypatch.setenv("BOX_UPLOAD_FOLDER_ID", "fid")
    # Neither enterprise nor app user set

    settings = BoxSettings.from_env()
    with pytest.raises(ValueError):
        build_client(settings)
