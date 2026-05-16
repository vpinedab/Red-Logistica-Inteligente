# app/main.py

"""
Pipeline de Ejecución Principal

Este módulo orquesta el flujo de trabajo logístico inteligente completo.

Etapas del pipeline:
1. Carga de datos de demanda simulados
2. Entrenamiento del modelo de predicción de demanda mediante aprendizaje automático
3. Generación de predicciones de demanda
4. Transformación de la demanda prevista en pedidos logísticos
5. Ejecución de la simulación logística y el pipeline de enrutamiento
6. Evaluación de los resultados operativos

El objetivo es simular una red logística autónoma
capaz de tomar decisiones operativas basadas en la demanda.

Integración de aprendizaje automático:
- Regresor de bosque aleatorio para la predicción de la demanda
- Métricas de predicción:

* MAE -> Error absoluto medio
* RMSE -> Error cuadrático medio
* MAPE -> Error porcentual absoluto medio
"""

from app.logistics import (
    logistics_summary,
    load_demand
)

from app.order_adapter import create_orders_from_demand

from app.logistics_engine import (
    run_logistics_pipeline_by_date,
    print_logistics_results
)

from app.demand_forecast_model import (
    train_demand_model,
    predict_demand,
    save_forecast_results
)


def main():
    print("SMART LOGISTICS PROJECT")
    print("=======================")
    print()

    logistics_summary()

    print("Cargando demanda simulada...")
    demand_df = load_demand()

    print("Entrenando modelo de prediccion de demanda...")
    model, feature_columns, metrics = train_demand_model(
        demand_df
    )

    print()
    print("Metricas del modelo:")

    for metric, value in metrics.items():
        print(f"{metric}: {value}")

    print()
    print("Generando predicciones de demanda...")

    forecast_df = predict_demand(
        demand_df,
        model,
        feature_columns
    )

    save_forecast_results(
        forecast_df,
        metrics
    )

    print()
    print(
        "Convirtiendo demanda pronosticada "
        "en pedidos logísticos..."
    )

    orders = create_orders_from_demand(
        forecast_df
    )

    print()
    print(
        "Ejecutando motor logistico "
        "sobre demanda pronosticada..."
    )

    results_by_date = (
        run_logistics_pipeline_by_date(
            orders,
            seed=42,
            max_days=5
        )
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