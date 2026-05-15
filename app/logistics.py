# app/logistics.py

import pandas as pd
from pathlib import Path


DATA_RAW_PATH = Path("data/raw")


def load_warehouses(path=DATA_RAW_PATH / "warehouses.csv"):
    """
    Carga los almacenes generados por logistics_network.py.
    """
    return pd.read_csv(path)


def load_trucks(path=DATA_RAW_PATH / "trucks.csv"):
    """
    Carga los camiones generados por logistics_network.py.
    """
    return pd.read_csv(path)


def load_routes(path=DATA_RAW_PATH / "routes.csv"):
    """
    Carga las rutas almacén-tienda generadas por logistics_network.py.
    """
    return pd.read_csv(path)


def load_demand(path=DATA_RAW_PATH / "demand_data.csv"):
    """
    Carga la demanda diaria generada por demand_generator.py.
    """
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def get_nearest_warehouse_for_store(store_id, routes_df=None):
    """
    Encuentra el almacén más cercano para una tienda usando routes.csv.
    """
    if routes_df is None:
        routes_df = load_routes()

    store_routes = routes_df[routes_df["store_id"] == store_id]

    if store_routes.empty:
        return None, None

    best_route = store_routes.sort_values("distance_km").iloc[0]

    return best_route["warehouse_id"], best_route["distance_km"]


def get_route_data(warehouse_id, store_id, routes_df=None):
    """
    Devuelve la ruta específica entre un almacén y una tienda.
    """
    if routes_df is None:
        routes_df = load_routes()

    match = routes_df[
        (routes_df["warehouse_id"] == warehouse_id) &
        (routes_df["store_id"] == store_id)
    ]

    if match.empty:
        return None

    return match.iloc[0].to_dict()


def logistics_summary():
    """
    Imprime resumen de la red logística generada.
    """
    warehouses = load_warehouses()
    trucks = load_trucks()
    routes = load_routes()

    print("RESUMEN LOGISTICO")
    print("-----------------")
    print(f"Almacenes: {len(warehouses)}")
    print(f"Camiones: {len(trucks)}")
    print(f"Rutas: {len(routes)}")
    print()