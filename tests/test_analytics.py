import unittest

import pandas as pd

from src.analytics import campaign_performance, incrementality, recommend_budget
from src.generate_data import generate


class CampaignAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.customers, cls.campaigns, cls.exposures = generate(seed=9, n_customers=1_000, n_campaigns=8)

    def test_generator_integrity(self):
        self.assertEqual(len(self.exposures), len(self.customers) * len(self.campaigns))
        self.assertTrue(set(self.exposures["assignment"]).issubset({"treatment", "control"}))
        self.assertTrue((self.exposures["media_cost"] >= 0).all())
        self.assertFalse(self.exposures[["campaign_id", "customer_id"]].duplicated().any())

    def test_performance_rates_are_valid(self):
        result = campaign_performance(self.exposures, self.campaigns)
        self.assertTrue(result["ctr"].between(0, 1).all())
        self.assertTrue(result["conversion_rate"].between(0, 1).all())
        self.assertTrue((result["spend"] > 0).all())

    def test_incrementality_has_one_row_per_campaign(self):
        result = incrementality(self.exposures, self.campaigns)
        self.assertEqual(len(result), len(self.campaigns))
        self.assertTrue((result["ci95_low"] <= result["ci95_high"]).all())

    def test_budget_is_preserved_and_capped(self):
        lift = incrementality(self.exposures, self.campaigns)
        budget = float(lift["spend"].sum())
        result = recommend_budget(lift, budget)
        self.assertAlmostEqual(float(result["recommended_budget"].sum()), budget, places=4)
        self.assertTrue((result["recommended_budget"] <= result["spend"] * 2 + 1e-6).all())
        self.assertTrue((result["recommended_budget"] >= result["spend"] * 0.25 - 1e-6).all())


if __name__ == "__main__":
    unittest.main()

