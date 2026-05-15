# app/delivery_simulation.py

import random


AVERAGE_SPEED_KM_H = 40
TRAFFIC_PROBABILITY = 0.60
DELAY_PROBABILITY = 0.40
COST_PER_DELAY_HOUR = 80


def simulate_random_delay():
    """
    Simula retrasos adicionales no relacionados directamente con distancia:
    carga, descarga, espera, fallas menores o congestión en tienda.
    """
    has_delay = random.random() < DELAY_PROBABILITY

    if not has_delay:
        return {
            "has_delay": False,
            "delay_hours": 0
        }

    delay_hours = round(random.uniform(0.25, 1.5), 2)

    return {
        "has_delay": True,
        "delay_hours": delay_hours
    }


def simulate_delivery_for_order(order, truck_data=None):
    """
    Simula la entrega de un pedido usando información de:
    - la ruta
    - el tráfico
    - el camión asignado

    Ahora el pedido viene de una tienda, no de un cliente manual.
    """
    round_trip_distance = order["distance_km"] * 2

    if truck_data is not None:
        average_speed = truck_data.get("average_speed", AVERAGE_SPEED_KM_H)
    else:
        average_speed = AVERAGE_SPEED_KM_H

    base_time = round(round_trip_distance / average_speed, 2)

    traffic_risk = order.get("traffic_risk", 0)
    congestion_probability = order.get(
        "congestion_probability",
        TRAFFIC_PROBABILITY
    )

    has_traffic = random.random() < congestion_probability

    if has_traffic:
        if traffic_risk >= 0.7:
            traffic_level = "High"
            traffic_factor = round(random.uniform(1.5, 2.0), 2)
        elif traffic_risk >= 0.4:
            traffic_level = "Medium"
            traffic_factor = round(random.uniform(1.2, 1.5), 2)
        else:
            traffic_level = "Low"
            traffic_factor = round(random.uniform(1.05, 1.2), 2)
    else:
        traffic_level = "None"
        traffic_factor = 1.0

    delay_data = simulate_random_delay()

    time_with_traffic = base_time * traffic_factor
    total_time = round(time_with_traffic + delay_data["delay_hours"], 2)

    delay_cost = round(delay_data["delay_hours"] * COST_PER_DELAY_HOUR, 2)

    delivered_on_time = total_time <= 2.5

    return {
        "date": order.get("date"),
        "store_id": order["store_id"],
        "warehouse_id": order["warehouse_id"],
        "requested_quantity": order["requested_quantity"],
        "round_trip_distance": round(round_trip_distance, 2),
        "base_time_hours": base_time,
        "traffic_risk": traffic_risk,
        "congestion_probability": congestion_probability,
        "traffic_level": traffic_level,
        "traffic_factor": traffic_factor,
        "delay_hours": delay_data["delay_hours"],
        "total_time_hours": total_time,
        "delay_cost": delay_cost,
        "delivered_on_time": delivered_on_time
    }


def simulate_deliveries(truck_loads, seed=99):
    """
    Simula todas las entregas de todos los camiones.

    Usamos seed para que la simulación sea reproducible.
    """
    random.seed(seed)

    delivery_results = {}

    for truck_id, truck_data in truck_loads.items():
        delivery_results[truck_id] = []

        for order in truck_data["orders"]:
            result = simulate_delivery_for_order(order, truck_data)
            delivery_results[truck_id].append(result)

    return delivery_results


def calculate_delivery_metrics(delivery_results):
    """
    Calcula métricas agregadas de entregas.
    """
    total_deliveries = 0
    on_time_deliveries = 0
    delayed_deliveries = 0
    total_delivery_time = 0
    total_delay_cost = 0
    total_delivered_quantity = 0

    for truck_id, deliveries in delivery_results.items():
        for delivery in deliveries:
            total_deliveries += 1
            total_delivery_time += delivery["total_time_hours"]
            total_delay_cost += delivery["delay_cost"]
            total_delivered_quantity += delivery["requested_quantity"]

            if delivery["delivered_on_time"]:
                on_time_deliveries += 1
            else:
                delayed_deliveries += 1

    if total_deliveries == 0:
        service_level = 0
        average_delivery_time = 0
    else:
        service_level = round((on_time_deliveries / total_deliveries) * 100, 2)
        average_delivery_time = round(total_delivery_time / total_deliveries, 2)

    return {
        "total_deliveries": total_deliveries,
        "on_time_deliveries": on_time_deliveries,
        "delayed_deliveries": delayed_deliveries,
        "service_level": service_level,
        "average_delivery_time": average_delivery_time,
        "total_delay_cost": round(total_delay_cost, 2),
        "total_delivered_quantity": round(total_delivered_quantity, 2)
    }