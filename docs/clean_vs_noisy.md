Clean vs Noisy Game Classification
1. Purpose

The Clean vs Noisy classifier describes the predictability of a game’s environment, not the quality of teams or the expected winner.

It answers one question:

Are the conditions surrounding this game stable enough for performance signals to be trusted, or are they dominated by instability and randomness?

This classification is designed for context and interpretation, not prediction.

2. What the Classifier Measures

Each game is evaluated using team-level, pre-game signals from both sides:

Fatigue load (execution risk)

Recent performance volatility (unpredictability)

Asymmetry between teams (mismatch in conditions)

Data maturity (enough historical signal or not)

Only information available before the game is used.

3. Inputs Used

For each game (home + away teams):

Core Inputs

fatigue_index

pve_volatility

consistency

games_played

Derived Signals

Average fatigue risk (home + away)

Average volatility risk (home + away)

Asymmetry score (fatigue mismatch + consistency mismatch)

Maturity flag (both teams have sufficient history)

If a signal is missing or immature, it is excluded from the calculation.

4. Normalization Philosophy

All components are normalized into a 0–1 risk scale.

This allows different dimensions (fatigue points, volatility in points, consistency ratios) to be combined meaningfully.

Normalization reflects relative risk, not absolute thresholds.

Examples:

Low fatigue → near 0

High fatigue → near 1

Calm recent performance → near 0

Highly volatile recent performance → near 1

5. Composite Noise Score

The final noise_score is a weighted average of three components:

Component	Weight	Interpretation
Fatigue risk	0.45	Execution degradation
Volatility risk	0.35	Unpredictability
Asymmetry risk	0.20	Fragility from mismatch

Fatigue is weighted highest because it directly affects execution quality.
Volatility reflects recent instability.
Asymmetry captures uneven conditions that increase randomness.

6. Maturity Rule

If either team has played fewer than 10 games, the environment is labeled:

Forming

This prevents early-season or low-sample noise from being misclassified as meaningful structure.

7. Environment Labels
Clean

Low fatigue

Low volatility

Symmetric conditions

Mature data

Interpretation:

Outcomes are more likely to reflect underlying team quality and structure.

Mixed

Some instability present

Signals partially reliable

Interpretation:

Context matters; signals should be interpreted cautiously.

Noisy

High fatigue, volatility, or asymmetry

Execution and randomness dominate

Interpretation:

Outcomes are heavily influenced by unstable conditions rather than form.

Forming

Insufficient historical data

Interpretation:

Signals exist but are not yet reliable.

8. What This Classifier Is NOT

This system is not:

A win probability

A betting signal

A team strength ranking

A player evaluation tool

It is strictly a game-environment descriptor.

9. Intended Use

The Clean vs Noisy classification is intended to:

Add context to pre-game analysis

Explain why certain games behave unexpectedly

Separate structural outcomes from chaotic ones

Support narrative interpretation of metrics

10. Design Principle

The classifier describes the environment, not the result.

If the code changes, this document must be updated first.