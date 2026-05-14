"""
logistics_network.py

AI-Powered Logistics Infrastructure Generator
---------------------------------------------

This module simulates the *base logistics network* for an AI routing system inspired by Amazon.

It builds the static infrastructure for:
- truck routing
- congestion handling
- overload management
- dynamic route optimization (future module)

This module **does not perform optimization** yet.

It generates:
- Warehouses (with capacities and trucks)
- Store connections to warehouses
- Routes between warehouses and stores
- Base traffic/congestion metrics

Outputs:
  data/raw/warehouses.csv
  data/raw/routes.csv
  data/raw/trucks.csv
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# =============================================================================
# Data Configurations
# =============================================================================

@dataclass
class WarehouseConfig:
    warehouse_id: str
    zone: str
    max_capacity: float
    truck_count: int


@dataclass
class TruckConfig:
    truck_id: str
    warehouse_id: str
    max_load: float
    fuel_efficiency: float
    average_speed: float


# =============================================================================
# Logistics Network Generator
# =============================================================================

class LogisticsNetworkGenerator:
    """
    Constructs the static logistics network topology:
    - Warehouses distributed across zones
    - Store connections and route data
    - Truck assignments
    """

    def __init__(self, seed: Optional[int] = 42):
        if seed is not None:
            np.random.seed(seed)

        # Default zones compatible with demand generator
        self.zones = [
            "Urban", "Suburban", "Industrial", "Port", "Airport",
            "North", "South", "Center"
        ]

        # Warehouse per zone mix
        self.warehouse_templates = [
            ("W1", "Urban"), ("W2", "Industrial"),
            ("W3", "Center"), ("W4", "South")
        ]

    # -------------------------------------------------------------------------
    def generate_warehouses(self) -> pd.DataFrame:
        """Creates initial warehouse infrastructure with realistic capacities."""
        records = []
        for wid, zone in self.warehouse_templates:
            base_capacity = np.random.randint(10000, 20000)
            trucks = np.random.randint(8, 15)
            records.append(WarehouseConfig(
                warehouse_id=wid,
                zone=zone,
                max_capacity=base_capacity,
                truck_count=trucks
            ).__dict__)
        return pd.DataFrame(records)

    # -------------------------------------------------------------------------
    def generate_trucks(self, warehouses: pd.DataFrame) -> pd.DataFrame:
        """Generate all truck configurations for each warehouse."""
        trucks = []
        for _, wh in warehouses.iterrows():
            for i in range(wh.truck_count):
                truck_id = f"{wh.warehouse_id}-T{i+1:03d}"
                max_load = np.random.uniform(8000, 15000)
                fuel_eff = np.random.uniform(3.5, 6.5)   # km/l
                avg_speed = np.random.uniform(50, 90)
                trucks.append(TruckConfig(
                    truck_id=truck_id,
                    warehouse_id=wh.warehouse_id,
                    max_load=round(max_load, 2),
                    fuel_efficiency=round(fuel_eff, 2),
                    average_speed=round(avg_speed, 1)
                ).__dict__)
        return pd.DataFrame(trucks)

    # -------------------------------------------------------------------------
    def _zone_distance_profile(self, zone: str) -> tuple:
        """Return typical distance, speed, and traffic risk ranges by zone."""
        profiles = {
            "Urban": (10, 30, 0.7),
            "Suburban": (30, 60, 0.4),
            "Industrial": (40, 70, 0.5),
            "Port": (20, 40, 0.8),
            "Airport": (30, 50, 0.7),
            "North": (70, 120, 0.5),
            "South": (70, 100, 0.5),
            "Center": (40, 80, 0.4)
        }
        return profiles.get(zone, (50, 80, 0.5))

    # -------------------------------------------------------------------------
    def generate_routes(self, stores: pd.DataFrame, warehouses: pd.DataFrame) -> pd.DataFrame:
        """
        Create routes connecting warehouses to stores with distances, capacities,
        and traffic risks determined stochastically based on zone type.
        """
        records = []

        for _, store in stores.iterrows():
            # Random number of warehouse connections (1-2)
            assigned_whs = warehouses.sample(np.random.choice([1, 2], p=[0.7, 0.3]))

            for _, wh in assigned_whs.iterrows():
                base_dist, dist_std, base_risk = self._zone_distance_profile(store["zone"])
                distance = np.random.normal(base_dist, dist_std / 4)
                travel_time = distance / np.random.uniform(40, 70)  # hours
                route_capacity = np.random.uniform(3000, 8000)
                traffic_risk = np.clip(np.random.normal(base_risk, 0.1), 0, 1)

                records.append({
                    "warehouse_id": wh["warehouse_id"],
                    "store_id": store["store_id"],
                    "zone": store["zone"],
                    "distance_km": round(distance, 2),
                    "average_travel_time_hr": round(travel_time, 2),
                    "route_capacity": round(route_capacity, 2),
                    "traffic_risk": round(traffic_risk, 2)
                })

        return pd.DataFrame(records)

    # -------------------------------------------------------------------------
    def simulate_traffic(self, df_routes: pd.DataFrame) -> pd.DataFrame:
        """Augment route DataFrame with congestion probability."""
        df = df_routes.copy()
        df["congestion_probability"] = np.clip(
            df["traffic_risk"] * np.random.uniform(0.5, 1.2, len(df)), 0, 1
        )
        return df


# =============================================================================
# Visualization
# =============================================================================

class NetworkVisualizer:
    """Provides plots of the generated logistics infrastructure."""

    def __init__(self, warehouses: pd.DataFrame, routes: pd.DataFrame, trucks: pd.DataFrame):
        self.wh = warehouses
        self.routes = routes
        self.trucks = trucks

    def plot_warehouses(self):
        fig, ax = plt.subplots(figsize=(7, 5))
        self.wh.plot(kind="bar", x="warehouse_id", y="max_capacity", ax=ax,
                     color="#42A5F5", legend=False)
        ax.set_title("Warehouse Capacity Distribution", fontweight="bold")
        ax.set_xlabel("Warehouse")
        ax.set_ylabel("Max Capacity (units)")
        ax.grid(alpha=0.3)
        return fig

    def plot_trucks(self):
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.hist(self.trucks["max_load"], bins=15, color="#66BB6A", alpha=0.7)
        ax.set_title("Truck Load Distribution", fontweight="bold")
        ax.set_xlabel("Max Load (kg)")
        ax.set_ylabel("Count")
        ax.grid(alpha=0.3)
        return fig

    def plot_routes(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(self.routes["distance_km"], self.routes["average_travel_time_hr"],
                   c=self.routes["traffic_risk"], cmap="coolwarm", alpha=0.7)
        ax.set_title("Route Distance vs Travel Time", fontweight="bold")
        ax.set_xlabel("Distance (km)")
        ax.set_ylabel("Avg Travel Time (hr)")
        plt.colorbar(ax.collections[0], ax=ax, label="Traffic Risk")
        return fig

    def plot_traffic_risk_distribution(self):
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.hist(self.routes["traffic_risk"], bins=15, color="#EF5350", alpha=0.7)
        ax.set_title("Traffic Risk Distribution", fontweight="bold")
        ax.set_xlabel("Traffic Risk (0–1)")
        ax.set_ylabel("Route Count")
        ax.grid(alpha=0.3)
        return fig


# =============================================================================
# Main Execution
# =============================================================================

def main():
    print("=" * 60)
    print("AI-POWERED LOGISTICS NETWORK GENERATION")
    print("=" * 60)

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # For demonstration, assume we have store data from demand_generator.py
    try:
        stores = pd.read_csv("data/raw/demand_data.csv")
        stores = stores[["store_id", "zone"]].drop_duplicates()
    except FileNotFoundError:
        # Create synthetic store placeholders if not found
        print("Warning: demand_data.csv not found. Generating synthetic store data.")
        stores = pd.DataFrame({
            "zone": np.random.choice(
                ["Urban", "Suburban", "Industrial", "Port", "Airport", "North", "South", "Center"], 30
            )
        })
        stores["store_id"] = [f"S{i+1:03d}" for i in range(len(stores))]

    # -------------------------------------------------------------------------
    print("\n[1/4] Generating Warehouses...")
    generator = LogisticsNetworkGenerator(seed=42)
    df_wh = generator.generate_warehouses()
    df_wh.to_csv(output_dir / "warehouses.csv", index=False)
    print("Warehouses created:", len(df_wh))

    print("\n[2/4] Generating Trucks...")
    df_trucks = generator.generate_trucks(df_wh)
    df_trucks.to_csv(output_dir / "trucks.csv", index=False)
    print("Trucks created:", len(df_trucks))

    print("\n[3/4] Generating Routes...")
    df_routes = generator.generate_routes(stores, df_wh)
    df_routes = generator.simulate_traffic(df_routes)
    df_routes.to_csv(output_dir / "routes.csv", index=False)
    print("Routes created:", len(df_routes))

    # -------------------------------------------------------------------------
    print("\n[4/4] Creating Visualizations...")
    vis = NetworkVisualizer(df_wh, df_routes, df_trucks)
    vis.plot_warehouses().savefig(output_dir / "warehouses_capacity.png", dpi=150, bbox_inches="tight")
    vis.plot_trucks().savefig(output_dir / "trucks_distribution.png", dpi=150, bbox_inches="tight")
    vis.plot_routes().savefig(output_dir / "route_distances.png", dpi=150, bbox_inches="tight")
    vis.plot_traffic_risk_distribution().savefig(output_dir / "traffic_risk.png", dpi=150, bbox_inches="tight")

    print(f"\nNetwork infrastructure generated in: {output_dir}")
    print("=" * 60)

    plt.show()
    return df_wh, df_routes, df_trucks


if __name__ == "__main__":
    df_wh, df_routes, df_trucks = main()
