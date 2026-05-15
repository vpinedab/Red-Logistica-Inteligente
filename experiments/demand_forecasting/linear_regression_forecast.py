# experiments/demand_forecasting/linear_regression_forecast.py

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEMAND_PATH = PROJECT_ROOT / "data" / "raw" / "demand_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_PATH = OUTPUT_DIR / "forecast_results.csv"


def load_demand_data():
    """
    Carga la demanda simulada generada por demand_generator.py.
    """
    df = pd.read_csv(DEMAND_PATH)
    df["date"] = pd.to_datetime(df["date"])

    return df


def create_features(df):
    """
    Crea variables predictoras a partir de la fecha.

    La variable objetivo sigue siendo:
        demand

    Las variables nuevas son:
        weekday
        month
        day_of_year
        is_weekend
    """
    df = df.copy()

    df["weekday"] = df["date"].dt.weekday
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)

    return df


def temporal_train_test_split(df, train_ratio=0.8):
    """
    Separa los datos respetando el tiempo.
    
    """
    unique_dates = sorted(df["date"].unique())
    split_index = int(len(unique_dates) * train_ratio)

    train_dates = unique_dates[:split_index]
    test_dates = unique_dates[split_index:]

    train_df = df[df["date"].isin(train_dates)].copy()
    test_df = df[df["date"].isin(test_dates)].copy()

    return train_df, test_df


def build_model():
    """
    Construye una regresión lineal con preprocesamiento.

    Variables numéricas:
        weekday, month, day_of_year, is_weekend, overload_risk

    Variables categóricas:
        zone, event, store_id

    OneHotEncoder convierte texto en columnas numéricas 0/1.
    """
    numeric_features = [
        "weekday",
        "month",
        "day_of_year",
        "is_weekend",
        "overload_risk"
    ]

    categorical_features = [
        "zone",
        "event",
        "store_id"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression())
        ]
    )

    return model, numeric_features + categorical_features


def train_and_evaluate():
    """
    Ejecuta el experimento completo.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_demand_data()
    df = create_features(df)

    train_df, test_df = temporal_train_test_split(df, train_ratio=0.8)

    model, feature_columns = build_model()

    X_train = train_df[feature_columns]
    y_train = train_df["demand"]

    X_test = test_df[feature_columns]
    y_test = test_df["demand"]

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    # Evitamos predicciones negativas porque la demanda no puede ser negativa.
    predictions = np.maximum(predictions, 0)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    results_df = test_df.copy()
    results_df["forecasted_demand"] = predictions
    results_df["absolute_error"] = abs(results_df["demand"] - results_df["forecasted_demand"])
    results_df["squared_error"] = (results_df["demand"] - results_df["forecasted_demand"]) ** 2

    results_df.to_csv(OUTPUT_PATH, index=False)

    print("=" * 60)
    print("LINEAR REGRESSION DEMAND FORECAST EXPERIMENT")
    print("=" * 60)
    print()
    print(f"Input data: {DEMAND_PATH}")
    print(f"Output saved to: {OUTPUT_PATH}")
    print()
    print("Temporal split:")
    print(f"Train dates: {train_df['date'].min().date()} to {train_df['date'].max().date()}")
    print(f"Test dates:  {test_df['date'].min().date()} to {test_df['date'].max().date()}")
    print()
    print("Dataset size:")
    print(f"Train rows: {len(train_df)}")
    print(f"Test rows:  {len(test_df)}")
    print()
    print("Forecast metrics:")
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²:   {r2:.4f}")
    print()
    print("Sample predictions:")
    print(
        results_df[
            ["date", "store_id", "zone", "event", "demand", "forecasted_demand", "absolute_error"]
        ].head(10).round(2)
    )
    print("=" * 60)

    return results_df


if __name__ == "__main__":
    train_and_evaluate()