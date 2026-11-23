---
title: Wilson score interval
description: Why Benchtop Lab reports a success rate with a 95% Wilson interval and grades on its lower bound.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Wilson score interval

A success rate measured on a handful of episodes is an estimate, not a fact. The Wilson score interval says how
far the true rate could plausibly be from what you measured. Benchtop Lab reports it with every success rate and
grades on its lower bound.
{ .lead }

## The problem

You run a policy for 10 episodes and it succeeds 7 times. Is the policy "70% good"?

!!! question "Predict"

    Before reading on, write down the lowest true success rate you think is still consistent with seeing 7
    successes in 10 episodes.

Each episode either succeeds or fails, so the number of successes in $n$ independent episodes follows a binomial
distribution with an unknown true success rate $p$. The **point estimate** is the fraction you observed,
$\hat{p} = k / n$ for $k$ successes. A **confidence interval** is a range computed from the data that, over many
repetitions of the experiment, contains the true $p$ a stated fraction of the time (here 95%).

## The formula

For $k$ successes in $n$ episodes, with $\hat{p} = k/n$ and $z = 1.96$ for a 95% interval:

$$
\frac{\hat{p} + \dfrac{z^2}{2n}}{1 + \dfrac{z^2}{n}}
\;\pm\;
\frac{z}{1 + \dfrac{z^2}{n}} \sqrt{\frac{\hat{p}\,(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}
$$

The first term is the centre of the interval. It is pulled from $\hat{p}$ towards one half, strongly when $n$ is
small and hardly at all when $n$ is large. The second term is the half-width, which shrinks roughly as
$1/\sqrt{n}$.

## A worked example

The same 70% point estimate, measured on more and more episodes:

| Successes | Episodes | Point estimate | 95% Wilson interval | Lower bound |
| ---: | ---: | ---: | ---: | ---: |
| 7 | 10 | 0.70 | [0.40, 0.89]{ .interval } | 0.40 |
| 35 | 50 | 0.70 | [0.56, 0.81]{ .interval } | 0.56 |
| 70 | 100 | 0.70 | [0.60, 0.78]{ .interval } | 0.60 |
| 140 | 200 | 0.70 | [0.63, 0.76]{ .interval } | 0.63 |

Seven out of ten is consistent with a policy that fails more often than it succeeds. To claim "at least 60%"
with this method you need about 100 episodes at a 70% observed rate.

??? example "Explain: check the first row by hand"

    With $k = 7$, $n = 10$ and $z = 1.96$: $z^2 = 3.8416$, so $1 + z^2/n = 1.38416$.

    Centre: $(0.7 + 0.19208) / 1.38416 = 0.6445$.

    Half-width: $(1.96 / 1.38416) \times \sqrt{0.021 + 0.009604} = 1.4160 \times 0.17494 = 0.2477$.

    Interval: $0.6445 \pm 0.2477$, which is $[0.397,\ 0.892]$.

## Why not the textbook interval?

The interval most courses teach first, $\hat{p} \pm z\sqrt{\hat{p}(1-\hat{p})/n}$ (the Wald interval), breaks in
exactly the situations robot evaluation produces: few episodes and success rates near 0 or 1.

| Result | Wald interval | Wilson interval |
| --- | ---: | ---: |
| 10 of 10 | [1.00, 1.00]{ .interval } | [0.72, 1.00]{ .interval } |
| 0 of 10 | [0.00, 0.00]{ .interval } | [0.00, 0.28]{ .interval } |
| 7 of 10 | [0.42, 0.98]{ .interval } | [0.40, 0.89]{ .interval } |

Ten successes out of ten do not prove a policy never fails, yet the Wald interval has zero width there. The
Wilson interval stays inside 0 to 1 and keeps a sensible width at the extremes.

## How Benchtop Lab uses it

- Every success rate in a report card is shown with its 95% Wilson interval.
- Grade thresholds are compared with the **lower bound**, so more evaluation episodes can only help a policy
  that deserves the grade ([ADR-006](../DECISIONS.md#adr-006-thresholds-use-the-wilson-95-lower-bound-and-are-calibrated-from-measurements)).
- LeRobot's own evaluation reports the same interval, so numbers from the two tools are comparable.

## Limits to keep in mind

The interval assumes episodes are independent and drawn from the conditions you care about. It says nothing
about scenes the evaluation never sampled, which is why the grader also runs held-out seeds and perturbation
suites.
