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