import pandas as pd

# Wczytanie danych z pliku CSV
try:
    df = pd.read_csv('network_connections.csv', sep=";")
    df_2 = pd.read_csv("power_balance_report.csv")
except FileNotFoundError as e:
    print(f"Nie znaleziono pliku: {e}")
    exit()

# Łączenie danych
df = pd.concat([df, df_2], axis=1, ignore_index=False)

# Sprawdzenie struktury danych
print("Kolumny w danych:", df.columns)

# Dodanie kolumny 'Protection' jeśli jej brakuje
if 'Protection' not in df.columns:
    print("Dodajemy brakującą kolumnę 'Protection' z domyślną wartością 'Brak ochrony'.")
    df['Protection'] = 'Brak ochrony'

# Filtracja danych od połączenia o indeksie 0 do ostatnich 12 połączeń
df_filtered = df.iloc[:-12]  # Otrzymujemy wszystkie wiersze z wyjątkiem ostatnich 12 (pomijamy kable oceaniczne)
print("Przefiltrowane dane:", df_filtered)

# Definicje kosztów (w AUD)
costs = {
    'Gigabit switch': 500,
    '10 Gbps switch': 1500,
    'Medium-grade router': 2000,
    'Carrier-grade router': 5000,
    'WDM with optical regenerators': 20000,
    'Cat 6A cable': 2,
    'Multimode fiber': 5,
    'Single-mode fiber': 10,
    'Optical regenerator': 10000,
    'Installation switch/router': 200,
    'Installation Cat 6A cable per meter': 5,
    'Installation Multimode fiber per meter': 10,
    'Installation Single-mode fiber per meter': 10,
    'Installation regenerator': 1000,
    'Annual maintenance rate': 0.10,
    'Electricity cost per kWh': 0.25,
    'Administrative fees per year': 1000000,
    'Power reserve factor': 1.20
}

# Funkcja klasyfikująca połączenia z uwzględnieniem ochrony ścieżki
def classify_connection(length_km, bandwidth_mbps, protection_type):
    if length_km < 10:
        if bandwidth_mbps < 1000:
            return 'Gigabit switch', 'Cat 6A cable', protection_type
        else:
            return '10 Gbps switch', 'Multimode fiber', protection_type
    elif 10 <= length_km <= 100:
        if bandwidth_mbps < 10000:
            return 'Medium-grade router', 'Single-mode fiber', protection_type
        else:
            return 'Carrier-grade router', 'Single-mode fiber', protection_type
    else:
        return 'WDM with optical regenerators', 'Single-mode fiber', protection_type

# Inicjalizacja zmiennych do zliczania sprzętu i długości kabli
equipment_count = {key: 0 for key in costs if 'switch' in key or 'router' in key or 'regenerator' in key}
cable_length = {key: 0 for key in costs if 'cable' in key or 'fiber' in key}

# Przetwarzanie danych połączeń
for index, row in df_filtered.iterrows():
    try:
        length_km = row['d']
        bandwidth_mbps = row['prze']
        protection_type = row['Protection']  # Kolumna z typem ochrony
    except KeyError as e:
        print(f"Błąd dostępu do danych: {e}")
        continue

    equipment, cable, protection = classify_connection(length_km, bandwidth_mbps, protection_type)

    # Jeśli połączenie ma ochronę 1+1, podwajamy liczbę urządzeń i kabli
    if protection == '1+1 Path Protection':
        equipment_count[equipment] += 2
        cable_length[cable] += 2 * length_km
    else:  # Jeśli połączenie ma ochronę 1:1, dodajemy tylko zapasową ścieżkę
        equipment_count[equipment] += 1
        cable_length[cable] += length_km

    # Jeśli połączenie ma długą odległość, dodajemy regenerator optyczny
    if length_km > 100:
        regenerator_count = max(1, length_km // 100)
        equipment_count['Optical regenerator'] += regenerator_count

# Obliczenie kosztów początkowych
initial_costs = {}
for equipment, count in equipment_count.items():
    equipment_cost = count * costs[equipment]
    installation_cost = count * costs.get(f'Installation {equipment.split()[0].lower()}', 0)
    initial_costs[equipment] = equipment_cost + installation_cost

for cable, length in cable_length.items():
    # Warunki na sztywno przypisujące klucze instalacji
    if str(cable) == 'Cat 6A cable':
        installation_key = 'Installation Cat 6A cable per meter'
    elif str(cable) == 'Multimode fiber':
        installation_key = 'Installation Multimode fiber per meter'
    elif str(cable) == 'Single-mode fiber':
        installation_key = 'Installation Single-mode fiber per meter'

    # Koszt kabla
    cable_cost = length * costs[cable] * 1000
    initial_costs[cable] = cable_cost + costs[installation_key] * length * 1000

# Tworzenie dodatkowej tabeli z licznością sprzętu i długościami kabli
summary_data = [
    {'Item': item, 'Count or Length (km)': count_or_length}
    for item, count_or_length in {**equipment_count, **cable_length}.items()
]

# Całkowity koszt początkowy
total_initial_cost = sum(initial_costs.values())

# Obliczenie rocznych kosztów utrzymania
annual_maintenance_cost = sum([
    count * costs[equipment] * costs['Annual maintenance rate']
    for equipment, count in equipment_count.items()
])

# Obliczenie kosztów energii
total_power_consumption = sum([
    count * costs[equipment] * costs['Electricity cost per kWh'] * costs['Power reserve factor']
    for equipment, count in equipment_count.items()
])

# Roczne koszty energii
annual_energy_cost = total_power_consumption * 8760  # liczba godzin w roku

# Całkowite koszty utrzymania
total_annual_maintenance_cost = annual_maintenance_cost + annual_energy_cost + costs['Administrative fees per year']

# Tworzenie raportów w Excelu
with pd.ExcelWriter('network_cost_report.xlsx') as writer:
    pd.DataFrame(initial_costs.items(), columns=['Element', 'Cost (AUD)']).to_excel(writer, sheet_name='Initial Costs', index=False)
    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary Data', index=False)
    pd.DataFrame([
        {'Category': 'Annual Maintenance', 'Cost (AUD)': annual_maintenance_cost},
        {'Category': 'Annual Energy', 'Cost (AUD)': annual_energy_cost},
        {'Category': 'Administrative Fees', 'Cost (AUD)': costs['Administrative fees per year']}
    ]).to_excel(writer, sheet_name='Annual Maintenance Costs', index=False)

print(f"Total Initial Cost: {total_initial_cost:.2f} AUD")
print(f"Total Annual Maintenance Cost: {total_annual_maintenance_cost:.2f} AUD")
