import os

import matplotlib.pyplot as plt
import pandas as pd


def save_forecast_plot(forecast_df):
    os.makedirs("outputs", exist_ok=True)

    plot_df = forecast_df.copy()
    plot_df["date"] = pd.to_datetime(plot_df["date"])

    daily_df = (
        plot_df.groupby("date")[["demand", "predicted_demand"]]
        .sum()
        .reset_index()
    )

    plt.figure(figsize=(10, 5))
    plt.plot(daily_df["date"], daily_df["demand"], marker="o", label="Demanda real")
    plt.plot(
        daily_df["date"],
        daily_df["predicted_demand"],
        marker="o",
        label="Demanda predicha",
    )

    plt.title("Demanda real vs demanda predicha")
    plt.xlabel("Fecha")
    plt.ylabel("Demanda total")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig("outputs/forecast_vs_real.png")
    plt.close()


def save_zone_demand_plot(forecast_df):
    os.makedirs("outputs", exist_ok=True)

    zone_df = (
        forecast_df.groupby("zone")["predicted_demand"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(8, 5))
    zone_df.plot(kind="bar")

    plt.title("Demanda predicha por zona")
    plt.xlabel("Zona")
    plt.ylabel("Demanda predicha total")
    plt.tight_layout()

    plt.savefig("outputs/predicted_demand_by_zone.png")
    plt.close()

def save_kpi_dashboard(results_by_date):
    os.makedirs("outputs", exist_ok=True)

    dates = []
    total_costs = []
    service_levels = []
    deliveries = []
    delay_costs = []

    for date, results in results_by_date.items():
        dates.append(str(date)[:10])

        total_costs.append(
            results["final_total_cost"]
        )

        service_levels.append(
            results["delivery_metrics"]["service_level"]
        )

        deliveries.append(
            results["delivery_metrics"]["total_deliveries"]
        )

        delay_costs.append(
            results["delivery_metrics"]["total_delay_cost"]
        )

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].plot(dates, total_costs, marker="o")
    axes[0, 0].set_title("Costo Total")

    axes[0, 1].plot(dates, service_levels, marker="o")
    axes[0, 1].set_title("Nivel de Servicio (%)")

    axes[1, 0].bar(dates, deliveries)
    axes[1, 0].set_title("Entregas Totales")

    axes[1, 1].bar(dates, delay_costs)
    axes[1, 1].set_title("Costo por Retrasos")

    for ax in axes.flat:
        ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    plt.savefig("outputs/logistics_kpi_dashboard.png")
    plt.close()