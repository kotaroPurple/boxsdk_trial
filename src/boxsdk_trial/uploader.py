"""CSV 走査、アップロード、ダミー生成のユーティリティ。"""

from __future__ import annotations

import csv
import json
import logging
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from boxsdk import Client

logger = logging.getLogger(__name__)


def find_csv_files(directory: Path) -> list[Path]:
    """ディレクトリ内の CSV ファイル一覧を返す。"""
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return sorted(path for path in directory.glob("*.csv") if path.is_file())


class UploadLog:
    """アップロード済みファイルを JSON で管理する。"""

    def __init__(self, path: Path):
        self.path = path
        self._uploaded: set[str] = set()
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self._uploaded = set(data.get("uploaded", []))
            except json.JSONDecodeError:
                logger.warning("Failed to parse upload log. Starting fresh.")
                self._uploaded = set()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"uploaded": sorted(self._uploaded)}
        self.path.write_text(json.dumps(payload, indent=2))

    def is_uploaded(self, file_path: Path) -> bool:
        return str(file_path.resolve()) in self._uploaded

    def mark_uploaded(self, file_path: Path) -> None:
        self._uploaded.add(str(file_path.resolve()))


@dataclass
class UploadStats:
    attempted: int = 0
    skipped: int = 0
    succeeded: int = 0
    failed: int = 0


def upload_directory(
    client: Client,
    folder_id: str,
    files: Iterable[Path],
    log: UploadLog,
    max_retries: int = 3,
) -> UploadStats:
    """CSV 群を BOX にアップロードする。"""
    stats = UploadStats()
    for path in files:
        if log.is_uploaded(path):
            stats.skipped += 1
            continue
        stats.attempted += 1
        try:
            _upload_with_retry(client, folder_id, path, max_retries)
            log.mark_uploaded(path)
            stats.succeeded += 1
            logger.info("Uploaded %s", path.name)
        except Exception as exc:  # noqa: BLE001
            stats.failed += 1
            logger.error("Failed to upload %s: %s", path.name, exc)
    log.save()
    return stats


def _upload_with_retry(client: Client, folder_id: str, file_path: Path, max_retries: int) -> None:
    attempts = 0
    delay = 0.5
    while True:
        try:
            with file_path.open("rb") as stream:
                client.folder(folder_id).upload_stream(stream, file_name=file_path.name)
            return
        except Exception:  # noqa: BLE001
            attempts += 1
            if attempts > max_retries:
                raise
            time.sleep(delay)
            delay *= 2


def create_dummy_files(directory: Path, rows: int, files: int) -> list[Path]:
    """テスト用のダミー CSV を生成する。"""
    directory.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for index in range(files):
        path = directory / f"dummy_{index:03d}.csv"
        with path.open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp", "sensor_a", "sensor_b"])
            base_ts = int(time.time())
            for row_idx in range(rows):
                writer.writerow(
                    [
                        base_ts + row_idx,
                        round(random.uniform(0, 1), 5),
                        round(random.uniform(0, 1), 5),
                    ]
                )
        generated.append(path)
    return generated
