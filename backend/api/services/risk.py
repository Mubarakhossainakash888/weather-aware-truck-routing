RISK_LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"]


def classify_wind(wind_mph: float) -> tuple[int, str]:
    if wind_mph >= 55:
        return 4, f"Wind {wind_mph} mph (>=55 mph)"
    if wind_mph >= 45:
        return 3, f"Wind {wind_mph} mph (45-54 mph)"
    if wind_mph >= 35:
        return 2, f"Wind {wind_mph} mph (35-44 mph)"
    if wind_mph >= 25:
        return 1, f"Wind {wind_mph} mph (25-34 mph)"
    return 0, ""


def classify_rain(rain_in: float) -> tuple[int, str]:
    if rain_in > 1.00:
        return 4, f"Rain {rain_in} in/hr (>1.00 in/hr)"
    if rain_in >= 0.50:
        return 3, f"Rain {rain_in} in/hr (0.50-1.00 in/hr)"
    if rain_in >= 0.25:
        return 2, f"Rain {rain_in} in/hr (0.25-0.50 in/hr)"
    if rain_in >= 0.10:
        return 1, f"Rain {rain_in} in/hr (0.10-0.25 in/hr)"
    return 0, ""


def classify_snow(snow_in: float) -> tuple[int, str]:
    if snow_in > 3.0:
        return 4, f"Snow {snow_in} in/hr (>3.0 in/hr)"
    if snow_in >= 2.0:
        return 3, f"Snow {snow_in} in/hr (2.0-3.0 in/hr)"
    if snow_in >= 1.0:
        return 2, f"Snow {snow_in} in/hr (1.0-2.0 in/hr)"
    if snow_in >= 0.5:
        return 1, f"Snow {snow_in} in/hr (0.5-1.0 in/hr)"
    return 0, ""


def evaluate_risk(wind_mph: float, rain_in: float, snow_in: float, load_lb: float) -> dict:
    w_score, w_reason = classify_wind(wind_mph)
    r_score, r_reason = classify_rain(rain_in)
    s_score, s_reason = classify_snow(snow_in)

    score = max(w_score, r_score, s_score)
    reasons = [r for r in (w_reason, r_reason, s_reason) if r]

    # Load rules
    if wind_mph >= 55:
        score = 4
    elif 45 <= wind_mph < 55 and load_lb > 30000:
        score = 4
        reasons.append(f"Heavy load {int(load_lb):,} lb (>30,000 lb) with 45-54 mph wind -> No Travel")
    elif 35 <= wind_mph < 45 and load_lb > 40000:
        if score < 3:
            score = 3
        reasons.append(f"Heavy load {int(load_lb):,} lb (>40,000 lb) with 35-44 mph wind -> Severe")

    return {
        "level": RISK_LEVELS[score],
        "score": score,
        "reasons": reasons if reasons else ["Clear / low-risk conditions"],
    }