#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crawlers.adapters.met import MET_TEENS_FREE_WORKSHOPS_URL, parse_met_events_html
from src.crawlers.pipeline.runner import upsert_extracted_activities


DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "html" / "met"


def _json_ready(row: dict) -> dict:
    out = dict(row)
    for key in ("start_at", "end_at"):
        value = out.get(key)
        if isinstance(value, datetime):
            out[key] = value.isoformat()
    return out


def _write_text_dump(html: str, dump_dir: Path, *, source_html_path: Path | None = None) -> Path:
    dump_dir.mkdir(parents=True, exist_ok=True)
    if source_html_path is not None:
        output_path = dump_dir / f"{source_html_path.stem}.txt"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = dump_dir / f"met_events_{stamp}.txt"

    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _creation_timestamp(path: Path) -> float:
    stat = path.stat()
    return getattr(stat, "st_birthtime", stat.st_ctime)


def _resolve_input_html_path(*, input_html: str | None, cache_dir: Path) -> Path:
    if input_html:
        input_path = Path(input_html)
        if not input_path.exists():
            print(f"Input HTML file not found: {input_path}")
            raise SystemExit(1)
        return input_path

    html_files = [path for path in cache_dir.glob("*.html") if path.is_file()]
    if not html_files:
        print(f"No HTML files found in cache directory: {cache_dir}")
        print("Provide --input-html or place an HTML file under data/html/met.")
        raise SystemExit(1)

    return max(html_files, key=_creation_timestamp)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse MET teens/free/workshops events from local HTML. "
            "Print parsed rows, and optionally commit to DB."
        )
    )
    parser.add_argument("--url", default=MET_TEENS_FREE_WORKSHOPS_URL)
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help="Directory used to auto-select the newest HTML file (default: data/html/met).",
    )
    parser.add_argument(
        "--input-html",
        default=None,
        help="Parse from a specific local HTML file. If omitted, load newest HTML in --cache-dir.",
    )
    parser.add_argument(
        "--dump-text",
        action="store_true",
        help="Write normalized page text lines to a .txt file for parser debugging.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="When set, upsert parsed rows into MySQL.",
    )
    args = parser.parse_args()

    input_path = _resolve_input_html_path(input_html=args.input_html, cache_dir=Path(args.cache_dir))
    print(f"Loading HTML from file: {input_path}")
    html = input_path.read_text(encoding="utf-8")

    if args.dump_text:
        dump_path = _write_text_dump(html, Path(args.cache_dir), source_html_path=input_path)
        print(f"Saved text dump to: {dump_path}")

    parsed = parse_met_events_html(html=html, list_url=args.url)

    print(f"Parsed rows: {len(parsed)}")
    for row in parsed:
        print(json.dumps(_json_ready(asdict(row)), ensure_ascii=True))

    if not args.commit:
        print("Dry run only. Pass --commit to write to DB.")
        return

    persisted = upsert_extracted_activities(
        source_url=args.url,
        extracted=parsed,
        adapter_type="met_events_filtered",
    )
    print(f"Committed rows (deduped input size): {len(persisted)}")


if __name__ == "__main__":
    asyncio.run(main())
