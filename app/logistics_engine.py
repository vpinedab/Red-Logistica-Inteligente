# app/logistics_engine.py

from app.routing import (
    assign_orders_to_warehouses,
    group_orders_by_warehouse,
    assign_orders_to_trucks,
    calculate_transport_cost,
    calculate_truck_utilization,
    routing_summary
)

from app.delivery_simulation import (
    simulate_deliveries,
    calculate_delivery_metrics
)


def validate_orders(orders):
    """
    Valida pedidos generados desde demand_data.csv.

    Cada pedido debe tener:
    - store_id
    - requested_quantity
    """
    valid_orders = []
    invalid_orders = []

    for order in orders:
        if "store_id" not in order or "requested_quantity" not in order:
            invalid_orders.append({
                "order": order,
                "reason": "Missing store_id or requested_quantity"
            })
            continue

        if order["requested_quantity"] <= 0:
            invalid_orders.append({
                "order": order,
                "reason": "requested_quantity must be positive"
            })
            continue

        valid_orders.append(order)

    return valid_orders, invalid_orders


def run_logistics_pipeline(orders, seed=42):
    """
    Ejecuta todo el flujo logístico para una tanda de pedidos.

    Entrada:
    [
        {
            "date": "2026-01-01",
            "store_id": "UR-001",
            "zone": "Urban",
            "forecasted_demand": 1400.5,
            "requested_quantity": 1400.5,
            "event": "None",
            "overload_risk": 0.72
        }
    ]
    """
    valid_orders, invalid_orders = validate_orders(orders)

    assigned_orders, warehouse_unassigned_orders = assign_orders_to_warehouses(
        valid_orders
    )

    grouped_orders = group_orders_by_warehouse(assigned_orders)

    truck_loads, truck_unassigned_orders = assign_orders_to_trucks(
        assigned_orders
    )

    unassigned_orders = warehouse_unassigned_orders + truck_unassigned_orders

    cost_data = calculate_transport_cost(truck_loads)
    truck_utilization = calculate_truck_utilization(truck_loads)
    route_summary = routing_summary(truck_loads, unassigned_orders)

    delivery_results = simulate_deliveries(truck_loads, seed=seed)
    delivery_metrics = calculate_delivery_metrics(delivery_results)

    final_total_cost = (
        cost_data["total_cost"] +
        delivery_metrics["total_delay_cost"]
    )

    results = {
        "input_orders": orders,
        "valid_orders": valid_orders,
        "invalid_orders": invalid_orders,
        "assigned_orders": assigned_orders,
        "grouped_orders": grouped_orders,
        "truck_loads": truck_loads,
        "unassigned_orders": unassigned_orders,
        "cost_data": cost_data,
        "truck_utilization": truck_utilization,
        "route_summary": route_summary,
        "delivery_results": delivery_results,
        "delivery_metrics": delivery_metrics,
        "final_total_cost": round(final_total_cost, 2)
    }

    return results


def run_logistics_pipeline_by_date(orders, seed=42, max_days=None):
    """
    Ejecuta el motor logístico por fecha.

    Recibe una lista de pedidos ya adaptados, no el DataFrame crudo.
    """
    orders_by_date = {}

    for order in orders:
        date = str(order["date"])

        if date not in orders_by_date:
            orders_by_date[date] = []

        orders_by_date[date].append(order)

    results_by_date = {}

    for i, (date, day_orders) in enumerate(orders_by_date.items()):
        if max_days is not None and i >= max_days:
            break

        results_by_date[date] = run_logistics_pipeline(
            day_orders,
            seed=seed + i
        )

    return results_by_date


def format_money(value):
    return f"${float(value):,.2f}"


def format_percent(value):
    return f"{float(value):.2f}%"


def print_logistics_results(results):
    """Imprime resultados principales del flujo logístico en formato limpio."""

    print("RESULTADOS DEL MOTOR LOGISTICO")
    print("==============================")
    print()

    print(f"Pedidos recibidos: {len(results['input_orders'])}")
    print(f"Pedidos validos: {len(results['valid_orders'])}")
    print(f"Pedidos invalidos: {len(results['invalid_orders'])}")
    print(f"Pedidos asignados a almacenes: {len(results['assigned_orders'])}")
    print(f"Pedidos no asignados: {len(results['unassigned_orders'])}")
    print()

    print("Costos logisticos:")
    cost_data = results["cost_data"]
    for key, value in cost_data.items():
        clean_key = key.replace("_", " ").capitalize()
        if "cost" in key:
            print(f"- {clean_key}: {format_money(value)}")
        else:
            print(f"- {clean_key}: {float(value):,.2f}")
    print()

    print("Utilizacion de camiones:")
    used_trucks = {
        truck_id: utilization
        for truck_id, utilization in results["truck_utilization"].items()
        if utilization > 0
    }

    for truck_id, utilization in used_trucks.items():
        print(f"- {truck_id}: {format_percent(utilization)}")
    print()

    print("Metricas de entrega:")
    delivery_metrics = results["delivery_metrics"]
    for key, value in delivery_metrics.items():
        clean_key = key.replace("_", " ").capitalize()
        if "cost" in key:
            print(f"- {clean_key}: {format_money(value)}")
        elif "rate" in key or "level" in key:
            print(f"- {clean_key}: {format_percent(value)}")
        else:
            print(f"- {clean_key}: {float(value):,.2f}")
    print()

    print(
        "Costo total final con incertidumbre: "
        f"{format_money(results['final_total_cost'])}"
    )