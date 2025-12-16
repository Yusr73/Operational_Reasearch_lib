import math

def compute_intermediates(users, aps, settings):
    env = settings["EnvironmentType"]
    wifi_band = settings["WifiBand"]
    include_power = settings["IncludePowerConsumption"]

    # Alpha by environment
    alpha = 3 if env == "Indoor" else 3.5 if env == "Urban" else 2.7

    # D_max by band and environment (scaled to coordinate system)
    if wifi_band == "2.4 GHz":
        D_max = 5 if env == "Indoor" else 7 if env == "Urban" else 12
    else:  # 5 GHz
        D_max = 3 if env == "Indoor" else 5 if env == "Urban" else 10

    D_intf = 1.5 * D_max

    # Distances and feasible edges
    distances, E = {}, []
    for u in users:
        for a in aps:
            if None in (u["X"], u["Y"], a["X"], a["Y"]):
                continue
            d = math.sqrt((u["X"] - a["X"])**2 + (u["Y"] - a["Y"])**2)
            distances[(u["Name"], a["Name"])] = d
            if d <= D_max:
                E.append((u["Name"], a["Name"]))

    # Normalized energy costs with 0.7 scaling factor
    base_power = {
        "IoT Sensor": 1,
        "Wearable": 1,
        "Smartphone": 3,
        "Tablet": 4,
        "Laptop": 6
    }

    c = {}
    for (u_name, a_name) in E:
        device_type = next(u for u in users if u["Name"] == u_name)["Device"]
        factor = base_power.get(device_type, 1) if include_power else 0
        c[(u_name, a_name)] = 0.1 * factor * (distances[(u_name, a_name)] ** alpha) / (D_max ** alpha)

    # AP-AP distances
    ap_distances = {}
    for i, a1 in enumerate(aps):
        for j, a2 in enumerate(aps):
            if i < j and None not in (a1["X"], a1["Y"], a2["X"], a2["Y"]):
                d_ab = math.sqrt((a1["X"] - a2["X"])**2 + (a1["Y"] - a2["Y"])**2)
                ap_distances[(a1["Name"], a2["Name"])] = d_ab

    # Interference pairs
    I = []
    for (a1_name, a2_name), d_ab in ap_distances.items():
        a1 = next(a for a in aps if a["Name"] == a1_name)
        a2 = next(a for a in aps if a["Name"] == a2_name)
        if d_ab <= D_intf and a1["Channel"] == a2["Channel"]:
            I.append((a1_name, a2_name))

    # M values
    M = {}
    for (a1_name, a2_name) in I:
        a1 = next(a for a in aps if a["Name"] == a1_name)
        a2 = next(a for a in aps if a["Name"] == a2_name)
        k_a, k_b = a1["Capacity"], a2["Capacity"]
        d_ab = ap_distances[(a1_name, a2_name)]
        M_ab = math.floor(k_a + k_b - min(k_a,k_b) * max(0, 1 - d_ab/D_intf))
        M[(a1_name, a2_name)] = M_ab

    # User weights (priority)
    w = {}
    for u in users:
        if u["Priority"] == "High":
            w[u["Name"]] = 3
        elif u["Priority"] == "Medium":
            w[u["Name"]] = 2
        else:
            w[u["Name"]] = 1

    return {
        "D_max": D_max,
        "D_intf": D_intf,
        "distances": distances,
        "E": E,
        "c": c,
        "I": I,
        "M": M,
        "w": w
    }
