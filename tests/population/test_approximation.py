"""Tests for the population approximation module."""

import pytest
from geopandas import GeoDataFrame
from networkx import ego_graph
from numpy import float32, ones
from rasterio import open as rasopen
from rasterio.transform import from_origin

from superblockify.population import approximation
from superblockify.population.approximation import (
    add_edge_population,
    get_population_area,
    get_edge_population,
)


@pytest.fixture
def fake_ghsl_raster(tmp_path, test_city_small_copy):
    """Create a small local raster covering the test city."""
    _, graph = test_city_small_copy
    boundary = GeoDataFrame(
        geometry=[graph.graph["boundary"]], crs=graph.graph["boundary_crs"]
    ).to_crs("World Mollweide")
    minx, miny, maxx, maxy = boundary.total_bounds
    resolution = 100.0
    minx -= 1000
    miny -= 1000
    maxx += 1000
    maxy += 1000
    width = int((maxx - minx) / resolution)
    height = int((maxy - miny) / resolution)
    data = ones((height, width), dtype=float32)
    path = tmp_path / "fake_ghsl.tif"
    with rasopen(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        crs=boundary.crs.to_wkt(),
        transform=from_origin(minx, maxy, resolution, resolution),
    ) as raster:
        raster.write(data, 1)
    return str(path)


def test_add_edge_population(test_city_small_copy, fake_ghsl_raster, monkeypatch):
    """Test the `add_edge_population` function by design."""
    monkeypatch.setattr(approximation, "get_ghsl", lambda bbox: fake_ghsl_raster)
    _, graph = test_city_small_copy
    add_edge_population(graph, overwrite=True)
    # Check all edges have the `population` and `area` attributes
    for _, _, data in graph.edges(data=True):
        assert isinstance(data["population"], float32)
        assert isinstance(data["area"], float32)
        assert isinstance(data["cell_id"], int)


def test_add_edge_population_written(test_city_small_copy):
    """Test the `add_edge_population` function for already written population."""
    _, graph = test_city_small_copy
    with pytest.raises(ValueError):
        add_edge_population(graph, overwrite=False)


@pytest.mark.parametrize("subgraph_node", [0, 100, 200])
@pytest.mark.parametrize("subgraph_radius", [0, 1, 2, 10])
def test_get_population_area(test_city_small_copy, subgraph_node, subgraph_radius):
    """Test the `subgraph_population` function by design."""
    _, graph = test_city_small_copy
    subgraph = ego_graph(
        graph, list(graph.nodes)[subgraph_node], radius=subgraph_radius
    )
    population, area = get_population_area(subgraph)
    assert isinstance(population, float)
    assert isinstance(area, float)
    if subgraph_radius == 0:
        assert population == 0
        assert area == 0
    else:
        assert population > 0
        assert area > 0


def test_get_population_area_no_edge_population(test_city_small_copy):
    """Test the `subgraph_population` function for missing edge population."""
    _, graph = test_city_small_copy
    del graph.graph["edge_population"]
    with pytest.raises(ValueError):
        get_population_area(graph)


@pytest.mark.parametrize("batch_size", [-1, 0, None, "1", (1, 2), [1], {1, 2}])
def test_get_edge_population_faulty_batch_size(test_city_small_copy, batch_size):
    """Test the `get_edge_population` function for faulty batch sizes."""
    _, graph = test_city_small_copy
    with pytest.raises(ValueError):
        get_edge_population(graph, batch_size=batch_size)
