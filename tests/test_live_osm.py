"""Optional live compatibility test against OSM services."""

from time import sleep

import pytest
from shapely import MultiPolygon, Polygon

from superblockify.config import Config
from superblockify.utils import load_graph_from_place

pytestmark = pytest.mark.live


def test_load_graph_from_place_live(tmp_path):
    """Check that the live OSM download and preprocessing path still works.

    This test is excluded from normal CI runs. It uses one small place and only
    asserts stable structural properties so that normal OSM data edits do not
    make it fail.
    """
    delays = [10, 30, 60]
    graph = None
    for attempt, delay in enumerate(delays, start=1):
        try:
            graph = load_graph_from_place(
                save_as=str(tmp_path / "Adliswil.graphml"),
                search_string="Adliswil, Bezirk Horgen, Zürich, Switzerland",
                add_population=False,
                max_nodes=100,
                network_type="drive",
                custom_filter=Config.NETWORK_FILTER,
                simplify=True,
            )
            break
        except Exception as err:  # pylint: disable=broad-except
            if attempt == len(delays):
                raise err
            sleep(delay)

    assert graph is not None
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0
    assert isinstance(graph.graph["boundary"], (MultiPolygon, Polygon))
    for _, _, data in graph.edges(data=True):
        assert "length" in data
        assert "speed_kph" in data
        assert "travel_time" in data
