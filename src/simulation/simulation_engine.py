"""
simulation_engine.py

AI-Powered Logistics Routing Simulation Engine
----------------------------------------------

This module simulates the daily operational behavior of a logistics network
inspired by Amazon. It models warehouse constraints, truck capacity, route
congestion, and overload phenomena under stochastic demand.

Unlike later optimization modules, this version models only *baseline behavior*.

Input Datasets:
  - data/raw/demand_data.csv
  - data/raw/warehouses.csv
  - data/raw/routes.csv
  - data/raw/trucks.csv

Output:
  - data/results/simulation_results.csv
  - visualizations (PNG charts)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional


# =============================================================================
# Simulation Engine
# =============================================================================

class SimulationEngine:
    """
    Simulates daily logistics operations (no optimization yet).

    Steps per day:
    1. Aggregate total store demand
    2. Allocate demand to warehouses based on capacity
    3. Check truck load availability
    4. Simulate route congestion and overload
    5. Produce operational metrics
    """

    def __init__(
        self,
        demand_path="data/raw/demand_data.csv",
        warehouse_path="data/raw/warehouses.csv",
        route_path="data/raw/routes.csv",
        truck_path="data/raw/trucks.csv",
        seed: Optional[int] = 42,
    ):
        if seed is not None:
            np.random.seed(seed)

        # Load datasets
        self.demand_data = pd.read_csv(demand_path)
        self.warehouses = pd.read_csv(warehouse_path)
        self.routes = pd.read_csv(route_path)
        self.trucks = pd.read_csv(truck_path)

        self.demand_data["date"] = pd.to_datetime(self.demand_data["date"])
        self.daily_metrics = []

    # -------------------------------------------------------------------------
    def _simulate_day(self, date, day_data):
        """Simulates one day of logistics operation."""

        metrics = {
            "date": date,
            "total_demand": 0.0,
            "completed_deliveries": 0.0,
            "delayed_deliveries": 0.0,
            "overloaded_routes": 0,
            "warehouse_utilization": 0.0,
            "truck_utilization": 0.0,
            "active_event": "None",
        }

        # Detect active event
        active_event = day_data["event"].replace("None", np.nan).dropna().unique()
        if len(active_event) > 0:
            metrics["active_event"] = ", ".join(active_event)

        # Total store demand
        total_demand = day_data["demand"].sum()
        metrics["total_demand"] = total_demand

        # ---------------------------------------------------------------------
        # Step 1: Distribute demand to zones
        zone_demand = day_data.groupby("zone")["demand"].sum().to_dict()

        # Step 2: Assign zones to warehouses
        wh_stats = []
        for _, wh in self.warehouses.iterrows():
            wh_zone = wh["zone"]
            wh_demand = zone_demand.get(wh_zone, 0)

            # Apply 20% random uncertainty to simulate uneven region coverage
            wh_demand = wh_demand * np.random.uniform(0.9, 1.1)

            # Step 3: Apply warehouse capacity and truck constraints
            max_capacity = wh["max_capacity"]
            assigned_trucks = self.trucks[self.trucks["warehouse_id"] == wh["warehouse_id"]]
            truck_capacity = assigned_trucks["max_load"].sum()

            # Real effective throughput limited by both
            effective_capacity = min(max_capacity, truck_capacity)
            completed = min(wh_demand, effective_capacity)
            delayed = max(0, wh_demand - completed)

            wh_utilization = completed / max_capacity if max_capacity > 0 else 0
            truck_utilization = completed / truck_capacity if truck_capacity > 0 else 0

            wh_stats.append({
                "warehouse_id": wh["warehouse_id"],
                "completed": completed,
                "delayed": delayed,
                "wh_utilization": wh_utilization,
                "truck_utilization": truck_utilization,
            })

        df_wh = pd.DataFrame(wh_stats)

        # ---------------------------------------------------------------------
        # Step 4: Normalize totals to ensure physical constraints
        # Avoid completed > total_demand issue by scaling proportionally
        completed_total = df_wh["completed"].sum()
        delayed_total = df_wh["delayed"].sum()

        if completed_total + delayed_total > 0:
            scale_factor = total_demand / (completed_total + delayed_total)
        else:
            scale_factor = 1.0

        df_wh["completed"] *= scale_factor
        df_wh["delayed"] *= scale_factor

        completed_total = df_wh["completed"].sum()
        delayed_total = df_wh["delayed"].sum()

        # ---------------------------------------------------------------------
        # Step 5: Route congestion simulation
        route_df = self.routes.copy()
        congestion_factor = 1.3 if metrics["active_event"] != "None" else 1.0
        route_df["is_overloaded"] = 0

        for i, r in route_df.iterrows():
            congestion_trigger = np.random.random() < min(1.0, r["congestion_probability"] * congestion_factor)
            if congestion_trigger or (r["traffic_risk"] * congestion_factor > 0.75):
                route_df.loc[i, "is_overloaded"] = 1
        overloaded_routes = route_df["is_overloaded"].sum()

        # Delivery delays from congestion
        delay_multiplier = 1.0 + 0.05 * overloaded_routes / (len(route_df) + 1e-6)
        delayed_total *= delay_multiplier

        # ---------------------------------------------------------------------
        # Step 6: Update metrics
        metrics["completed_deliveries"] = min(completed_total, total_demand)
        metrics["delayed_deliveries"] = max(total_demand - metrics["completed_deliveries"], delayed_total)
        metrics["overloaded_routes"] = overloaded_routes
        metrics["warehouse_utilization"] = df_wh["wh_utilization"].mean()
        metrics["truck_utilization"] = df_wh["truck_utilization"].mean()

        # Ensure consistency
        if metrics["completed_deliveries"] + metrics["delayed_deliveries"] > total_demand:
            overflow = (metrics["completed_deliveries"] + metrics["delayed_deliveries"]) - total_demand
            metrics["delayed_deliveries"] -= overflow  # trim the excess
            metrics["delayed_deliveries"] = max(0.0, metrics["delayed_deliveries"])

        self.daily_metrics.append(metrics)

    # -------------------------------------------------------------------------
    def run(self):
        """Run full-year baseline simulation."""
        print("Running baseline logistics network simulation...\n")
        for date, group in self.demand_data.groupby("date"):
            self._simulate_day(date, group)
        return pd.DataFrame(self.daily_metrics)

    # -------------------------------------------------------------------------
    def export_results(self, df, path="data/results/simulation_results.csv"):
        """Save simulation results."""
        output_dir = Path(path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"Simulation results saved to: {path}")


# =============================================================================
# Visualization
# =============================================================================

class SimulationVisualizer:
    """Visualization tools for analyzing baseline simulation results."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])

    def plot_demand_vs_deliveries(self):
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(self.df["date"], self.df["total_demand"], label="Total Demand", color="#1976D2", linewidth=2)
        ax.plot(self.df["date"], self.df["completed_deliveries"], label="Completed Deliveries", color="#43A047", linewidth=2)
        ax.set_title("Daily Demand vs Completed Deliveries", fontsize=13, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Units")
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_delayed_deliveries(self):
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(self.df["date"], self.df["delayed_deliveries"], color="#E53935")
        ax.set_title("Delayed Deliveries Over Time", fontsize=13, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Units")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_overloaded_routes(self):
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(self.df["date"], self.df["overloaded_routes"], color="#FB8C00")
        ax.set_title("Overloaded Routes Over Time", fontsize=13, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Count")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_warehouse_utilization(self):
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(self.df["date"], self.df["warehouse_utilization"], color="#3949AB")
        ax.set_title("Warehouse Utilization", fontsize=13, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Utilization (0–1)")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_truck_utilization(self):
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(self.df["date"], self.df["truck_utilization"], color="#00897B")
        ax.set_title("Truck Utilization", fontsize=13, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Utilization (0–1)")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_event_congestion_spikes(self):
        fig, ax = plt.subplots(figsize=(12, 5))
        event_df = self.df[self.df["active_event"] != "None"]
        ax.scatter(event_df["date"], event_df["overloaded_routes"], color="#F44336", label="Event Days")
        ax.plot(self.df["date"], self.df["overloaded_routes"], color="#FFC107", alpha=0.7)
        ax.set_title("Event Congestion Spikes", fontsize=13, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Overloaded Routes")
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig


# =============================================================================
# Main Execution
# =============================================================================

def main():
    print("=" * 60)
    print("AI-POWERED LOGISTICS BASELINE SIMULATION")
    print("=" * 60)

    engine = SimulationEngine()
    df_results = engine.run()
    engine.export_results(df_results, "data/results/simulation_results.csv")

    print("\nSummary Statistics:")
    print(df_results.describe().round(2))
    print("\nEvent Days Detected:", df_results[df_results["active_event"] != "None"].shape[0])

    # Visualization
    vis = SimulationVisualizer(df_results)
    output_dir = Path("data/results")
    vis.plot_demand_vs_deliveries().savefig(output_dir / "demand_vs_deliveries.png", dpi=150)
    vis.plot_delayed_deliveries().savefig(output_dir / "delayed_deliveries.png", dpi=150)
    vis.plot_overloaded_routes().savefig(output_dir / "overloaded_routes.png", dpi=150)
    vis.plot_warehouse_utilization().savefig(output_dir / "warehouse_utilization.png", dpi=150)
    vis.plot_truck_utilization().savefig(output_dir / "truck_utilization.png", dpi=150)
    vis.plot_event_congestion_spikes().savefig(output_dir / "event_spikes.png", dpi=150)

    print("\nVisual outputs saved under data/results/")
    print("=" * 60)

    plt.show()
    return df_results


if __name__ == "__main__":
    main()
