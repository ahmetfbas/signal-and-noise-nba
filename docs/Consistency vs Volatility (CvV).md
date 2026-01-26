What this metric tries to answer

How predictable is a team’s performance right now?

CvV is not about how good a team is.
It is about how stable the performance signal is.

Core idea

Two teams can have the same average PvE:

Team A: +8, +7, +9, +8, +7 → predictable

Team B: +25, −10, +18, −5, +12 → chaotic

CvV separates these.

Step 1: Define the window

We use the last 5 PvE values, same as RPMI.

WINDOW = 5


Reason:

Same temporal sensitivity

CvV and RPMI stay aligned in interpretation

Step 2: Compute raw volatility

Volatility is simply:

pve_volatility = standard_deviation(pve_window)


Unit: points

Higher = more noise

Lower = more control

This is raw, not yet normalized.

Step 3: Normalize volatility

To prevent scale issues, we normalize:

normalized_vol = pve_volatility / 10


Why 10?

Typical PvE standard deviation in NBA ranges ~5–25

This keeps values in a usable range

Step 4: Convert volatility into consistency

Consistency is the inverse of volatility:

consistency = 1 / (1 + normalized_vol)


Properties:

Bounded between 0 and 1

Monotonic

Interpretable

Examples:

Very stable → ~0.7–0.8

Average → ~0.45–0.55

Very noisy → ~0.25–0.35

Step 5: Track games played

For each team:

games_played = index + 1


Why this matters:

Early values are statistically unreliable

We need maturity awareness

Step 6: Consistency labels

Labels depend on both consistency and maturity.

Logic:

If no data → Insufficient

If games_played < 10 → Forming

Else:

Consistency	Label
≥ 0.65	Very Consistent
≥ 0.50	Consistent
≥ 0.35	Volatile
< 0.35	Very Volatile
Output fields produced

Per team, per game:

pve_volatility

consistency

games_played

consistency_label

Mental model

Volatility = noise amplitude

Consistency = signal reliability

High consistency means:

PvE is meaningful

Momentum signals can be trusted

Low consistency means:

Expect surprises

Trend-based conclusions are fragile