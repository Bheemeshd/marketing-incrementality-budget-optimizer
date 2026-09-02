# Omnichannel Campaign Measurement & Budget Optimization

**Role simulated:** Marketing Data Analyst  
**Tools:** SQL, Python, pandas, SQLite, Streamlit, experiment measurement  
**Data:** 100% synthetic, seeded, and public-safe  
**Status:** Reproducible portfolio case study

## The 30-second story

Channel dashboards said marketing generated €334.9K of revenue from €257.9K spend. That attribution view could not answer the CFO’s real question: *how much demand would disappear without the campaigns?* I built randomized holdout measurement across 12 campaigns, estimated €118.4K of incremental revenue (0.46× incremental ROAS), quantified uncertainty, and translated the results into a fixed-budget reallocation scenario with visible guardrails.

## Context

Marketing, growth, and finance were using different definitions of success. Campaign managers prioritized observed ROAS; finance wanted incremental contribution; analysts needed a design that could survive review. I treated those definitions as a data-product problem rather than only a dashboard problem.

## My approach

1. Designed a synthetic customer/campaign model with heterogeneous baseline behavior.
2. Simulated independently randomized 80/20 treatment-control assignments.
3. Loaded the sources into SQLite and created reusable KPI and experiment views.
4. Calculated observed funnel metrics and treatment-control lift with 95% intervals.
5. Estimated incremental conversions, revenue, and ROAS.
6. Built an auditable allocation scenario that preserves total spend, retains a 25% floor, and limits campaigns to 2× prior spend.
7. Packaged the work in a Streamlit dashboard, portable executive view, tests, and CI.

## Key results

| Result | Value |
|---|---:|
| Campaigns measured | 12 |
| Synthetic assignments | 72,000 |
| Observed revenue | €334,901 |
| Estimated incremental revenue | €118,414 |
| Portfolio incremental ROAS | 0.46× |
| Positive 95% lift intervals | 10 / 12 campaigns |

The most important insight is not that marketing “failed.” It is that observed and incremental metrics answer different questions. The more conservative incremental view gives finance a comparable decision basis and tells marketing where better tests or creative changes are needed.

## Recommendation

Use incremental contribution as the portfolio decision metric, retain observed KPIs for operational diagnostics, and require holdouts for material campaigns. Treat the proposed allocation as a bounded planning scenario. Before changing production budgets, validate response curves and include gross margin, repeat purchases, and channel interactions.

## What I would improve with real data

- CUPED or regression adjustment using pre-period behavior
- cluster-robust inference and multiple-test governance
- contribution margin and return/cancellation adjustments
- longer conversion windows and cross-device identity
- geo experiments where user-level holdouts are infeasible
- saturation curves instead of assuming constant historical iROAS

## Interview prompts

- Why is attributed ROAS usually larger than incremental ROAS?
- What does a confidence interval crossing zero mean for a budget decision?
- Why did you impose allocation floors and caps?
- How would interference between customers or channels affect the estimate?

## Links to add after publishing

- GitHub repository: **[add URL]**
- Live dashboard/demo: **[add URL]**
- Portfolio home: **[add URL]**

