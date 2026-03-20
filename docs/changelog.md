# Changelog

## [1.0.2](https://github.com/BikeNetKit/superblockify/compare/1.0.1...v1.0.2) (2026-03-20)


### Bug Fixes

* `osmnx` API change & `union_all()` ([a46fefa](https://github.com/BikeNetKit/superblockify/commit/a46fefadca1f0f19634f3d2d22ba65f30f2f25e5))
* added missing cache id & Update checkout and cache version ([df33318](https://github.com/BikeNetKit/superblockify/commit/df33318535fc9a1106e8bba622230321e65e28b3))
* bump version to 1.0.1 ([4cdc244](https://github.com/BikeNetKit/superblockify/commit/4cdc244c3fce4446149dd949e901e39adcb02fd2))
* cell dissolve column ([3c0a18d](https://github.com/BikeNetKit/superblockify/commit/3c0a18d011d0c5e06cbfd76ea0e5363416f593ea))
* Coverage pipeline & Pylint imports ([0ea2ef2](https://github.com/BikeNetKit/superblockify/commit/0ea2ef2aa90db123d1805b26a588a3cc09e398f9))
* distance calculation order ([7382ce4](https://github.com/BikeNetKit/superblockify/commit/7382ce438223ab3694a142a5d7d1da040f041790))
* Full raster path ([c2892df](https://github.com/BikeNetKit/superblockify/commit/c2892df540c596e6c858bb51a3cf7d8d336e5cbe))
* graph dtype for `population` ([28dd7ce](https://github.com/BikeNetKit/superblockify/commit/28dd7ce6dda462cab74ae81ba2e18580486851a7))
* Graph Import Projection Order ([56aefb7](https://github.com/BikeNetKit/superblockify/commit/56aefb7cdb07f8c2009df4960095cb69d66ed9d3))
* hash environment file - load cache ([985d330](https://github.com/BikeNetKit/superblockify/commit/985d330d9beb684db08f7096dbdf5297d4f96fe0))
* Metric load path ([1143822](https://github.com/BikeNetKit/superblockify/commit/11438229bc70bb1305314b3978ea5650d3265a77))
* missing attribute ([9ce55c8](https://github.com/BikeNetKit/superblockify/commit/9ce55c81c939dc69c7de1c4a7a5244ae4cacc1ff))
* move test fixture `_delete_ghsl_tifs` ([537897a](https://github.com/BikeNetKit/superblockify/commit/537897ab448f7e6916a5cfb9ec67942e464f80d2))
* remove unused Haversine distance function ([29b470d](https://github.com/BikeNetKit/superblockify/commit/29b470dac3646d382e7d6b17af7b851090bda904))
* Set date to today ([fa3c695](https://github.com/BikeNetKit/superblockify/commit/fa3c6956a83b9167dccc2f724998caeb31ae1199))
* Split edge length when splitting isolated edges ([75f13fc](https://github.com/BikeNetKit/superblockify/commit/75f13fc19232f387f9259e7b1a2ebe2acc1b3016))
* tests for newly supported degree splitting ([23d69f8](https://github.com/BikeNetKit/superblockify/commit/23d69f872cdd130b50eadee480719e040ddcb8e8))
* TypeError in utils ([fc622f3](https://github.com/BikeNetKit/superblockify/commit/fc622f354f34da287ffef32c1939351d6f229e0b))
* use inbuilt `sum` due to `numpy` incomp. ([982e4d9](https://github.com/BikeNetKit/superblockify/commit/982e4d988a03ee0e1f8beb67674337d3fd346a20))
* Use partitioner copy fixture ([d38ac6e](https://github.com/BikeNetKit/superblockify/commit/d38ac6e3742d3198dba8171402f24f411df50bab))


### Dependencies

* Add separate dev `environment-dev.yml` ([a190a54](https://github.com/BikeNetKit/superblockify/commit/a190a54a40a67b3d8ec2415efe330349d29bbe18))


### Documentation

* Add Master Thesis link and references ([733b644](https://github.com/BikeNetKit/superblockify/commit/733b64448f4bdb22075f8e6d747bc08a3c2855b7))

## Changelog

## Version 1.0.1 (2024-12-04)

* 🧹 Lint: Reconfigured linting settings.
* 🐛 Fixes: Removed unused Haversine distance function and adapted to `osmnx` API changes.
* 🛠️ Update: Updated `test.yml` for artifacts v4.4.0 breaking change.
* 📝 Documentation: Various updates including changelog, badge links,
  mobile optimization, GitHub handles, installation instructions, `CITATION.cff`, and `paper.md`.

## Version 1.0.0 (2024-08-12)

* ✨ First major release ✨
* 📦 Prepared for osmnx 2.0.0 and shipped `cities.yml` in pypi package.
* ⚙️ Added function to set log level and added python versions 3.11 and 3.12.
* 🔄 Merged several pull requests improving settings, README, dependencies, and project structure.
* 🐛 Fixed coverage for special case, tests, and code style issues.
* 📝 Updated README with CI/CD badges, improved documentation, and unified capitalization.
* 🗒️ Updated Changelog, Version, and Website Copyright.
* 📝 Licensed work under GNU AGPLv3.
* 📊 IO operations enhanced with graph reduction.
* 🗒️ Logging improvements: silenced numba compilation, reprojected debug messages.
* ⚙️ Parallelization updates: removed `num_workers` and `chunk_size`.
* 🧪 Testing updates: increased util coverage, added response 502 as `xfail`.
* 🆕 New features: Betweenness Centrality Cutoff, Reduced path filling.
* 🐛 Fixes: notebook formatting, GEOSException in tesselation, missing attribute.
* 🔄 Merged pull request: `🌐 Added Betweenness Centrality Cutoff
  <https://github.com/BikeNetKit/superblockify/pull/82>`_.
* 📝 Misc changes: deactivated colormap logging,
  unified nodes and edges into one variable.
* 📊 Improved analysis scripts

Version 0.2.2 (2023-06-27)
**************************

* 📊 Unified Plot image format/suffix in config
* 🔢 Key Figures: lightweight results for analysis, see
  :func:`superblockify.partitioning.utils.get_key_figures`.
* 💾 Lightweigth metric saving
* 🆔 Added ISO 3166 country codes
* 🏙️ City Crawling: Get cities from Springer Website Table. Useful functions to add
  OSM relation IDs to the cities. Moved cities to `cities.yml` file.
* 🌆 City List format specification.
* 🗒️ Adjust logging for better usefullness. Add and remove some log messages.
* 📚️ Added `mamba` to the installation instructions and changed standard environment
  name.
* ⬆️ Demand Change: Added Superblock aggregate statistics for the betweennesses.

## Version 0.2.1 (2023-06-22)

* ✨ Second release ✨
* ⬆️ Integrated final graph statistics and Superblock statistics.
* 🏡 Moved Coverage to Codecov |codecov-badge|.
* ⬆️ Display basic graph stats at Partitioner initialization.
  Abstract base class :class:`superblockify.partitioning.base.BasePartitioner`.
* ⬆️ Geopackage export: Resolve Superblock cell option. If set to True, the Superblock cells are
  resolved to polygons. Normally, only the edges are exported.
  Added general graph stats with OSM boundary polygon.

.. |codecov-badge| image:: https://codecov.io/gh/BikeNetKit/superblockify/branch/main/graph/badge.svg?token=AS72IFT2Q4
   :target: https://codecov.io/gh/BikeNetKit/superblockify
   :height: 2ex

## Version 0.2.0 (2023-06-20)

* 🔧 Sped up population distribution in
  :func:`superblockify.population.approximation.get_edge_population`.
* ⬆️ Add population and density to Superblocks
* 🐛 Fix: Graph import projection order. Un-skewed distance attribute.

## Version 0.1.3 (2023-06-19)

* 📚️ Documented approaches in reference notebooks :ref:`Population Data`,
  :ref:`Street Tessellation`, and :ref:`Street Population Density`.
* ⬆️ Added population preprocessing for for every tesselated edge. This enables an
  efficient population density aggregation for any given superblock.
  See modules in :mod:`superblockify.population`.
* ⬆️ Automated population data download and preprocessing of the GHS-POP - R2023A dataset
  <https://ghsl.jrc.ec.europa.eu/ghs_pop2023.php>.
* ⬆️ Added graph attribute `boundary`, used for calculating the total area of the city.
* ⬆️ Added general graph statistics :mod:`superblockify.metric.graph_stats`.
  Including spatial clustering and anisotropy.

## Version 0.1.2 (2023-05-18)

* ⬆️ Added Partitioner based on Betweenness Centrality.
* 🐛 Fix segfault in betweenness centrality calculation caused by testcase with one node
  graph.

## Version 0.1.1 (2023-05-15)

* ⬆️ Added Betweenness Centrality Calculation in measures, precompiled version works
  quick on metropolitan sized city networks.
* ⬆️ Added speed limit: Routing and low traffic speed overwriting. Unit can be passed
  when initializing a partitioner.

## Version 0.1.0 (2023-04-11)

* ✨ Initial release ✨
* 🔧 Full rework of the restricted distance calculation. Runs quicker and is more
  memory efficient. Also, path finding had a bug in the previous version.


## Version 0.0.0

* See changes before in the repository under the tag `0.0.0
  <https://github.com/BikeNetKit/superblockify/tags>`_.
