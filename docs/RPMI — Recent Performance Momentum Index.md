What this metric tries to answer

Is a team’s performance trend improving or deteriorating right now?

RPMI is momentum, not level.

PvE → how well you played

RPMI → where you are heading

Core idea

RPMI looks only at recent PvE values and answers:

Are recent games better than older ones, and how stable is that trend?

Step 1: Define the window

We use the last 5 games for each team.

WINDOW = 5


Why 5?

Short enough to react

Long enough to avoid single-game noise

Step 2: Weight recent games more

PvE values are weighted, giving more importance to the most recent games.

Weights:

[1, 2, 3, 4, 5]


So:

Oldest game → weight 1

Most recent game → weight 5

Weighted PvE:

weighted_pve = sum(pve_i × weight_i) / sum(weights)


This ensures:

Momentum reacts faster to recent changes

One bad old game doesn’t dominate

Step 3: Penalize inconsistency

Raw momentum can be misleading if performance is erratic.

So we compute volatility inside the window:

std = standard_deviation(pve_window)


Then derive a consistency factor:

consistency_factor = 1 / (1 + std / 10)


Meaning:

Stable performance → factor close to 1

Wild swings → factor shrinks RPMI

This prevents:

Fake momentum caused by one outlier game

Step 4: Compute RPMI

Final formula:

rpmi = weighted_pve × consistency_factor


Rounded to 2 decimals.

Step 5: RPMI delta (optional but useful)

We also track change vs previous game:

rpmi_delta = rpmi_today − rpmi_previous


This helps detect:

acceleration

deceleration

momentum reversals

Step 6: RPMI interpretation (labels)

RPMI is directional, not bounded.

Typical labels:

RPMI value	Interpretation
≥ +15	Strong positive momentum
+5 to +15	Improving
−5 to +5	Neutral
−15 to −5	Slipping
≤ −15	Strong negative momentum

(Labels are descriptive, not used in math.)

Output fields produced

Per team, per game:

rpmi

rpmi_delta

rpmi_label

Mental model (important)

RPMI ≠ strength

RPMI ≠ quality

RPMI = direction

Examples:

Strong team playing worse → negative RPMI

Weak team improving → positive RPMI

RPMI answers:

“Are things getting better or worse right now?”