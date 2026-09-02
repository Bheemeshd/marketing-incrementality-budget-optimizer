# Methodology and analytical controls

## Measurement design

Each synthetic campaign randomly assigns approximately 80% of customers to treatment and 20% to holdout. The generator varies baseline conversion propensity by customer segment and treatment lift by both segment and channel. Random assignment is performed separately for each campaign.

The primary estimand is the difference in conversion rates:

`absolute lift = treatment conversions / treatment customers − control conversions / control customers`

Incremental conversions scale that difference to the treated population. Incremental revenue multiplies incremental conversions by the treated converters’ average order value; incremental ROAS divides this revenue by treatment media spend.

## Uncertainty

The pipeline reports a two-sided 95% normal-approximation interval for the difference in proportions. A campaign is tagged as having a positive interval when its lower bound is above zero. This is a communication aid, not a replacement for power analysis or multiple-testing controls.

## Budget scenario

The scenario preserves total historical spend, starts every campaign at 25% of its current spend, caps every campaign at 200%, and gives additional budget to positive lower-bound lift signals weighted by iROAS. The algorithm is intentionally simple enough for a stakeholder to audit.

## Quality controls

- One assignment per customer and campaign.
- Only treatment records carry media delivery and cost.
- Rates constrained to `[0, 1]` and spend to non-negative values.
- Allocation must preserve the total budget and respect campaign floors/caps.
- Seeded generation and automated unit tests run in CI.

## Production extensions

A real deployment would add identity resolution, consent controls, margin and returns, delayed outcomes, cluster-robust inference, pre-experiment covariate adjustment, sequential-test governance, saturation curves, channel interaction, and an approval workflow for allocation changes.

