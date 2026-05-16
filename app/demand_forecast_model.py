import os
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


def prepare_features(df):
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["dayofweek"] = df["date"].dt.dayofweek

    df["event"] = df.get("event", "None").fillna("None")
    df["zone"] = df["zone"].fillna("Unknown")

    df = pd.get_dummies(df, columns=["zone", "event"], drop_first=True)

    return df


def train_demand_model(demand_df):
    df = prepare_features(demand_df)

    target = "demand"

    drop_cols = ["date", "store_id", target]

    X = df.drop(columns=[col for col in drop_cols if col in df.columns])
    y = df[target]

    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        max_depth=10
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)

    rmse = np.sqrt(
        mean_squared_error(y_test, predictions)
    )

    mape = np.mean(
        np.abs((y_test - predictions) / y_test)
    ) * 100

    metrics = {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2)
    }

    return model, X.columns.tolist(), metrics


def predict_demand(demand_df, model, feature_columns):
    df_original = demand_df.copy()

    df_features = prepare_features(demand_df)

    X = df_features.drop(
        columns=[
            col for col in [
                "date",
                "store_id",
                "demand"
            ]
            if col in df_features.columns
        ]
    )

    X = X.reindex(
        columns=feature_columns,
        fill_value=0
    )

    df_original["predicted_demand"] = model.predict(X)

    df_original["predicted_demand"] = (
        df_original["predicted_demand"]
        .round(2)
    )

    return df_original


def save_forecast_results(df, metrics):
    os.makedirs("outputs", exist_ok=True)

    df.to_csv(
        "outputs/demand_forecast_results.csv",
        index=False
    )

    metrics_df = pd.DataFrame([metrics])

    metrics_df.to_csv(
        "outputs/demand_model_metrics.csv",
        index=False
    )