# app/main.py

"""
Pipeline de Ejecución Principal

Este módulo orquesta el flujo de trabajo logístico inteligente completo.
"""

from app.logistics import (
    logistics_summary,
    load_demand,
)

from app.order_adapter import create_orders_from_demand

from app.logistics_engine import (
    run_logistics_pipeline_by_date,
    print_logistics_results,
)

from app.demand_forecast_model import (
    train_demand_model,
    predict_demand,
    save_forecast_results,
)

from app.visualizations import (
    save_forecast_plot,
    save_zone_demand_plot,
)

from app.visualizations import (
    save_forecast_plot,
    save_zone_demand_plot,
    save_kpi_dashboard,
)


def main():
    print("SMART LOGISTICS PROJECT")
    print("=======================")
    print()

    logistics_summary()

    print("Cargando demanda simulada...")
    demand_df = load_demand()

    print("Entrenando modelo de prediccion de demanda...")
    model, feature_columns, metrics = train_demand_model(demand_df)

    print()
    print("Metricas del modelo:")

    for metric, value in metrics.items():
        print(f"{metric}: {value}")

    print()
    print("Generando predicciones de demanda...")

    forecast_df = predict_demand(
        demand_df,
        model,
        feature_columns,
    )

    save_forecast_results(
        forecast_df,
        metrics,
    )

    print("Forecast guardado en outputs/demand_forecast_results.csv")
    print("Metricas guardadas en outputs/demand_model_metrics.csv")

    save_forecast_plot(forecast_df)
    save_zone_demand_plot(forecast_df)

    print("Graficas guardadas en outputs/")

    print()
    print(
        "Convirtiendo demanda pronosticada "
        "en pedidos logísticos..."
    )

    orders = create_orders_from_demand(forecast_df)

    print()
    print(
        "Ejecutando motor logistico "
        "sobre demanda pronosticada..."
    )

    results_by_date = run_logistics_pipeline_by_date(
        orders,
        seed=42,
        max_days=5,
    )

    for date, results in results_by_date.items():
        print()
        print(f"RESULTADOS PARA FECHA: {date}")
        print("--------------------------------")

        print_logistics_results(results)

    save_kpi_dashboard(results_by_date)

    print("Dashboard KPI guardado en outputs/")

    print()
    print("Archivos generados en carpeta outputs/")
    print("Ejecucion finalizada.")


if __name__ == "__main__":
    main()