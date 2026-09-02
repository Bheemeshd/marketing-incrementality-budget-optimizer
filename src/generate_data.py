"""Generate a reproducible, synthetic omnichannel campaign experiment dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CHANNELS = ("paid_search", "paid_social", "email", "display")
CHANNEL_LIFT = {"paid_search": 0.014, "paid_social": 0.010, "email": 0.019, "display": 0.006}
CHANNEL_CPM = {"paid_search": 34.0, "paid_social": 18.0, "email": 2.5, "display": 9.0}


def generate(seed: int = 42, n_customers: int = 6_000, n_campaigns: int = 12) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    segments = np.array(["high_value", "growth", "occasional", "new"])
    segment = rng.choice(segments, n_customers, p=[0.15, 0.30, 0.35, 0.20])
    customers = pd.DataFrame(
        {
            "customer_id": [f"C{i:06d}" for i in range(1, n_customers + 1)],
            "segment": segment,
            "region": rng.choice(["north", "south", "east", "west"], n_customers),
            "is_mobile_first": rng.binomial(1, 0.61, n_customers),
            "prior_90d_orders": rng.poisson(np.select(
                [segment == "high_value", segment == "growth", segment == "occasional"],
                [4.6, 2.3, 0.9],
                default=0.25,
            )),
        }
    )

    campaign_rows = []
    start = pd.Timestamp("2025-01-06")
    for i in range(n_campaigns):
        channel = CHANNELS[i % len(CHANNELS)]
        campaign_rows.append(
            {
                "campaign_id": f"CMP{i + 1:03d}",
                "campaign_name": f"{channel.replace('_', ' ').title()} Wave {i // 4 + 1}",
                "channel": channel,
                "start_date": (start + pd.Timedelta(days=28 * (i // 4))).date().isoformat(),
                "end_date": (start + pd.Timedelta(days=28 * (i // 4) + 20)).date().isoformat(),
                "planned_budget": float(rng.integers(14_000, 32_000)),
                "holdout_share": 0.20,
            }
        )
    campaigns = pd.DataFrame(campaign_rows)

    frames: list[pd.DataFrame] = []
    segment_base = {"high_value": 0.085, "growth": 0.048, "occasional": 0.022, "new": 0.012}
    segment_lift = {"high_value": 0.004, "growth": 0.008, "occasional": 0.003, "new": 0.006}
    for campaign in campaigns.itertuples(index=False):
        assignment = rng.choice(["treatment", "control"], n_customers, p=[0.80, 0.20])
        treated = assignment == "treatment"
        impressions = np.where(treated, np.maximum(1, rng.poisson(3.2, n_customers)), 0)
        click_rate = {"paid_search": 0.075, "paid_social": 0.035, "email": 0.105, "display": 0.014}[campaign.channel]
        clicks = np.where(treated, rng.binomial(impressions, click_rate), 0)
        base_probability = np.array([segment_base[s] for s in segment])
        lift = np.array([segment_lift[s] for s in segment]) + CHANNEL_LIFT[campaign.channel]
        conversion_probability = np.clip(base_probability + treated * lift, 0, 0.4)
        converted = rng.binomial(1, conversion_probability)
        order_value = np.where(
            converted == 1,
            rng.gamma(shape=3.0, scale=np.select(
                [segment == "high_value", segment == "growth"], [48.0, 34.0], default=24.0,
            )),
            0.0,
        )
        media_cost = np.where(treated, impressions * CHANNEL_CPM[campaign.channel] / 1000.0, 0.0)
        if campaign.channel in {"paid_search", "paid_social"}:
            media_cost += np.where(treated, clicks * (1.25 if campaign.channel == "paid_search" else 0.72), 0.0)
        # Reconcile granular delivery cost to the campaign ledger so spend is
        # plausible relative to the planned budget while retaining row weights.
        target_spend = campaign.planned_budget * rng.uniform(0.88, 1.03)
        media_cost *= target_spend / max(float(media_cost.sum()), 1.0)

        frames.append(
            pd.DataFrame(
                {
                    "exposure_id": [f"{campaign.campaign_id}-E{i:06d}" for i in range(1, n_customers + 1)],
                    "campaign_id": campaign.campaign_id,
                    "customer_id": customers["customer_id"],
                    "assignment": assignment,
                    "impressions": impressions,
                    "clicks": clicks,
                    "converted": converted,
                    "order_value": np.round(order_value, 2),
                    "media_cost": np.round(media_cost, 4),
                }
            )
        )
    exposures = pd.concat(frames, ignore_index=True)
    return customers, campaigns, exposures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=6_000)
    parser.add_argument("--campaigns", type=int, default=12)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    customers, campaigns, exposures = generate(args.seed, args.customers, args.campaigns)
    customers.to_csv(args.output_dir / "customers.csv", index=False)
    campaigns.to_csv(args.output_dir / "campaigns.csv", index=False)
    exposures.to_csv(args.output_dir / "exposures.csv", index=False)
    print(f"Generated {len(customers):,} customers, {len(campaigns)} campaigns, and {len(exposures):,} assignments.")


if __name__ == "__main__":
    main()
