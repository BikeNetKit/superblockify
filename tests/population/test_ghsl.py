"""Tests for the ghsl module."""

from io import BytesIO
from os.path import basename, isfile, join
from zipfile import ZipFile

import pytest
from affine import Affine
from geopandas import GeoDataFrame
from numpy import ndarray

from superblockify.config import Config
from superblockify.population import ghsl

GHSL_TIF = join(
    Config.TEST_DATA_PATH,
    "ghsl",
    "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C29.tif",
)


class _FakeResponse:  # pylint: disable=too-few-public-methods
    """Minimal requests response for mocked downloads."""

    def __init__(self, content=b"", status_code=200, content_type="application/zip"):
        self.content = content
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}


def _zip_bytes(url):
    """Create an in-memory zip with the raster name expected by download_ghsl."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        zip_file.writestr(basename(url)[:-4] + ".tif", b"fake tif")
    return buffer.getvalue()


@pytest.mark.parametrize(
    "resample_factor, no_window",
    [
        (1 / 2, False),
        (1, False),
        (2, False),
        (1 / 100, True),
    ],
)
def test_resample_load_window_gdf(
    resample_factor, no_window, test_one_city_copy, monkeypatch
):
    """Test loading and resampling a gdf window of a raster file."""
    monkeypatch.setattr(ghsl, "get_ghsl", lambda bbox: GHSL_TIF)
    _, graph = test_one_city_copy
    # Get mollweide bounding box
    boundary_polygon = graph.graph["boundary"]
    crs = graph.graph["boundary_crs"]
    boundary_gdf = GeoDataFrame(geometry=[boundary_polygon], crs=crs).to_crs(
        "World Mollweide"
    )
    raster_rescaled, res_affine = ghsl.resample_load_window(
        GHSL_TIF,
        resample_factor=resample_factor,
        window=boundary_gdf if not no_window else None,
    )
    assert isinstance(raster_rescaled, ndarray)
    assert isinstance(res_affine, Affine)


@pytest.mark.parametrize("window", [True, False, 1, 1.0, "test"])
def test_resample_load_window_gdf_wrong_type(window):
    """Test loading and resampling a gdf window with wrong type."""
    with pytest.raises(TypeError):
        ghsl.resample_load_window(
            GHSL_TIF,
            resample_factor=1,
            window=window,
        )


@pytest.mark.parametrize(
    "y_moll, x_moll, row, col",
    [
        (-1, -1, 10, 19),
        (-1, 1, 10, 19),
        (1, 1, 9, 19),
        (1, -1, 9, 19),
        (-1, -40000, 10, 19),
        (-1, -42000, 10, 18),
        (-1, 958000, 10, 19),
        (-1, 959001, 10, 20),
        (-1, -18040999, 10, 1),
        (-1, -17040999, 10, 2),
        (-1, 16958999, 10, 35),
        (-1, 16959001, 10, 36),
        (-1, 18040999, 10, 36),
        (9.9e5, -1e5, 9, 18),
        (9.9e5, 1e5, 9, 19),
        (10.1e5, 1e5, 8, 19),
        (10.1e5, -1e5, 8, 18),
        (89e5, -179e5, 1, 1),
        (89e5, 179e5, 1, 36),
        (-89e5, 179e5, 18, 36),
        (-89e5, -179e5, 18, 1),
        (6064791.288371984, 553663.6837159488, 3, 19),
        (6087463.855133052, 553663.6837159488, 3, 19),
        (6064791.288371984, 576088.653201773, 3, 19),
        (6087463.855133052, 576088.653201773, 3, 19),
        (4.4711754e5, -74.2235137e5, 9, 11),
        (4.4711754e5, -74.0102577e5, 9, 11),
        (4.8331695e5, -74.0102577e5, 9, 11),
        (4.8331695e5, -74.2235137e5, 9, 11),
    ],
)
def test_row_col(y_moll, x_moll, row, col):
    """Test the row_col function."""
    assert ghsl.row_col(y_moll, x_moll) == (row, col)


@pytest.mark.parametrize(
    "bbox_moll, urls",
    [
        (
            [1, 1, 2, 2],
            [
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R9_C19.zip",
            ],
        ),
        (
            [-1, -1, 1, 1],
            [
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R9_C19.zip",
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C19.zip",
            ],
        ),
        (
            [-1, -1, 1, 1],
            [
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R9_C19.zip",
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C19.zip",
            ],
        ),
        (
            [-42000, -1, 0, 1],
            [
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R9_C19.zip",
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C19.zip",
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R9_C18.zip",
                "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
                "/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles"
                "/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C18.zip",
            ],
        ),
    ],
)
def test_get_ghsl_urls(bbox_moll, urls):
    """Test the get_GHSL_urls function."""
    assert set(ghsl.get_ghsl_urls(bbox_moll)) == set(urls)


@pytest.mark.parametrize(
    "bbox_moll",
    [
        [0, 0, 2.1e6, 1],
        [0, 0, 7.1e6, 1],
        [-7e6, 0, -4e6, 1],
        [0, 0, 1, 2.1e6],
        [0, 0, 1, 7.1e6],
        [0, -7e6, 1, -4e6],
        [-4e6, 3e6, 2e6, 6e6],
    ],
)
def test_get_ghsl_urls_invalid_bbox(bbox_moll):
    """Test the get_GHSL_urls function with invalid bbox."""
    with pytest.raises(ValueError):
        ghsl.get_ghsl_urls(bbox_moll)


BASE_PATH = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/"


@pytest.mark.parametrize(
    "urls",
    [
        BASE_PATH + "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R2_C30.zip",
        [
            BASE_PATH + "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R2_C30.zip",
            BASE_PATH + "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R7_C2.zip",
        ],
    ],
)
def test_download_ghsl(urls, tmp_path, monkeypatch):
    """Test the download_ghsl function with mocked downloads."""
    monkeypatch.setattr(
        ghsl.requests,
        "get",
        lambda url, timeout=None: _FakeResponse(_zip_bytes(url)),
    )
    filepaths = ghsl.download_ghsl(urls, save_dir=str(tmp_path))
    assert (
        isinstance(filepaths, list)
        and isinstance(urls, list)
        or isinstance(filepaths, str)
        and isinstance(urls, str)
    )
    # Check files exist in save_dir
    for filepath in filepaths if isinstance(filepaths, list) else [filepaths]:
        assert isfile(filepath)


@pytest.mark.parametrize(
    "url,status_code,content_type",
    [
        (  # non-existent tile
            "GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles/"
            "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R18_C27.zip",
            404,
            "application/zip",
        ),
        (  # non-zip file
            "copyright.txt",
            200,
            "text/plain",
        ),
    ],
)
def test_download_ghsl_invalid_urls(
    url, status_code, content_type, tmp_path, monkeypatch
):
    """Test the download_ghsl function with invalid urls."""
    monkeypatch.setattr(
        ghsl.requests,
        "get",
        lambda *args, **kwargs: _FakeResponse(
            b"", status_code=status_code, content_type=content_type
        ),
    )
    with pytest.raises(ValueError):
        ghsl.download_ghsl(BASE_PATH + url, save_dir=str(tmp_path))


def test_download_ghsl_create_save_dir(tmp_path, monkeypatch):
    """Test the download_ghsl function with non-existent save_dir."""
    url = BASE_PATH + (
        "GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles/"
        "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R18_C26.zip"
    )
    monkeypatch.setattr(
        ghsl.requests,
        "get",
        lambda *args, **kwargs: _FakeResponse(_zip_bytes(url)),
    )
    save_dir = tmp_path / "non-existent-dir"
    ghsl.download_ghsl(url, save_dir=str(save_dir))
    # Check files exist in save_dir
    assert isfile(join(str(save_dir), basename(url)[:-4] + ".tif"))


def test_download_ghsl_connection_error(tmp_path, monkeypatch):
    """Test the download_ghsl function for a connection error."""

    def fake_get(*args, **kwargs):
        raise ghsl.requests.exceptions.ConnectionError("connection error")

    monkeypatch.setattr(ghsl.requests, "get", fake_get)
    with pytest.raises(ValueError):
        ghsl.download_ghsl("https://non-existent-url.com", save_dir=str(tmp_path))


def test_download_ghsl_connection_timeout(tmp_path, monkeypatch):
    """Test the download_ghsl function for a connection timeout."""

    def fake_get(*args, **kwargs):
        raise ghsl.requests.exceptions.Timeout("timeout")

    monkeypatch.setattr(ghsl.requests, "get", fake_get)
    with pytest.raises(ValueError):
        ghsl.download_ghsl(
            BASE_PATH + "does-not-matter.zip",
            save_dir=str(tmp_path),
            timeout=0.0001,
        )


@pytest.mark.parametrize(
    "full_raster, bbox_moll, expected",
    [
        (
            join(
                Config.TEST_DATA_PATH,
                "ghsl",
                "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C29.tif",
            ),
            None,
            join(
                Config.TEST_DATA_PATH,
                "ghsl",
                "GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R10_C29.tif",
            ),
        ),
        (
            None,
            [1, 1, 2, 2],
            None,
        ),
        (
            False,
            [1, 1, 2, 2],
            None,
        ),
        (
            None,
            [-1, -1, 1, 1],
            None,
        ),
    ],
)
def test_get_ghsl(full_raster, bbox_moll, expected, monkeypatch):
    """Test the get_ghsl_urls function.
    Overwrite the config.Config.FULL_RASTER value with full_raster.
    """
    monkeypatch.setattr(Config, "FULL_RASTER", full_raster)
    # mock download_ghsl not to download the files
    monkeypatch.setattr(ghsl, "download_ghsl", lambda ghsl_urls: ghsl_urls)
    urls = ghsl.get_ghsl(bbox_moll=bbox_moll)
    if isinstance(expected, str):
        assert urls == expected
    if expected is None:
        assert set(urls) == set(ghsl.get_ghsl_urls(bbox_moll))


@pytest.mark.parametrize(
    "full_raster, bbox_moll",
    [
        (  # faulty full_raster
            "non-existent",
            None,
        ),
        (  # no rasters
            None,
            None,
        ),
        (  # bbox outside World Mollweide
            None,
            [-181e5, -91e5, 181e5, 91e5],
        ),
    ],
)
def test_get_ghsl_invalid(full_raster, bbox_moll, monkeypatch):
    """Test the get_ghsl_urls with invalid inputs.
    Overwrite the config.Config.FULL_RASTER value with full_raster.
    """
    monkeypatch.setattr(Config, "FULL_RASTER", full_raster)
    with pytest.raises(ValueError):
        ghsl.get_ghsl(bbox_moll=bbox_moll)
