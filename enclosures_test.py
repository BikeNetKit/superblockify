from networkx import Graph, is_isomorphic, set_node_attributes, set_edge_attributes, MultiDiGraph
import osmnx as ox
import networkx as nx
import superblockify as sb
from superblockify.graph_stats import basic_graph_stats
from superblockify.population.approximation import add_edge_population
from superblockify.population.tessellation import  add_edge_cells
import momepy as mp
import pandas as pd
import geopandas as gpd
import os
from libpysal import graph
import numpy as np

def preprocess_graph(G: MultiDiGraph, boundary_buffer_dist: float = 200) -> MultiDiGraph:

    # Add edge bearings    
    G = ox.add_edge_bearings(G)    

    # Checks if the graph is projected, if not it projects it to the local UTM.
    if not ox.projection.is_projected(G.graph["crs"]):
        G = ox.project_graph(G)
    
    # A geodataframe is created from the projected graph for extracting the
    # boundary of the graph. And, if missing, extract the lenghts of the geometies 
    edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)
    names_attribute = edges_gdf.columns

    # Checks if the lenght is missing, e.g. the graph was not created with osmnx, and adds it if necessary
    if "length" not in names_attribute:
        logger.warning(
            "Length attribute is not present in the graph. Calculating lengths from geometry."
        )
        edges_lengths = edges_gdf.geometry.length
        set_edge_attributes(G, edges_lengths.to_dict(), name="length")

    # Checks if the maxspeed attribute is missing, e.g. this is not a graph from OSM data.
    # Adds a default maxspeed of 30 km/h if it is missing, as this is needed for calculating
    # travel times. 
    if "maxspeed" not in names_attribute:
        logger.warning(
            "maxspeed attribute is not present in the graph. Global max speeds are going to be set to 30 km/h."
        )
        set_edge_attributes(G, 30, name="maxspeed")

    # Add speeds and travel times using  osmnx 
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    

    # Create a convex hull of the graph to calculate the area and set the boundary for saving the graph.
    # This is implemented with an if statement to support older versions of geopandas < 1.0.0 
    if hasattr(edges_gdf.geometry, "union_all"):
        edge_union = edges_gdf.geometry.union_all()
    else:
        edge_union = edges_gdf.geometry.unary_union

    # A convex hull is created arround the bufferred edges.
    enclosing_hull = edge_union.buffer(boundary_buffer_dist).convex_hull
    
    # Assigning the attributes to the graph
    G.graph.update(basic_graph_stats(G, area=enclosing_hull.area))
    G.graph["area"] = enclosing_hull.area
    G.graph['boundary'] = enclosing_hull

    # Adding the edge population data
    add_edge_population(G)
    add_edge_cells(G)

    return G

if not os.path.exists("data/bogota_test.graphml"):
    # Manual download of a road network graph
    point_city = (4.691389013888271, -74.06823532051276)
    distance = 4000
    G_raw = ox.graph_from_point(center_point=point_city, dist=distance, network_type='drive')
    ox.save_graphml(G_raw, "data/bogota_test.graphml")
else:
    G_raw = ox.load_graphml("bogota_test.graphml")    

G_processed = preprocess_graph(G_raw)

# Running the partitioner on the graph 
part = sb.ResidentialPartitioner(
    name="Bogota_residential_test",
    city_name="Bogota_test",
    unit="time",
    graph=G_processed
)

part.run(
    calculate_metrics=True,
    make_plots=True,
    replace_max_speeds=False
)

sparse_graph = part.sparsified

boundary = part.graph.graph['boundary']

sparse_gdf = ox.graph_to_gdfs(sparse_graph.to_undirected(), nodes=False, edges=True)

# sparse_gdf.explore()

enclosures = mp.enclosures(sparse_gdf, boundary)


enclosures["area"] = enclosures.geometry.area*1e-6  
enclosures["perimeter"] = enclosures.geometry.length*1e-3 

enclosures.explore(column="area", legend=True)
enclosures.explore(column="perimeter", legend=True)

nodes, edges = ox.graph_to_gdfs(part.graph, nodes=True, fill_edge_geometry=True)

diss_edges = edges[edges["component_name"].isna() == False].dissolve(by="component_name")

dissolved_edges = gpd.GeoDataFrame(geometry=diss_edges.centroid)

