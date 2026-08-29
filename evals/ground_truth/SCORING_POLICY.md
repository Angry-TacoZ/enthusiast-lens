# Enthusiast Lens Evaluation Scoring Policy

## Primary metric: Correct Enthusiast Fact Coverage

For each benchmark fixture:

`fixture_coverage = correctly surfaced scorable facts / total scorable ground-truth facts`

A scorable `Unknown` is not a hallucinated error, but it does not count as a correctly surfaced fact.

## Aggregation rule

The primary reported score is **macro-averaged by the original 11 vehicle families**, not by raw fact count.

1. Calculate coverage independently for each fixture.
2. For the MINI family, average the true-positive and false-positive ACC subcases into one MINI family score.
3. Calculate the unweighted mean of the 11 vehicle-family scores.

This prevents:
- the Miata fixture, which has more verified facts, from dominating the overall result;
- the paired MINI ACC cases from giving MINI twice the weight of every other originally selected vehicle.

## Secondary metrics

Report both family-macro and raw micro totals where useful:
- accuracy of attempted facts;
- error rate;
- unknown rate;
- web/search calls per case;
- latency per case;
- estimated cost per case;
- provenance/source success.

The **headline comparison must use the 11-family macro coverage score**.
