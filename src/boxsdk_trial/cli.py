"""CLI エントリーポイント。"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import BoxSettings, build_client
from .uploader import UploadLog, create_dummy_files, find_csv_files, upload_directory


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Upload CSV files to BOX using JWT authentication."
    )
    parser.add_argument("--env-file", type=Path, help=".env path (default: auto-detect)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload", help="Upload CSV files to BOX")
    upload_parser.add_argument("--limit", type=int, default=None, help="Limit number of files")

    dummy_parser = subparsers.add_parser("make-dummy", help="Generate dummy CSV files")
    dummy_parser.add_argument("--rows", type=int, default=5, help="Rows per file")
    dummy_parser.add_argument("--files", type=int, default=3, help="Number of files")
    dummy_parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Destination directory (default: LOCAL_DATA_DIR)",
    )

    list_parser = subparsers.add_parser("list", help="List CSV files and upload status")
    list_parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Target directory (default: LOCAL_DATA_DIR)",
    )

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    settings = BoxSettings.from_env(args.env_file)
    data_dir = args.dir if hasattr(args, "dir") and args.dir else settings.local_data_dir

    if args.command == "make-dummy":
        created = create_dummy_files(data_dir, rows=args.rows, files=args.files)
        for path in created:
            logging.info("Created %s", path)
        logging.info("Dummy generation completed: %d file(s) under %s", len(created), data_dir)
        return 0

    log = UploadLog(settings.upload_log_path)

    if args.command == "list":
        files = find_csv_files(data_dir)
        if not files:
            print(f"No CSV files found in {data_dir}")
            return 0
        for path in files:
            status = "uploaded" if log.is_uploaded(path) else "pending"
            print(f"{path.name}\t{status}")
        return 0

    if args.command == "upload":
        files = find_csv_files(settings.local_data_dir)
        if not files:
            logging.info("No CSV files found in %s", settings.local_data_dir)
            return 0

        if args.limit:
            files = files[: args.limit]

        logging.info("Found %d CSV files. Starting upload...", len(files))
        client = build_client(settings)
        stats = upload_directory(
            client=client,
            folder_id=settings.upload_folder_id,
            files=files,
            log=log,
            max_retries=settings.max_retries,
        )
        logging.info(
            "Upload done: attempted=%d, succeeded=%d, failed=%d, skipped=%d",
            stats.attempted,
            stats.succeeded,
            stats.failed,
            stats.skipped,
        )
        if stats.failed:
            logging.error("Some files failed to upload. See logs above.")
        return 0 if stats.failed == 0 else 1

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli())
