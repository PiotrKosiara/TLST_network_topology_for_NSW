import csv
from math import radians, sin, cos, sqrt, asin


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Promień Ziemi w kilometrach

    # Konwersja stopni na radiany
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Różnice współrzędnych
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Średnia szerokość geograficzna
    phi_m = (lat1 + lat2) / 2

    # Obliczenie zgodne z podanym wzorem
    a = (1 - cos(dlat)) / 2 + cos(lat1) * cos(lat2) * (1 - cos(dlon)) / 2
    c = asin(sqrt(a))
    wyn = 2 * R * c

    return wyn

input_file = "NSW_coordinates.csv"
output_file = "distances.csv"

data = []

with open(input_file, "r") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        data.append({
            "name": row["Local Government areas"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"])
        })

with open(output_file, "w", newline="") as csvfile:
    fieldnames = ["Place 1", "Place 2", "Distance (km)"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    for i, place1 in enumerate(data):
        for j, place2 in enumerate(data):
            if i < j:  # Aby uniknąć powielania par
                distance = haversine(
                    place1["latitude"], place1["longitude"],
                    place2["latitude"], place2["longitude"]
                )
                writer.writerow({
                    "Place 1": place1["name"],
                    "Place 2": place2["name"],
                    "Distance (km)": round(distance, 2)
                })

print(f"Plik z odległościami został zapisany jako '{output_file}'")
