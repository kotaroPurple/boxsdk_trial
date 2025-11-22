from pathlib import Path
from types import SimpleNamespace

import pytest

from boxsdk_trial.uploader import UploadLog, create_dummy_files, upload_directory


class FakeUploads:
    def __init__(self) -> None:
        self.uploaded: list[str] = []

    def upload_file(self, attributes, file, file_file_name=None, **kwargs):  # noqa: ANN001,ARG002
        file.read()
        self.uploaded.append(file_file_name or attributes.name)
        return SimpleNamespace(id="file-id", name=file_file_name)


class FakeClient:
    def __init__(self, uploads: FakeUploads) -> None:
        self.uploads = uploads


def test_create_dummy_files(tmp_path: Path) -> None:
    files = create_dummy_files(tmp_path, rows=3, files=2)
    assert len(files) == 2
    assert all(path.exists() for path in files)
    content = files[0].read_text().splitlines()
    assert content[0] == "timestamp,sensor_a,sensor_b"
    assert len(content) == 4  # header + 3 rows


def test_upload_directory_skips_uploaded(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    created = create_dummy_files(data_dir, rows=1, files=2)
    log = UploadLog(tmp_path / "log.json")
    log.mark_uploaded(created[0])
    log.save()

    uploads = FakeUploads()
    client = FakeClient(uploads)

    stats = upload_directory(
        client=client,
        folder_id="123",
        files=created,
        log=log,
        max_retries=1,
    )

    assert stats.skipped == 1
    assert stats.succeeded == 1
    assert len(uploads.uploaded) == 1
    assert uploads.uploaded[0] == created[1].name
