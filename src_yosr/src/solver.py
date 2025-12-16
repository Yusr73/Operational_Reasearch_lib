# solver.py
from gurobipy import Model, GRB, quicksum

def solve_network(intermediates, aps_data, lambda_energy=1):
    """
    Solve the AP-user assignment using Gurobi with a combined weighted objective:
    user priorities and optional energy minimization (lambda_energy = 0 or 1).

    Returns:
        assignments: dict with AP names as keys and lists of assigned user names
        status: string describing solver result ("Optimal", "Infeasible", etc.)
    """

    # Unpack intermediates
    E = intermediates["E"]
    c = intermediates["c"]        # normalized energy costs
    w = intermediates["w"]        # integer user weights (priority)
    I = intermediates["I"]
    M = intermediates["M"]

    # Create model
    m = Model("AP_Assignment")
    m.setParam('OutputFlag', 0)
    m.setParam('Threads', 1)

    # Variables
    x = {(u, a): m.addVar(vtype=GRB.BINARY, name=f"x_{u}_{a}") for (u, a) in E}
    m.update()

    # Constraints
    # 1. Exclusivity: each user ≤ 1 AP
    for u in set(u for u,_ in E):
        m.addConstr(quicksum(x[(u,a)] for (uu,a) in E if uu == u) <= 1)

    # 2. AP capacity
    aps = {a["Name"]: a["Capacity"] for a in aps_data}
    for a in aps:
        m.addConstr(quicksum(x[(u,a)] for (u,aa) in E if aa == a) <= aps[a])

    # 3. Interference
    for a1, a2 in I:
        m.addConstr(
            quicksum(x[(u,a1)] for (u,aa) in E if aa==a1) +
            quicksum(x[(u,a2)] for (u,aa) in E if aa==a2)
            <= M[(a1,a2)]
        )

    # Objective: combined weight + energy
    m.setObjective(
        quicksum((w[u] - lambda_energy * c[(u,a)]) * x[(u,a)] for (u,a) in E),
        GRB.MAXIMIZE
    )

    # === Solve
    m.optimize()

    # Initialize assignments dictionary (same format for all cases)
    assignments = {a: [] for a in aps}

    # Extract solution if feasible
    if m.status == GRB.OPTIMAL:
        for (u,a) in E:
            if x[(u,a)].X > 0.5:
                assignments[a].append(u)
        status = "Optimal"

    elif m.status == GRB.INFEASIBLE:
        # Keep empty lists for all APs
        status = "Infeasible"

    else:
        # Keep empty lists but report solver status
        status = f"Solver status: {m.status}"

    return assignments, status
