# app/main.py

from app.logistics import (
    logistics_summary,
    load_demand
)

from app.order_adapter import create_orders_from_demand

from app.logistics_engine import (
    run_logistics_pipeline_by_date,
    print_logistics_results
)


def main():
    print("SMART LOGISTICS PROJECT")
    print("=======================")
    print()

    logistics_summary()

    print("Cargando demanda simulada...")
    demand_df = load_demand()

    print("Convirtiendo demanda en pedidos de tiendas...")
    orders = create_orders_from_demand(demand_df)

    print()
    print("Ejecutando motor logistico sobre pedidos derivados de demanda...")
    results_by_date = run_logistics_pipeline_by_date(
        orders,
        seed=42,
        max_days=5
    )

    for date, results in results_by_date.items():
        print()
        print(f"RESULTADOS PARA FECHA: {date}")
        print("--------------------------------")
        print_logistics_results(results)

    print()
    print("Ejecucion finalizada.")


if __name__ == "__main__":
    main()