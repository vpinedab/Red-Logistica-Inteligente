# app/routing.py

from app.logistics import (
    load_trucks,
    load_routes,
    get_nearest_warehouse_for_store,
    get_route_data
)


COST_PER_KM = 12


def assign_orders_to_warehouses(orders, routes_df=None):
    """
    Asigna cada pedido al almacén más cercano disponible en routes.csv.

    Formato esperado de cada pedido:
    {
        "date": "2026-01-01",
        "store_id": "UR-001",
        "zone": "Urban",
        "forecasted_demand": 1400.5,
        "requested_quantity": 1400.5,
        "event": "None",
        "overload_risk": 0.72
    }
    """
    if routes_df is None:
        routes_df = load_routes()

    assigned_orders = []
    unassigned_orders = []

    for order in orders:
        store_id = order["store_id"]

        warehouse_id, distance = get_nearest_warehouse_for_store(
            store_id,
            routes_df
        )

        if warehouse_id is None:
            unassigned_orders.append({
                "order": order,
                "reason": "No route available for store"
            })
            continue

        route_data = get_route_data(warehouse_id, store_id, routes_df)

        if route_data is None:
            unassigned_orders.append({
                "order": order,
                "reason": "Route data not found"
            })
            continue

        assigned_order = {
            "date": order.get("date"),
            "store_id": store_id,
            "zone": order.get("zone"),
            "forecasted_demand": order.get("forecasted_demand"),
            "requested_quantity": order["requested_quantity"],
            "warehouse_id": warehouse_id,
            "distance_km": distance,
            "event": order.get("event", "None"),
            "overload_risk": order.get("overload_risk", 0),
            "average_travel_time_hr": route_data.get("average_travel_time_hr", 0),
            "route_capacity": route_data.get("route_capacity", 0),
            "traffic_risk": route_data.get("traffic_risk", 0),
            "congestion_probability": route_data.get("congestion_probability", 0)
        }

        assigned_orders.append(assigned_order)

    return assigned_orders, unassigned_orders


def group_orders_by_warehouse(assigned_orders):
    """
    Agrupa pedidos por almacén.
    """
    grouped_orders = {}

    for order in assigned_orders:
        warehouse_id = order["warehouse_id"]

        if warehouse_id not in grouped_orders:
            grouped_orders[warehouse_id] = []

        grouped_orders[warehouse_id].append(order)

    return grouped_orders


def assign_orders_to_trucks(assigned_orders, trucks_df=None):
    """
    Asigna pedidos a camiones respetando:
    - almacén al que pertenece cada camión
    - capacidad máxima de carga del camión

    Estrategia greedy:
    - Ordena pedidos por requested_quantity descendente.
    - Intenta meter cada pedido en el primer camión disponible del mismo almacén.
    """
    if trucks_df is None:
        trucks_df = load_trucks()

    truck_loads = {}

    for _, truck in trucks_df.iterrows():
        truck_id = truck["truck_id"]

        truck_loads[truck_id] = {
            "warehouse_id": truck["warehouse_id"],
            "capacity": truck["max_load"],
            "remaining_capacity": truck["max_load"],
            "used_capacity": 0,
            "orders": [],
            "fuel_efficiency": truck["fuel_efficiency"],
            "average_speed": truck["average_speed"]
        }

    sorted_orders = sorted(
        assigned_orders,
        key=lambda order: order["requested_quantity"],
        reverse=True
    )

    unassigned_orders = []

    for order in sorted_orders:
        requested_quantity = order["requested_quantity"]
        warehouse_id = order["warehouse_id"]
        assigned = False

        for truck_id, truck_data in truck_loads.items():
            same_warehouse = truck_data["warehouse_id"] == warehouse_id
            enough_capacity = truck_data["remaining_capacity"] >= requested_quantity

            if same_warehouse and enough_capacity:
                truck_data["orders"].append(order)
                truck_data["remaining_capacity"] -= requested_quantity
                truck_data["used_capacity"] += requested_quantity
                assigned = True
                break

        if not assigned:
            unassigned_orders.append({
                "order": order,
                "reason": "No truck capacity available in assigned warehouse"
            })

    return truck_loads, unassigned_orders


def calculate_total_distance(truck_loads):
    """
    Calcula distancia total aproximada.

    Por ahora usamos ida y vuelta por pedido:
        distancia_total += distance_km * 2

    Esto mantiene la idea de camiones en ciclo:
    almacén → tienda → almacén.
    """
    total_distance = 0

    for truck_id, truck_data in truck_loads.items():
        for order in truck_data["orders"]:
            total_distance += order["distance_km"] * 2

    return round(total_distance, 2)


def calculate_transport_cost(truck_loads):
    """
    Calcula costo variable de transporte:
        costo = distancia_total * COST_PER_KM
    """
    total_distance = calculate_total_distance(truck_loads)
    variable_cost = total_distance * COST_PER_KM

    return {
        "total_distance": round(total_distance, 2),
        "variable_cost": round(variable_cost, 2),
        "total_cost": round(variable_cost, 2)
    }


def calculate_truck_utilization(truck_loads):
    """
    Calcula porcentaje de utilización por camión.
    """
    utilization = {}

    for truck_id, truck_data in truck_loads.items():
        capacity = truck_data["capacity"]
        used_capacity = truck_data["used_capacity"]

        if capacity == 0:
            utilization[truck_id] = 0
        else:
            utilization[truck_id] = round((used_capacity / capacity) * 100, 2)

    return utilization


def routing_summary(truck_loads, unassigned_orders):
    """
    Genera resumen general de la asignación logística.
    """
    cost_data = calculate_transport_cost(truck_loads)
    utilization = calculate_truck_utilization(truck_loads)

    completed_orders = 0
    total_requested_quantity = 0
    total_loaded_quantity = 0

    for truck_id, truck_data in truck_loads.items():
        completed_orders += len(truck_data["orders"])
        total_loaded_quantity += truck_data["used_capacity"]

        for order in truck_data["orders"]:
            total_requested_quantity += order["requested_quantity"]

    return {
        "completed_orders": completed_orders,
        "unassigned_orders": len(unassigned_orders),
        "total_loaded_quantity": round(total_loaded_quantity, 2),
        "total_distance": cost_data["total_distance"],
        "variable_cost": cost_data["variable_cost"],
        "total_cost": cost_data["total_cost"],
        "truck_utilization": utilization
    }