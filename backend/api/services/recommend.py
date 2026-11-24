def format_duration(seconds: float) -> str:
    total_mins = int(round(seconds / 60))
    hours = total_mins // 60
    mins = total_mins % 60
    return f"{hours}h {mins}m" if hours > 0 else f"{mins}m"


def rank_and_recommend(routes: list) -> list:
    for route in routes:
        miles_by_level = {
            "Low": 0.0,
            "Moderate": 0.0,
            "High": 0.0,
            "Severe": 0.0,
            "No Travel": 0.0,
        }
        weighted_score_sum = 0.0
        total_covered = 0.0
        has_no_travel = False

        for cp in route["checkpoints"]:
            lvl = cp["risk"]["level"]
            sc = cp["risk"]["score"]
            cov = cp["miles_covered"]
            miles_by_level[lvl] += cov
            weighted_score_sum += sc * cov
            total_covered += cov
            if lvl == "No Travel":
                has_no_travel = True

        avg_risk = (weighted_score_sum / total_covered) if total_covered > 0 else 0.0

        route["duration_formatted"] = format_duration(route["duration_seconds"])
        route["has_no_travel"] = has_no_travel
        route["risk_summary"] = {
            "low_miles": round(miles_by_level["Low"], 1),
            "moderate_miles": round(miles_by_level["Moderate"], 1),
            "high_miles": round(miles_by_level["High"], 1),
            "severe_miles": round(miles_by_level["Severe"], 1),
            "no_travel_miles": round(miles_by_level["No Travel"], 1),
            "avg_risk": round(avg_risk, 2),
        }

    # Exact assessment sorting priority (with No Travel prioritized above Severe):
    # 1. Fewest No Travel miles
    # 2. Fewest Severe miles
    # 3. Fewest High miles
    # 4. Lowest average risk
    # 5. Shortest travel times
    routes.sort(
        key=lambda r: (
            r["risk_summary"]["no_travel_miles"],
            r["risk_summary"]["severe_miles"],
            r["risk_summary"]["high_miles"],
            r["risk_summary"]["avg_risk"],
            r["duration_seconds"],
        )
    )

    for idx, route in enumerate(routes):
        route["rank"] = idx + 1
        route["is_recommended"] = idx == 0

    if routes:
        best = routes[0]
        rs = best["risk_summary"]
        if len(routes) > 1:
            second = routes[1]["risk_summary"]
            if rs["no_travel_miles"] < second["no_travel_miles"]:
                reason = f"Fewest No Travel miles ({rs['no_travel_miles']} mi vs {second['no_travel_miles']} mi)"
            elif rs["severe_miles"] < second["severe_miles"]:
                reason = f"Fewest Severe risk miles ({rs['severe_miles']} mi vs {second['severe_miles']} mi)"
            elif rs["high_miles"] < second["high_miles"]:
                reason = f"Fewest High risk miles ({rs['high_miles']} mi vs {second['high_miles']} mi)"
            elif rs["avg_risk"] < second["avg_risk"]:
                reason = f"Lowest average risk score ({rs['avg_risk']} vs {second['avg_risk']})"
            else:
                reason = f"Shortest travel time ({best['duration_formatted']}) with tied safety metrics"
        else:
            reason = "Safest available route based on weather and travel time"

        best["recommendation_reason"] = reason
        if best["has_no_travel"]:
            best["warning"] = "Warning: Even the best available route contains No Travel conditions."
        else:
            best["warning"] = ""

    return routes