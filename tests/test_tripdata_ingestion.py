from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.ingest_tripdata import choose_files_in_range, choose_recent_files, parse_index_links


def test_parse_index_links_extracts_tripdata_urls():
    html = """
    <html><body>
      <a href="202401-citibike-tripdata.csv.zip">zip</a>
      <a href="202402-citibike-tripdata.csv.zip">zip2</a>
      <a href="README.md">readme</a>
    </body></html>
    """

    links = parse_index_links(html, base_url="https://s3.amazonaws.com/tripdata/")

    assert links == [
        "https://s3.amazonaws.com/tripdata/202401-citibike-tripdata.csv.zip",
        "https://s3.amazonaws.com/tripdata/202402-citibike-tripdata.csv.zip",
    ]


def test_choose_recent_files_prefers_latest_months():
    urls = [
        "https://s3.amazonaws.com/baywheels-data/202301-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202402-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202403-baywheels-tripdata.zip",
    ]

    selected = choose_recent_files(urls, months=2)

    assert selected == [
        "https://s3.amazonaws.com/baywheels-data/202402-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202403-baywheels-tripdata.zip",
    ]


def test_choose_files_in_range_filters_inclusive_bounds():
    urls = [
        "https://s3.amazonaws.com/baywheels-data/202406-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202407-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202412-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202501-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202508-baywheels-tripdata.zip",
    ]

    selected = choose_files_in_range(urls, start=(2024, 7), end=(2025, 1))

    assert selected == [
        "https://s3.amazonaws.com/baywheels-data/202407-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202412-baywheels-tripdata.zip",
        "https://s3.amazonaws.com/baywheels-data/202501-baywheels-tripdata.zip",
    ]
