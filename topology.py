import networkx as nx
import requests
import random

# Stałe i parametry
BANDWIDTH_PER_PERSON_MBPS = 0.2
TOTAL_POPULATION = 8153000  # Całkowita populacja NSW
TARGET_BANDWIDTH_TBPS = (TOTAL_POPULATION * BANDWIDTH_PER_PERSON_MBPS) / 1000  # Przepustowość w Tbps

# Symulowane dane populacji dla głównych miast
CITY_POPULATION = {
    'Sydney': 5000000,
    'Newcastle': 322000,
    'Wollongong': 305000,
    'Central Coast': 333000,
    'Dubbo': 55000,
    'Tamworth': 42000,
    'Coffs Harbour': 75000,
}

# Węzły dostępu międzynarodowego i międzystanowego
ACCESS_POINTS = [
    ('Sydney', 'International Cable 1'),
    ('Sydney', 'International Cable 2'),
    ('Newcastle', 'Queensland Link'),
    ('Wollongong', 'Victoria Link')
]

# Funkcja symulująca pobieranie danych populacji (można zastąpić API)
def get_population_data():
    return CITY_POPULATION

# Funkcja tworząca graf topologii sieciowej
def create_network_topology():
    G = nx.Graph()
    population_data = get_population_data()

    # Dodawanie węzłów do grafu
    for city, population in population_data.items():
        bandwidth = population * BANDWIDTH_PER_PERSON_MBPS
        G.add_node(city, population=population, bandwidth=bandwidth)

    # Dodawanie połączeń (krawędzi) między miastami
    for city1 in CITY_POPULATION:
        for city2 in CITY_POPULATION:
            if city1 != city2:
                distance = random.randint(50, 300)  # Symulacja odległości
                latency = distance / 200  # Przykładowa latencja w ms
                capacity = (CITY_POPULATION[city1] + CITY_POPULATION[city2]) * BANDWIDTH_PER_PERSON_MBPS / 2
                G.add_edge(city1, city2, latency=latency, capacity=capacity)

    # Dodawanie połączeń do punktów dostępu
    for city, access_point in ACCESS_POINTS:
        G.add_edge(city, access_point, capacity=5000, latency=1)  # Duża przepustowość dla kabli międzynarodowych

    return G

# Wizualizacja topologii (opcjonalnie)
def visualize_topology(G):
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=700, node_color='skyblue')
    labels = nx.get_edge_attributes(G, 'capacity')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.show()

if __name__ == '__main__':
    topology = create_network_topology()
    print("Topologia sieci została wygenerowana.")
    visualize_topology(topology)
