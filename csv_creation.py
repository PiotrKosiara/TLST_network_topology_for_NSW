import openrouteservice
from geopy.distance import geodesic
import pandas as pd
import csv


def oblicz_dystans_prosty(miejsce_start, miejsce_cel):
    api_key = "5b3ce3597851110001cf6248338c53520f3a4157b41caa92deead9b6"
    client = openrouteservice.Client(key=api_key)

    start_coords = client.pelias_search(miejsce_start)['features'][0]['geometry']['coordinates']
    cel_coords = client.pelias_search(miejsce_cel)['features'][0]['geometry']['coordinates']

    start_coords = (start_coords[1], start_coords[0])
    cel_coords = (cel_coords[1], cel_coords[0])

    dystans = geodesic(start_coords, cel_coords).kilometers

    return dystans


def znajdz_wspolrzedne(miejsce):
    api_key = "5b3ce3597851110001cf6248338c53520f3a4157b41caa92deead9b6"
    client = openrouteservice.Client(key=api_key)

    wynik = client.pelias_search(str(miejsce)+" Australia")['features'][0]['geometry']['coordinates']
    wspolrzedne = {
        'latitude': wynik[1],
        'longitude': wynik[0]
    }

    return wspolrzedne


# Przetwarzanie pliku CSV
csv_file = 'NSW_population.csv'
data = pd.read_csv(csv_file, delimiter=';', encoding='mac_roman')

# Tworzenie listy współrzędnych
wspolrzedne_list = []
for miejsce in data['Local Government areas']:
    wspolrzedne = znajdz_wspolrzedne(miejsce)
    wspolrzedne_list.append({
        'Local Government areas': miejsce,
        'latitude': wspolrzedne['latitude'],
        'longitude': wspolrzedne['longitude']
    })

# Zapis do pliku CSV wspolrzednych
wspolrzedne_df = pd.DataFrame(wspolrzedne_list)
wspolrzedne_df.to_csv('NSW_coordinates.csv', index=False, sep=';')

