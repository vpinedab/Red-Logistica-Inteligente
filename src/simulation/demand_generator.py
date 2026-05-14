"""
demand_generator.py

AI-Powered Logistics Demand Simulation
--------------------------------------

This module simulates a realistic logistics network inspired by Amazon.
It generates one full year of daily demand across multiple zones and stores,
capturing cyclic patterns, stochastic fluctuations, and overload risk.

The generated data is used as input for:
- dynamic truck routing
- warehouse-to-store optimization
- congestion handling
- demand forecasting

Output: data/raw/demand_data.csv
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


# =============================================================================
# Configuration Structures
# =============================================================================

@dataclass
class StoreConfig:
    """Represents a single store’s base configuration."""
    store_id: str
    zone: str
    base_daily_demand: float
    volatility: float
    event_sensitivity: float


@dataclass
class EventConfig:
    """Represents a major logistics event."""
    name: str
    start_day: int
    duration: int
    multiplier: float
    overload_boost: float


# =============================================================================
# Demand Generator
# =============================================================================

class DemandGenerator:
    """
    Core engine that simulates daily demand for each store across all logistics zones.
    """

    def __init__(self, start_date: str = "2026-01-01", num_days: int = 365, seed: Optional[int] = 42):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.num_days = num_days
        if seed is not None:
            np.random.seed(seed)
        self.stores = self._create_stores()
        self.events = self._create_events()

    # -------------------------------------------------------------------------
    # Zone and Store Configuration
    # -------------------------------------------------------------------------
    def _create_stores(self) -> list[StoreConfig]:
        """Define stores within each zone."""
        zone_definitions = {
            "Urban": (5, 1400, 0.25, 1.3),
            "Suburban": (4, 1000, 0.18, 1.0),
            "Industrial": (3, 1600, 0.15, 1.1),
            "Port": (2, 1300, 0.20, 1.4),
            "Airport": (2, 1200, 0.22, 1.5),
            "North": (3, 1100, 0.19, 1.0),
            "South": (3, 1200, 0.21, 1.0),
            "Center": (4, 1500, 0.17, 1.1)
        }

        stores = []
        sid = 1
        for zone, (count, base, vol, sens) in zone_definitions.items():
            for i in range(count):
                stores.append(StoreConfig(
                    store_id=f"{zone[:2].upper()}-{sid:03d}",
                    zone=zone,
                    base_daily_demand=base * np.random.uniform(0.9, 1.1),
                    volatility=vol * np.random.uniform(0.8, 1.2),
                    event_sensitivity=sens * np.random.uniform(0.8, 1.2)
                ))
                sid += 1
        return stores

    def _create_events(self) -> list[EventConfig]:
        """Define major logistics events."""
        return [
            EventConfig("Summer Sale", 180, 14, 1.5, 0.3),
            EventConfig("Black Friday", 330, 4, 3.0, 0.8),
            EventConfig("Christmas Season", 340, 20, 2.5, 0.6),
            EventConfig("Flash Sale", 85, 2, 1.8, 0.4)
        ]

    # -------------------------------------------------------------------------
    # Demand Modeling
    # -------------------------------------------------------------------------
    def _weekly_cycle(self, weekday: int, zone: str) -> float:
        """Weekly cyclic demand per zone."""
        if weekday >= 5:  # weekend
            return {"Urban": 1.3, "Suburban": 1.2, "Industrial": 0.9,
                    "Port": 1.1, "Airport": 1.1, "North": 1.0,
                    "South": 1.1, "Center": 1.2}.get(zone, 1.0)
        else:
            return {"Urban": 1.0, "Suburban": 1.0, "Industrial": 1.2,
                    "Port": 1.0, "Airport": 1.0, "North": 1.0,
                    "South": 1.0, "Center": 1.0}.get(zone, 1.0)

    def _seasonal_cycle(self, day_of_year: int) -> float:
        """Seasonal pattern with Q4 rise."""
        return 1.0 + 0.15 * np.sin((2 * np.pi * (day_of_year - 300)) / 365)

    def _monthly_cycle(self, day_of_month: int, days_in_month: int) -> float:
        """Mild monthly fluctuations (mid-month and end-of-month peaks)."""
        pos = day_of_month / max(1, days_in_month)
        return 1.0 + 0.05 * np.sin(2 * np.pi * pos)

    def _get_event_multiplier(self, day_of_year: int, sensitivity: float) -> tuple[float, str]:
        """Retrieve any active event and its demand multiplier."""
        for e in self.events:
            if e.start_day <= day_of_year < e.start_day + e.duration:
                return e.multiplier * sensitivity, e.name
        return 1.0, "None"

    def _add_stochastic_noise(self, demand: float, volatility: float) -> float:
        """Apply random variability to demand."""
        noise = np.random.normal(0, demand * volatility)
        if np.random.rand() < 0.03:
            noise += demand * volatility * np.random.uniform(1.5, 3)
        return max(0, demand + noise)

    def _overload_risk(self, demand: float, base: float, event_mult: float, zone: str) -> float:
        """Compute overload risk score 0–1."""
        ratio = demand / (base + 1e-6)
        zone_weight = {
            "Urban": 0.6, "Suburban": 0.4, "Industrial": 0.7,
            "Port": 0.8, "Airport": 0.9, "North": 0.5,
            "South": 0.5, "Center": 0.6
        }[zone]
        risk = ratio * 0.6 + event_mult * 0.25 + zone_weight * 0.15
        return min(1.0, round(risk, 3))

    # -------------------------------------------------------------------------
    # Main Simulation Logic
    # -------------------------------------------------------------------------
    def generate(self) -> pd.DataFrame:
        """Generate full daily dataset for all stores."""
        records = []
        for d in range(self.num_days):
            date = self.start_date + timedelta(days=d)
            weekday = date.weekday()
            day_of_year = date.timetuple().tm_yday
            day_of_month = date.day
            days_in_month = (datetime(date.year, date.month % 12 + 1, 1) - timedelta(days=1)).day

            season_factor = self._seasonal_cycle(day_of_year)
            month_factor = self._monthly_cycle(day_of_month, days_in_month)

            for store in self.stores:
                weekly_factor = self._weekly_cycle(weekday, store.zone)
                event_mult, event_name = self._get_event_multiplier(day_of_year, store.event_sensitivity)

                base = store.base_daily_demand * weekly_factor * month_factor * season_factor * event_mult
                demand = self._add_stochastic_noise(base, store.volatility)
                risk = self._overload_risk(demand, store.base_daily_demand, event_mult, store.zone)

                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "zone": store.zone,
                    "store_id": store.store_id,
                    "demand": round(demand, 2),
                    "event": event_name,
                    "overload_risk": risk
                })

        return pd.DataFrame(records)


# =============================================================================
# Visualization
# =============================================================================

class DemandVisualizer:
    """Generate visual analyses of simulated demand data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])

    def plot_demand_over_time(self):
        fig, ax = plt.subplots(figsize=(14, 6))
        total = self.df.groupby("date")["demand"].sum()
        ax.plot(total.index, total.values, color="#2196F3")
        ax.set_title("Total Logistics Demand Over Time (1 Year)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Total Demand")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_overload_risk(self):
        fig, ax = plt.subplots(figsize=(14, 6))
        avg_risk = self.df.groupby("date")["overload_risk"].mean()
        ax.plot(avg_risk.index, avg_risk.values, color="#E53935")
        ax.fill_between(avg_risk.index, avg_risk.values, alpha=0.3, color="#FFCDD2")
        ax.set_title("Average Overload Risk Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Overload Risk")
        ax.grid(alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_zone_comparison(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        zone_avg = self.df.groupby("zone")[["demand", "overload_risk"]].mean().sort_values("demand", ascending=False)
        zone_avg["demand"].plot(kind="bar", color="#42A5F5", ax=ax, alpha=0.8)
        ax2 = ax.twinx()
        zone_avg["overload_risk"].plot(color="#EF5350", marker="o", ax=ax2)
        ax.set_title("Zone Comparison: Average Demand and Overload Risk")
        ax.set_ylabel("Average Demand")
        ax2.set_ylabel("Overload Risk")
        plt.tight_layout()
        return fig

    def plot_event_spikes(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        event_avg = self.df[self.df["event"] != "None"].groupby("event")["demand"].mean().sort_values(ascending=False)
        event_avg.plot(kind="bar", color="#FFA726", ax=ax)
        ax.set_title("Average Demand During Major Events")
        ax.set_ylabel("Average Demand")
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_demand_heatmap(self):
        import seaborn as sns
        fig, ax = plt.subplots(figsize=(12, 6))
        pivot = self.df.groupby(["zone", self.df["date"].dt.month])["demand"].mean().unstack()
        sns.heatmap(pivot, cmap="YlGnBu", ax=ax, annot=False)
        ax.set_title("Average Monthly Demand by Zone")
        ax.set_xlabel("Month")
        ax.set_ylabel("Zone")
        plt.tight_layout()
        return fig


# =============================================================================
# Main Execution Entry
# =============================================================================

def main():
    print("=" * 60)
    print("AI-POWERED LOGISTICS DEMAND ENVIRONMENT SIMULATION")
    print("=" * 60)

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Simulating store-level logistics demand...")
    generator = DemandGenerator(seed=42)
    df = generator.generate()
    output_path = output_dir / "demand_data.csv"
    df.to_csv(output_path, index=False)
    print(f"      Data saved to: {output_path}")

    print("\n[2/3] Summary Statistics:")
    print(df.groupby("zone")[["demand", "overload_risk"]].mean().round(2))
    print("\nEvents Included:", df["event"].unique())

    print("\n[3/3] Creating visualizations...")
    vis = DemandVisualizer(df)
    vis.plot_demand_over_time().savefig(output_dir / "demand_over_time.png", dpi=150, bbox_inches="tight")
    vis.plot_overload_risk().savefig(output_dir / "overload_risk.png", dpi=150, bbox_inches="tight")
    vis.plot_zone_comparison().savefig(output_dir / "zone_comparison.png", dpi=150, bbox_inches="tight")
    vis.plot_event_spikes().savefig(output_dir / "event_spikes.png", dpi=150, bbox_inches="tight")
    vis.plot_demand_heatmap().savefig(output_dir / "demand_heatmap.png", dpi=150, bbox_inches="tight")

    print("\nSimulation complete. Visual outputs saved under data/raw/.")
    print("=" * 60)
    plt.show()
    return df


if __name__ == "__main__":
    df = main()
