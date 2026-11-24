"""Unit tests for the weather risk engine (api/services/risk.py).

Thresholds come from the assessment spec:
- Wind (mph): Low <25, Moderate 25-34, High 35-44, Severe 45-54, No Travel >=55
- Rain (in/hr): Low <0.10, Moderate 0.10-0.25, High 0.25-0.50, Severe 0.50-1.00, No Travel >1.00
- Snow (in/hr): Low <0.5, Moderate 0.5-1.0, High 1.0-2.0, Severe 2.0-3.0, No Travel >3.0
- Load rules: >=55 mph wind is No Travel for any load; 45-54 mph with a load
  over 30,000 lb is No Travel; 35-44 mph with a load over 40,000 lb is Severe.
  Boundaries are strict (exactly 30,000 / 40,000 lb does NOT trigger).

Run with: python manage.py test api
"""

from django.test import SimpleTestCase

from api.services.risk import classify_rain, classify_snow, classify_wind, evaluate_risk


class WindClassificationTests(SimpleTestCase):
    def test_low_below_25(self):
        self.assertEqual(classify_wind(0)[0], 0)
        self.assertEqual(classify_wind(24.9)[0], 0)

    def test_moderate_from_25(self):
        self.assertEqual(classify_wind(25)[0], 1)
        self.assertEqual(classify_wind(34.9)[0], 1)

    def test_high_from_35(self):
        self.assertEqual(classify_wind(35)[0], 2)
        self.assertEqual(classify_wind(44.9)[0], 2)

    def test_severe_from_45(self):
        self.assertEqual(classify_wind(45)[0], 3)
        self.assertEqual(classify_wind(54.9)[0], 3)

    def test_no_travel_from_55(self):
        self.assertEqual(classify_wind(55)[0], 4)
        self.assertEqual(classify_wind(80)[0], 4)


class RainClassificationTests(SimpleTestCase):
    def test_low_below_0_10(self):
        self.assertEqual(classify_rain(0)[0], 0)
        self.assertEqual(classify_rain(0.09)[0], 0)

    def test_moderate_from_0_10(self):
        self.assertEqual(classify_rain(0.10)[0], 1)
        self.assertEqual(classify_rain(0.24)[0], 1)

    def test_high_from_0_25(self):
        self.assertEqual(classify_rain(0.25)[0], 2)
        self.assertEqual(classify_rain(0.49)[0], 2)

    def test_severe_from_0_50(self):
        self.assertEqual(classify_rain(0.50)[0], 3)
        self.assertEqual(classify_rain(1.00)[0], 3)

    def test_no_travel_above_1_00(self):
        self.assertEqual(classify_rain(1.01)[0], 4)


class SnowClassificationTests(SimpleTestCase):
    def test_low_below_0_5(self):
        self.assertEqual(classify_snow(0)[0], 0)
        self.assertEqual(classify_snow(0.49)[0], 0)

    def test_moderate_from_0_5(self):
        self.assertEqual(classify_snow(0.5)[0], 1)
        self.assertEqual(classify_snow(0.99)[0], 1)

    def test_high_from_1_0(self):
        self.assertEqual(classify_snow(1.0)[0], 2)
        self.assertEqual(classify_snow(1.99)[0], 2)

    def test_severe_from_2_0(self):
        self.assertEqual(classify_snow(2.0)[0], 3)
        self.assertEqual(classify_snow(3.0)[0], 3)

    def test_no_travel_above_3_0(self):
        self.assertEqual(classify_snow(3.01)[0], 4)


class EvaluateRiskTests(SimpleTestCase):
    def test_clear_conditions_are_low(self):
        result = evaluate_risk(10, 0, 0, 35000)
        self.assertEqual(result["level"], "Low")
        self.assertEqual(result["score"], 0)
        self.assertIn("Clear / low-risk conditions", result["reasons"])

    def test_worst_factor_wins(self):
        self.assertEqual(evaluate_risk(30, 0, 0, 35000)["level"], "Moderate")
        self.assertEqual(evaluate_risk(0, 0.3, 0, 35000)["level"], "High")
        self.assertEqual(evaluate_risk(0, 0, 1.5, 35000)["level"], "High")
        # 50 mph alone is Severe, but only with a light load (<=30,000 lb):
        # with 35,000 lb the load rule upgrades it to No Travel.
        self.assertEqual(evaluate_risk(50, 0, 0, 20000)["level"], "Severe")
        self.assertEqual(evaluate_risk(60, 0, 0, 35000)["level"], "No Travel")

    def test_heavy_load_45_to_54_mph_is_no_travel(self):
        # Exactly 30,000 lb does NOT trigger; 30,001 lb does.
        self.assertEqual(evaluate_risk(50, 0, 0, 30000)["level"], "Severe")
        self.assertEqual(evaluate_risk(50, 0, 0, 30001)["level"], "No Travel")

    def test_heavy_load_35_to_44_mph_is_severe(self):
        # Exactly 40,000 lb does NOT trigger; 40,001 lb does.
        self.assertEqual(evaluate_risk(40, 0, 0, 40000)["level"], "High")
        self.assertEqual(evaluate_risk(40, 0, 0, 40001)["level"], "Severe")

    def test_55_mph_plus_is_no_travel_for_any_load(self):
        self.assertEqual(evaluate_risk(60, 0, 0, 1000)["level"], "No Travel")
        self.assertEqual(evaluate_risk(55, 0, 0, 1000)["level"], "No Travel")

    def test_reasons_mention_the_trigger(self):
        result = evaluate_risk(50, 0, 0, 40000)
        self.assertEqual(result["level"], "No Travel")
        self.assertTrue(any("30,000" in reason for reason in result["reasons"]))
