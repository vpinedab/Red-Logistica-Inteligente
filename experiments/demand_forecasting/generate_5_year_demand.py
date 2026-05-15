# experiments/demand_forecasting/generate_5_year_demand.py

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.simulation.demand_generator import DemandGenerator


OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "demand_data_5_years.csv"


def main():
    """
    Genera 5 años de demanda simulada para experimentar con forecasting.

    No modifica el archivo principal demand_data.csv.
    Guarda una versión separada:

        data/raw/demand_data_5_years.csv
    """

    print("=" * 60)
    print("GENERATING 5-YEAR DEMAND DATASET")
    print("=" * 60)

    generator = DemandGenerator(
        start_date="2026-01-01",
        num_days=365 * 5,
        seed=42
    )

    df = generator.generate()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Data saved to: {OUTPUT_PATH}")
    print()
    print("Dataset summary:")
    print(f"Rows: {len(df)}")
    print(f"Stores: {df['store_id'].nunique()}")
    print(f"Zones: {df['zone'].nunique()}")
    print(f"Start date: {df['date'].min()}")
    print(f"End date: {df['date'].max()}")
    print()
    print("Events included:")
    print(df["event"].unique())
    print("=" * 60)

    return df


if __name__ == "__main__":
    main()