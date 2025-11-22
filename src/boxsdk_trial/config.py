"""環境変数と Box クライアント設定を扱うモジュール。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from box_sdk_gen.box.developer_token_auth import BoxDeveloperTokenAuth
from box_sdk_gen.box.jwt_auth import BoxJWTAuth, JWTConfig
from box_sdk_gen.client import BoxClient


def _get_env(name: str, default: str | None = None, required: bool = True) -> str | None:
    """環境変数取得のヘルパー。必須値が無ければ ValueError を投げる。"""
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise ValueError(f"Environment variable {name} is required.")
    if value is None or value == "":
        return None
    return value


def _normalize_private_key(raw_key: str) -> str:
    """PEM を環境変数で渡す際の \\n 埋め込みを復元する。"""
    if "-----BEGIN" in raw_key:
        return raw_key.replace("\\n", "\n")
    return raw_key


@dataclass
class BoxSettings:
    """BOX JWT 認証とアプリ設定。"""

    client_id: str | None
    client_secret: str | None
    enterprise_id: str | None
    jwt_private_key: str | None
    jwt_passphrase: str | None
    jwt_key_id: str | None
    upload_folder_id: str
    local_data_dir: Path
    upload_log_path: Path
    app_user_id: str | None = None
    max_retries: int = 3

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "BoxSettings":
        """環境変数 (必要に応じて .env) から設定を読み込む。"""
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        dev_token = os.getenv("BOX_DEVELOPER_TOKEN")
        local_dir = Path(os.getenv("LOCAL_DATA_DIR", "data")).expanduser()
        upload_log = Path(os.getenv("UPLOAD_LOG_PATH", ".upload_log.json")).expanduser()

        return cls(
            client_id=_get_env("BOX_CLIENT_ID", required=not dev_token),
            client_secret=_get_env("BOX_CLIENT_SECRET", required=not dev_token),
            enterprise_id=_get_env("BOX_ENTERPRISE_ID", required=False),
            jwt_private_key=_normalize_private_key(
                _get_env("BOX_JWT_PRIVATE_KEY", required=not dev_token)
            )
            if not dev_token
            else None,
            jwt_passphrase=_get_env("BOX_JWT_PASSPHRASE", required=not dev_token),
            jwt_key_id=_get_env("BOX_JWT_KEY_ID", required=not dev_token),
            upload_folder_id=_get_env("BOX_UPLOAD_FOLDER_ID"),
            local_data_dir=local_dir,
            upload_log_path=upload_log,
            app_user_id=_get_env("BOX_APP_USER_ID", required=False),
            max_retries=int(os.getenv("BOX_MAX_RETRIES", "3")),
        )


def build_client(settings: BoxSettings) -> BoxClient:
    """JWT 認証済みの Box クライアントを返す。"""
    dev_token = os.getenv("BOX_DEVELOPER_TOKEN")
    if dev_token:
        auth = BoxDeveloperTokenAuth(dev_token)
        return BoxClient(auth)

    if settings.enterprise_id is None and settings.app_user_id is None:
        raise ValueError("Provide BOX_ENTERPRISE_ID or BOX_APP_USER_ID (at least one is required).")

    if not all([settings.client_id, settings.client_secret, settings.jwt_key_id, settings.jwt_private_key]):
        raise ValueError("JWT mode requires client_id, client_secret, jwt_key_id, and private key.")

    config = JWTConfig(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        jwt_key_id=settings.jwt_key_id,
        private_key=settings.jwt_private_key,
        private_key_passphrase=settings.jwt_passphrase,
        enterprise_id=settings.enterprise_id,
        user_id=settings.app_user_id,
    )
    auth = BoxJWTAuth(config)
    return BoxClient(auth)
