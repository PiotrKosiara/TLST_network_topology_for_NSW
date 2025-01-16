import pandas as pd


def classify_connection(length, bandwidth):
    if length < 10:
        if bandwidth < 1000:
            return "Gigabit switch, Cat 6A cables"
        else:
            return "10 Gbps switch, multimode fiber"
    elif 10 <= length <= 100:
        if bandwidth < 10000:
            return "Medium-grade router, single-mode fiber"
        else:
            return "Carrier-grade router, WDM"
    else:
        if bandwidth < 10000:
            return "Single-mode fiber with optical regenerators"
        else:
            return "WDM with optical regenerators"


def protection_mechanism(length):
    if length < 10:
        return "1+1 Path Protection"
    elif 10 <= length <= 100:
        return "1:1 Path Protection"
    else:
        return "APS with signal monitoring"


def power_balance_calculation(length, bandwidth, equipment, reserve=0.2):
    # Constants for power consumption
    power_per_mbps = {
        "Gigabit switch, Cat 6A cables": 0.5,
        "10 Gbps switch, multimode fiber": 0.3,
        "Medium-grade router, single-mode fiber": 0.3,
        "Carrier-grade router, WDM": 0.3,
        "Single-mode fiber with optical regenerators": 0.5,
        "WDM with optical regenerators": 0.3,
    }
    cable_loss = {
        "Cat 6A cables": 2,  # W per km
        "multimode fiber": 0.5,  # W per km
        "single-mode fiber": 0.5,  # W per km
    }

    # Determine the correct loss value based on equipment
    if "Cat 6A cables" in equipment:
        loss = cable_loss["Cat 6A cables"]
    elif "multimode fiber" in equipment:
        loss = cable_loss["multimode fiber"]
    else:
        loss = cable_loss["single-mode fiber"]

    # Base power calculation
    base_power = power_per_mbps[equipment] * bandwidth

    # Cable loss calculation
    total_cable_loss = loss * length

    # Regenerators power, add if length > 100 km
    regenerators_power = 0
    if length > 100:
        regenerators_power = (length // 100) * 10  # 10 W per 100 km segment

    # Total power consumption before reserve
    total_power = base_power + total_cable_loss + regenerators_power

    # Adding power reserve
    total_power_with_reserve = total_power * (1 + reserve)

    return total_power_with_reserve


def generate_report(file_path):
    # Load data from CSV
    df = pd.read_csv(file_path, sep=";")

    report = []
    total_power_balance = 0

    for index, row in df.iterrows():
        miejsce_1 = row['miejsce_1']
        miejsce_2 = row['miejsce_2']
        length = row['d']
        bandwidth = row['prze']

        # Classify the connection
        equipment = classify_connection(length, bandwidth)
        protection = protection_mechanism(length)

        # Power balance calculation with reserve
        power_consumption = power_balance_calculation(length, bandwidth, equipment)
        total_power_balance += power_consumption

        # Add to report
        report.append({
            'Connection': f'{miejsce_1} - {miejsce_2}',
            'Length (km)': length,
            'Bandwidth (Mbps)': bandwidth,
            'Equipment': equipment,
            'Protection': protection,
            'Power Consumption with Reserve (W)': f'{power_consumption:.2f}'
        })

    # Convert report to DataFrame for pretty printing
    report_df = pd.DataFrame(report)
    print(report_df)

    # Save report to CSV
    report_df.to_csv('power_balance_with_reserve_report.csv', index=False)
    print(f'Total Power Balance for the network with reserve: {total_power_balance:.2f} W')


# Path to the CSV file
file_path = 'network_connections.csv'
generate_report(file_path)
