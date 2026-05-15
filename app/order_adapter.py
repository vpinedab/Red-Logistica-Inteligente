# app/order_adapter.py

def create_orders_from_demand(demand_df):
    """
    Convierte la demanda simulada/pronosticada en pedidos logísticos.

    La demanda representa lo que la tienda espera necesitar.
    El pedido representa lo que la tienda solicita al sistema logístico.

    En esta primera versión:
        requested_quantity = forecasted_demand
    """
    orders = []

    for _, row in demand_df.iterrows():
        forecasted_demand = float(row["demand"])

        order = {
            "date": row["date"],
            "store_id": row["store_id"],
            "zone": row["zone"],
            "forecasted_demand": forecasted_demand,
            "requested_quantity": forecasted_demand,
            "event": row.get("event", "None"),
            "overload_risk": row.get("overload_risk", 0)
        }

        orders.append(order)

    return orders