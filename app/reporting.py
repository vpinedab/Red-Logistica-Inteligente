import os
import pandas as pd


def save_executive_summary(results_by_date):
    os.makedirs("outputs", exist_ok=True)

    rows = []

    for date, results in results_by_date.items():
        delivery_metrics = results["delivery_metrics"]

        rows.append({
            "date": str(date)[:10],
            "total_cost": float(results["final_total_cost"]),
            "service_level": float(delivery_metrics["service_level"]),
            "total_deliveries": int(delivery_metrics["total_deliveries"]),
            "delayed_deliveries": int(delivery_metrics["delayed_deliveries"]),
            "total_delay_cost": float(delivery_metrics["total_delay_cost"]),
            "total_delivered_quantity": float(delivery_metrics["total_delivered_quantity"]),
        })

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv("outputs/executive_summary.csv", index=False)

    return summary_df