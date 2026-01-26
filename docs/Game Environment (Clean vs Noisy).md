What this metric tries to answer

How reliable is this game as a signal environment?

This is game-level, not team-level.

It answers:

Can we trust performance-based expectations here?

Or is this game dominated by noise, instability, and mismatch?

Core idea

A game becomes noisy when:

Teams are tired

Performances are volatile

Conditions between teams are asymmetric

A game becomes clean when:

Fatigue is low

Teams behave predictably

Conditions are balanced

Important concept: maturity

Before anything else, we ask:

Do we even have enough data to judge this game?

Maturity rule
MIN_GAMES_FOR_MATURE = 10


If either team has played fewer than 10 games:

Environment = Forming

No further judgment

This avoids false confidence early in the season.

Step 1: Normalize components to 0–1 risk

All components are mapped into a risk scale.

1️⃣ Fatigue risk

Input:

fatigue_index (roughly 0–120)

Mapping:

fatigue_risk = clip((fatigue_index - 30) / 50)


Interpretation:

~30 → low risk

~80+ → high risk

2️⃣ Volatility risk

Input:

pve_volatility (points)

Mapping:

volatility_risk = clip((volatility - 8) / 12)


Interpretation:

~8 → calm

~20 → very unstable

3️⃣ Asymmetry risks

Asymmetry captures mismatch, not absolute strength.

Fatigue asymmetry
abs(fatigue_home - fatigue_away) / 40

Consistency asymmetry
abs(consistency_home - consistency_away) / 0.30


These are then averaged into one asymmetry score.

Step 2: Aggregate team risks

For the game:

Average fatigue risk (home + away)

Average volatility risk (home + away)

Asymmetry risk (fatigue + consistency mismatch)

Missing values are handled safely.

Step 3: Composite noise score

Final noise score is a weighted average:

noise_score =
  0.45 * fatigue_risk_avg +
  0.35 * volatility_risk_avg +
  0.20 * asymmetry_risk


Why these weights?

Fatigue directly impacts execution → highest weight

Volatility impacts predictability → second

Asymmetry amplifies fragility → third

Step 4: Environment classification

Using thresholds:

CLEAN_THR = 0.33
NOISY_THR = 0.67


Rules:

If not mature → Forming

If noise_score ≤ 0.33 → Clean

If noise_score ≥ 0.67 → Noisy

Else → Mixed

Step 5: Drivers (explainability)

Each game gets a human-readable explanation:

Possible drivers:

high fatigue load

high volatility

asymmetry (conditions mismatch)

early-season/low-history

stable conditions

This makes the model interpretable, not black-box.

Output fields produced

Per game:

noise_score

environment_label (Clean / Mixed / Noisy / Forming)

drivers

Diagnostic fields:

fatigue home/away

volatility home/away

asymmetry score

maturity flags

Mental model

Clean game → signal dominates noise

Noisy game → noise dominates signal

Mixed → partial trust

Forming → do not conclude yet

This metric is the context lens for everything else:

PvE interpretation

RPMI confidence

Narrative quality