from __future__ import annotations

import re
from pathlib import Path
from typing import List, Sequence
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pandas as pd


DEFAULT_CITIBIKE_INDEX = "https://s3.amazonaws.com/tripdata/"
DEFAULT_BAYWHEELS_INDEX = "https://s3.amazonaws.com/baywheels-data/"


def parse_index_links(html: str, base_url: str) -> List[str]:
    """Extract downloadable tripdata links from an S3 bucket listing.

    The bucket root returns a raw `ListBucketResult` XML document (`<Key>`
    entries); the old `index.html` page rendered its listing client-side via
    JS, so scraping `<a href>` tags from it found nothing. Both `<Key>` and
    `<a href>` are parsed here so either input still works.
    """
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    key_pattern = re.compile(r"<Key>([^<]+)</Key>", re.IGNORECASE)
    candidates = href_pattern.findall(html) + key_pattern.findall(html)

    links = []
    for ref in candidates:
        if ref.startswith(("http://", "https://")):
            candidate = ref
        else:
            candidate = urljoin(base_url, ref)

        if candidate.lower().endswith((".zip", ".csv", ".csv.zip", ".gz")):
            links.append(candidate)

    return links


def _extract_year_month(url: str) -> tuple[int, int] | None:
    match = re.search(r"(\d{4})(\d{2})", url)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def choose_recent_files(urls: Sequence[str], months: int = 6) -> List[str]:
    """Choose the most recent files from a list of URLs containing YYYYMM in the name."""
    parsed = []
    for url in urls:
        year_month = _extract_year_month(url)
        if year_month is None:
            continue
        year, month = year_month
        parsed.append((year * 100 + month, url))

    parsed.sort(key=lambda item: item[0])
    if not parsed:
        return []

    selected = [url for _, url in parsed[-months:]]
    return selected


def choose_files_in_range(
    urls: Sequence[str], start: tuple[int, int], end: tuple[int, int]
) -> List[str]:
    """Choose files whose YYYYMM falls within [start, end], inclusive."""
    start_key = start[0] * 100 + start[1]
    end_key = end[0] * 100 + end[1]

    parsed = []
    for url in urls:
        year_month = _extract_year_month(url)
        if year_month is None:
            continue
        key = year_month[0] * 100 + year_month[1]
        if start_key <= key <= end_key:
            parsed.append((key, url))

    parsed.sort(key=lambda item: item[0])
    return [url for _, url in parsed]


def fetch_index(index_url: str) -> str:
    request = Request(index_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def download_tripdata(
    index_url: str,
    output_dir: str | Path | None = None,
    months: int = 6,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> List[Path]:
    """Download tripdata archives from an S3 index page.

    If `start`/`end` (year, month) tuples are given, downloads files in that
    inclusive range instead of the `months` most recent files.
    """
    output_dir = Path(output_dir or "data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    html = fetch_index(index_url)
    links = parse_index_links(html, base_url=index_url)

    if start is not None and end is not None:
        selected_links = choose_files_in_range(links, start=start, end=end)
    else:
        selected_links = choose_recent_files(links, months=months)

    downloaded_files: List[Path] = []
    for url in selected_links:
        filename = Path(url.split("/")[-1])
        destination = output_dir / filename
        if destination.exists():
            downloaded_files.append(destination)
            continue

        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())
        downloaded_files.append(destination)

    return downloaded_files


def load_downloaded_tripdata(paths: Sequence[str | Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        path = Path(path)
        if path.suffix == ".zip":
            frames.append(pd.read_csv(path, compression="zip"))
        else:
            frames.append(pd.read_csv(path))

    if not frames:
        raise ValueError("No tripdata files were available to load")

    return pd.concat(frames, ignore_index=True)