# rep_nodes = nodes[nodes["representative_node_name"].isna() == False].set_index("representative_node_name")
# rep_nodes = rep_nodes[["geometry"]]

ltn_data = pd.DataFrame(part.get_ltns()).set_index("name")

ltn_centroids = dissolved_edges.join(ltn_data)

joined_ltn_nodes = ltn_centroids.sjoin(enclosures[["eID","geometry"]],how="left", predicate="within")

enclosure_summary = joined_ltn_nodes.reset_index().groupby("eID").agg(
    ltn_count = ("component_name", "count"),
    ltn_pop = ("population", "sum"),
    ltn_length = ("length_total", "sum")
)

enclosures_expanded = enclosures.join(enclosure_summary)
enclosures_expanded = enclosures_expanded[enclosures_expanded.area < max(enclosures_expanded.area)]

# Flagging enclosures with more than 1 LTN
enclosures_expanded["ltn"] = enclosures_expanded["ltn_count"] > 0
enclosures_expanded["pop_dens_ha"] = enclosures_expanded["ltn_pop"] / (enclosures_expanded["area"] / 10000)

# Get the filtered enclosures (those with LTN)
filtered_enclosures = enclosures_expanded[enclosures_expanded["ltn"]]



m = enclosures_expanded.explore(column="ltn_count", legend=True,cmap = "Reds")
ltn_centroids.explore(m =m, legend=True)
sparse_gdf.explore(m =m, legend=True, col = "black")



m = enclosures_expanded.explore(column="pop_dens_ha", legend=True,cmap = "coolwarm")
ltn_centroids.explore(m =m, legend=True)

m = enclosures_expanded.explore(column="perimeter", legend=True,cmap = "turbo")
ltn_centroids.explore(m =m, legend=True)


m = enclosures_expanded.explore(column="ltn_length", legend=True,cmap = "turbo")
ltn_centroids.explore(m =m, legend=True)

# sb.save_to_gpkg(part,"bogota_test_residential.gpkg")


rook = graph.Graph.build_contiguity(enclosures_expanded[enclosures_expanded["ltn"]])

m = enclosures_expanded.explore(column="ltn")
rook.explore(
    enclosures_expanded, m=m, edge_kws=dict(style_kwds=dict(weight=1)), nodes=False
)

# Converting to networkx Graph
G_nx = rook.to_networkx()

# Get connected components
components = list(nx.connected_components(G_nx))

# Create a mapping of enclosure ID to component
id_to_component = {}
for comp_id, component in enumerate(components):
    for node_id in component:
        id_to_component[node_id] = comp_id


# Add component information based on the index/eID
filtered_enclosures["component"] = filtered_enclosures.index.map(id_to_component)

# Group by component and aggregate
component_stats = filtered_enclosures.groupby("component").agg(
    total_area=("area", "sum"),
    mean_area=("area", "mean"),
    sd_area=("area", "std"),
    total_population=("ltn_pop", "sum"),
    mean_population=("ltn_pop", "mean"),
    sd_population=("ltn_pop", "std"),
    component_size=("component", "count")
).reset_index()

print(component_stats.to_string())

# Create a scatter plot of total area vs total population, size by component size
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
x = np.linspace(0, component_stats["total_area"].max(), 100)
y = 26.141 * x
plt.plot(x, y, color="red", linestyle="--", label="Mean density = 26.141")
scatter = plt.scatter(
    component_stats["total_area"],
    component_stats["total_population"]/1000,  # Scale population for better visualization
    s=component_stats["component_size"] * 20,  # Scale size by component size
    # Color by population density (population per area)
    c=component_stats["total_population"] / component_stats["total_area"],
    cmap="viridis",
    alpha=0.6,
    edgecolors="w",
    linewidth=0.5
)
# Add a line with a slope of 26.141 
plt.xlabel("Total Area (sq km)")
plt.ylabel("Total Population (thousands)")
plt.title("Component Total Area vs Total Population")
plt.grid(True)
plt.show()

plt.hist(component_stats["total_area"], bins=20, alpha=0.5, label="Total Area")
plt.hist(component_stats["total_population"], bins=20, alpha=0.5, label="Total Population")
plt.xlabel("Population and Area")
plt.ylabel("Frequency")
plt.title("Distribution of Component Statistics")
plt.legend()
plt.show()
