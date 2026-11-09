def calculate_rescue_priority(
    flood_exposure,
    population_vulnerability,
    emergency_reports,
    accessibility_risk
):
    """
    Prototype rescue-priority scoring engine.

    Inputs are scores from 0 to 100.
    Weights are illustrative design choices, not validated.
    """

    weights = {
        "flood_exposure": 0.35,
        "population_vulnerability": 0.25,
        "emergency_reports": 0.20,
        "accessibility_risk": 0.20
    }

    scores = {
        "flood_exposure": flood_exposure,
        "population_vulnerability": population_vulnerability,
        "emergency_reports": emergency_reports,
        "accessibility_risk": accessibility_risk
    }

    for name, value in scores.items():
        if not 0 <= value <= 100:
            raise ValueError(f"{name} must be between 0 and 100")

    priority_score = sum(
        scores[name] * weights[name]
        for name in weights
    )

    if priority_score >= 70:
        priority = "CRITICAL"
    elif priority_score >= 50:
        priority = "HIGH"
    elif priority_score >= 30:
        priority = "MODERATE"
    else:
        priority = "LOW"

    return {
        "priority_score": round(priority_score, 2),
        "priority_level": priority,
        "component_scores": scores,
        "weights": weights,
        "disclaimer": (
            "Illustrative prototype score; not an operational "
            "rescue dispatch recommendation."
        )
    }


if __name__ == "__main__":
    result = calculate_rescue_priority(
        flood_exposure=85,
        population_vulnerability=70,
        emergency_reports=90,
        accessibility_risk=75
    )

    print(result)
    