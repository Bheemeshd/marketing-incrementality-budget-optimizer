"""Build the SQLite mart, analysis outputs, and a portable HTML report."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics import campaign_performance, incrementality, recommend_budget


def _fmt_money(value: float) -> str:
    return f"€{value:,.0f}"


def build(raw_dir: Path, processed_dir: Path, output_dir: Path) -> dict[str, float]:
    customers = pd.read_csv(raw_dir / "customers.csv")
    campaigns = pd.read_csv(raw_dir / "campaigns.csv")
    exposures = pd.read_csv(raw_dir / "exposures.csv")
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    database = processed_dir / "campaign_analytics.db"
    with sqlite3.connect(database) as connection:
        customers.to_sql("customers", connection, if_exists="replace", index=False)
        campaigns.to_sql("campaigns", connection, if_exists="replace", index=False)
        exposures.to_sql("exposures", connection, if_exists="replace", index=False)
        connection.executescript(Path("sql/schema.sql").read_text())

    performance = campaign_performance(exposures, campaigns)
    lift = incrementality(exposures, campaigns)
    allocation = recommend_budget(lift)
    performance.to_csv(processed_dir / "campaign_performance.csv", index=False)
    lift.to_csv(processed_dir / "campaign_incrementality.csv", index=False)
    allocation.to_csv(processed_dir / "budget_recommendation.csv", index=False)

    summary = {
        "campaigns": int(len(campaigns)),
        "customers": int(customers["customer_id"].nunique()),
        "media_spend": round(float(performance["spend"].sum()), 2),
        "observed_revenue": round(float(performance["revenue"].sum()), 2),
        "incremental_revenue": round(float(lift["incremental_revenue"].sum()), 2),
        "portfolio_incremental_roas": round(float(lift["incremental_revenue"].sum() / lift["spend"].sum()), 3),
        "positive_lift_campaigns": int((lift["ci95_low"] > 0).sum()),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    channel = lift.groupby("channel", as_index=False).agg(
        incremental_revenue=("incremental_revenue", "sum"), spend=("spend", "sum"), absolute_lift=("absolute_lift", "mean")
    )
    channel["incremental_roas"] = channel["incremental_revenue"] / channel["spend"]
    max_revenue = max(float(channel["incremental_revenue"].max()), 1.0)
    bars = "".join(
        f'<div class="bar-row"><span>{r.channel.replace("_", " ").title()}</span><div class="bar" style="width:{max(4, r.incremental_revenue/max_revenue*100):.1f}%"></div><b>{_fmt_money(r.incremental_revenue)}</b></div>'
        for r in channel.itertuples(index=False)
    )
    allocation_rows = "".join(
        f"<tr><td>{r.campaign_name}</td><td>{r.channel.replace('_', ' ').title()}</td><td>{_fmt_money(r.spend)}</td><td>{_fmt_money(r.recommended_budget)}</td><td>{r.incremental_roas:.2f}×</td></tr>"
        for r in allocation.head(8).itertuples(index=False)
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Campaign Measurement Executive View</title>
<style>body{{font-family:Inter,Arial;background:#f3f6fa;color:#102a43;margin:0}}main{{max-width:1120px;margin:auto;padding:40px}}h1{{margin-bottom:4px}}.sub{{color:#627d98}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card{{background:white;border-radius:12px;padding:20px;box-shadow:0 5px 20px #bcccdc55}}.label{{font-size:12px;text-transform:uppercase;color:#627d98}}.value{{font-size:28px;font-weight:700;margin-top:8px}}section{{background:white;padding:24px;border-radius:12px;margin:18px 0}}.bar-row{{display:grid;grid-template-columns:150px 1fr 100px;align-items:center;gap:14px;margin:14px 0}}.bar{{height:18px;background:linear-gradient(90deg,#0b7285,#38d9a9);border-radius:6px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #d9e2ec;text-align:left}}th{{font-size:12px;color:#627d98;text-transform:uppercase}}.note{{font-size:12px;color:#829ab1}}@media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}}}</style></head><body><main>
<h1>Omnichannel campaign measurement</h1><p class="sub">Executive decision view · synthetic randomized holdouts · generated reproducibly</p>
<div class="cards"><div class="card"><div class="label">Media spend</div><div class="value">{_fmt_money(summary['media_spend'])}</div></div><div class="card"><div class="label">Observed revenue</div><div class="value">{_fmt_money(summary['observed_revenue'])}</div></div><div class="card"><div class="label">Incremental revenue</div><div class="value">{_fmt_money(summary['incremental_revenue'])}</div></div><div class="card"><div class="label">Incremental ROAS</div><div class="value">{summary['portfolio_incremental_roas']:.2f}×</div></div></div>
<section><h2>Incremental revenue by channel</h2>{bars}<p class="note">Incrementality compares randomized treatment and holdout conversion rates. Synthetic results are illustrative.</p></section>
<section><h2>Budget reallocation scenario</h2><table><thead><tr><th>Campaign</th><th>Channel</th><th>Current spend</th><th>Scenario budget</th><th>iROAS</th></tr></thead><tbody>{allocation_rows}</tbody></table><p class="note">Transparent scenario constraints: 25% floor, 2× cap, fixed total portfolio budget. This is decision support, not a forecast guarantee.</p></section>
</main></body></html>"""
    (output_dir / "executive_dashboard.html").write_text(html)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    summary = build(args.raw_dir, args.processed_dir, args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

