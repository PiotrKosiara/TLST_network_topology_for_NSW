import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import contextily as ctx

BANDWIDTH_PER_PERSON_MBPS = 0.2*5
DISTANCE_THRESHOLD = 35  # Próg dystansu w km
MAX_CONNECTIONS = 10  # Maksymalna liczba połączeń na węzeł

# Wczytywanie danych (z separatorem ;)
population_df = pd.read_csv('NSW_population.csv', sep=';')
coordinates_df = pd.read_csv('NSW_coordinates.csv', sep=';')
distances_df = pd.read_csv('distances.csv', sep=';')
access_points_df = pd.read_csv('access_points.csv', sep=';')


# Tworzenie grafu
def create_network_topology():
    G = nx.Graph()
    connections_list = []

    # Dodawanie węzłów (Local Government Areas - LGA)
    for index, row in population_df.iterrows():
        lga = row['Local Government areas']
        population = row['Population']
        bandwidth = population * BANDWIDTH_PER_PERSON_MBPS * 1000

        coord = coordinates_df[coordinates_df['Local Government areas'] == lga]
        if not coord.empty:
            lat, lon = coord.iloc[0]['latitude'], coord.iloc[0]['longitude']
            G.add_node(lga, population=population, bandwidth=bandwidth, pos=(lon, lat))

    # Dodawanie krawędzi na podstawie dystansów (z progiem dystansu)
    for index, row in distances_df.iterrows():
        place1 = row['Place 1']
        place2 = row['Place 2']
        distance = row['Distance (km)']

        if 'Lord Howe Island' in [place1, place2]:
            continue  # Pomijamy połączenia z Lord Howe Island

        if place1 in G.nodes and place2 in G.nodes and distance <= DISTANCE_THRESHOLD:
            capacity = (G.nodes[place1]['bandwidth'] + G.nodes[place2]['bandwidth']) / 2
            latency = distance / 200  # Przykładowa latencja
            G.add_edge(place1, place2, latency=latency, capacity=capacity)
            connections_list.append([place1, place2, distance, capacity])

    # Dodawanie połączeń minimalnych (każdy punkt do 2 najbliższych)
    for node in G.nodes:
        if node == 'Lord Howe Island':
            continue  # Lord Howe Island nie powinno mieć połączeń

        neighbors = distances_df[(distances_df['Place 1'] == node) | (distances_df['Place 2'] == node)] \
            .sort_values(by='Distance (km)')
        connections = 0
        for _, row in neighbors.iterrows():
            if connections >= 2:
                break
            place1, place2 = row['Place 1'], row['Place 2']
            distance = row['Distance (km)']

            if place1 in G.nodes and place2 in G.nodes and not G.has_edge(place1, place2):
                capacity = (G.nodes[place1]['bandwidth'] + G.nodes[place2]['bandwidth']) / 2
                latency = distance / 200
                G.add_edge(place1, place2, latency=latency, capacity=capacity)
                connections_list.append([place1, place2, distance, capacity])
                connections += 1

    # Ograniczenie do maksymalnie 10 połączeń na węzeł
    for node in G.nodes:
        edges = [(node, neighbor, G[node][neighbor]['latency']) for neighbor in G.neighbors(node)]
        if len(edges) > MAX_CONNECTIONS:
            edges = sorted(edges, key=lambda x: x[2])  # Sortuj po latencji (dystansie)
            for _, neighbor, _ in edges[MAX_CONNECTIONS:]:
                G.remove_edge(node, neighbor)
                connections_list = [c for c in connections_list if not (c[0] == node and c[1] == neighbor)]

    # Dodawanie access pointów
    for index, row in access_points_df.iterrows():
        access_point = row['access_point']
        location_lga = row['location_lga']
        capacity = row['capacity'] * 1000000  # Z Tbps na Mbps

        if location_lga in G.nodes:
            G.add_node(access_point, pos=(G.nodes[location_lga]['pos']))
            G.add_edge(location_lga, access_point, capacity=capacity, latency=1)
            connections_list.append([location_lga, access_point, 0, capacity])

    # Zapisanie połączeń do pliku CSV
    connections_df = pd.DataFrame(connections_list, columns=['miejsce_1', 'miejsce_2', 'długość połączenia', 'przepustowość'])
    connections_df.to_csv('network_connections.csv', index=False, sep=';')

    return G


# Wizualizacja topologii
def visualize_topology(G):
    pos = nx.get_node_attributes(G, 'pos')
    node_pos_list = [{'Location': node, 'geometry': Point(lon, lat)} for node, (lon, lat) in pos.items()]
    nodes_gdf = gpd.GeoDataFrame(node_pos_list, crs='EPSG:4326')
    nodes_gdf = nodes_gdf.to_crs(epsg=3857)
    node_pos_mercator = nodes_gdf.set_index('Location')['geometry'].apply(lambda p: (p.x, p.y)).to_dict()

    fig, ax = plt.subplots(figsize=(15, 12), dpi=150)
    nodes_gdf.plot(ax=ax, marker='o', color='skyblue', markersize=100)
    nx.draw_networkx_edges(G, node_pos_mercator, ax=ax, edge_color='gray', width=2)

    #edge_labels = nx.get_edge_attributes(G, 'capacity')
    #for (u, v), label in edge_labels.items():
        #x = (node_pos_mercator[u][0] + node_pos_mercator[v][0]) / 2
        #y = (node_pos_mercator[u][1] + node_pos_mercator[v][1]) / 2
        #plt.text(x, y, f"{label:.1f} Mbps", fontsize=9, ha='center', va='center',
                  #bbox=dict(facecolor='white', alpha=0.7))

    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
    plt.title('Topologia sieci stanu NSW')
    plt.axis('off')
    plt.show()


if __name__ == '__main__':
    topology = create_network_topology()
    print("Topologia sieci została wygenerowana.")
    visualize_topology(topology)
