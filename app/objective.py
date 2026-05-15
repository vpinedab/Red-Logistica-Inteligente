# app/objective.py


def calculate_objective_score(
    service_level,
    final_total_cost,
    unassigned_orders,
    delayed_deliveries,
    alpha=100,
    beta=0.001,
    gamma=50,
    delta=10
):
    """
    Calcula la utilidad logística del sistema.

    U = alpha * SL
        - beta * C_total
        - gamma * N_unassigned
        - delta * N_delayed

    Más alto significa mejor desempeño logístico.
    """

    objective_score = (
        alpha * service_level
        - beta * final_total_cost
        - gamma * unassigned_orders
        - delta * delayed_deliveries
    )

    return round(objective_score, 2)