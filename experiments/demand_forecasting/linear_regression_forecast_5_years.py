# experiments/demand_forecasting/linear_regression_forecast_5_years.py

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEMAND_PATH = PROJECT_ROOT / "data" / "raw" / "demand_data_5_years.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_PATH = OUTPUT_DIR / "forecast_results_5_years.csv"


def load_demand_data():
    """
    Carga el dataset de 5 años generado para forecasting.
    """
    df = pd.read_csv(DEMAND_PATH)
    df["date"] = pd.to_datetime(df["date"])

    return df


def create_features(df):
    """
    Crea variables predictoras a partir de la fecha.

    Variables creadas:
    - year
    - weekday
    - month
    - day_of_year
    - is_weekend
    """
    df = df.copy()

    df["year"] = df["date"].dt.year
    df["weekday"] = df["date"].dt.weekday
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)

    return df


def year_train_test_split(df, test_year=2030):
    """
    Separa entrenamiento y prueba por año.

    Entrenamiento:
        años anteriores a test_year

    Prueba:
        test_year completo

    Esto respeta la lógica temporal:
        pasado -> futuro
    """
    train_df = df[df["year"] < test_year].copy()
    test_df = df[df["year"] == test_year].copy()

    if train_df.empty:
        raise ValueError("El conjunto de entrenamiento está vacío.")

    if test_df.empty:
        raise ValueError("El conjunto de prueba está vacío.")

    return train_df, test_df


def build_model():
    """
    Construye el pipeline de regresión lineal.

    Variables numéricas:
    - weekday
    - month
    - day_of_year
    - is_weekend
    - overload_risk

    Variables categóricas:
    - zone
    - event
    - store_id

    No usamos year como variable predictora porque queremos que el modelo
    aprenda patrones estructurales, no simplemente una tendencia por año.
    """
    numeric_features = [
    "weekday",
    "month",
    "day_of_year",
    "is_weekend"
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

    feature_columns = numeric_features + categorical_features

    return model, feature_columns


def summarize_error_by_event(results_df):
    """
    Calcula métricas de error por tipo de evento.
    """
    summary = (
        results_df
        .groupby("event")
        .agg(
            rows=("demand", "count"),
            avg_demand=("demand", "mean"),
            avg_forecast=("forecasted_demand", "mean"),
            mae=("absolute_error", "mean"),
            rmse=("squared_error", lambda x: np.sqrt(np.mean(x)))
        )
        .reset_index()
        .sort_values("mae", ascending=False)
    )

    return summary


def train_and_evaluate():
    """
    Ejecuta el experimento completo:

    1. Carga 5 años de demanda simulada.
    2. Crea variables predictoras.
    3. Entrena con 2026-2029.
    4. Prueba con 2030.
    5. Calcula MAE, RMSE y R².
    6. Guarda predicciones en forecast_results_5_years.csv.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_demand_data()
    df = create_features(df)

    train_df, test_df = year_train_test_split(df, test_year=2030)

    model, feature_columns = build_model()

    X_train = train_df[feature_columns]
    y_train = train_df["demand"]

    X_test = test_df[feature_columns]
    y_test = test_df["demand"]

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    predictions = np.maximum(predictions, 0)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    results_df = test_df.copy()
    results_df["forecasted_demand"] = predictions
    results_df["absolute_error"] = abs(
        results_df["demand"] - results_df["forecasted_demand"]
    )
    results_df["squared_error"] = (
        results_df["demand"] - results_df["forecasted_demand"]
    ) ** 2

    results_df.to_csv(OUTPUT_PATH, index=False)

    event_summary = summarize_error_by_event(results_df)

    print("=" * 60)
    print("5-YEAR LINEAR REGRESSION DEMAND FORECAST")
    print("=" * 60)
    print()
    print(f"Input data: {DEMAND_PATH}")
    print(f"Output saved to: {OUTPUT_PATH}")
    print()
    print("Temporal split:")
    print(f"Train years: {train_df['year'].min()} to {train_df['year'].max()}")
    print(f"Test year:   {test_df['year'].min()}")
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
    print("Error by event:")
    print(event_summary.round(2))
    print()
    print("Sample predictions:")
    print(
        results_df[
            [
                "date",
                "store_id",
                "zone",
                "event",
                "demand",
                "forecasted_demand",
                "absolute_error"
            ]
        ]
        .head(10)
        .round(2)
    )
    print("=" * 60)

    return results_df


if __name__ == "__main__":
    train_and_evaluate()