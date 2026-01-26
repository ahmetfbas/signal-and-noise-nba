What this metric tries to answer

How physically and mentally stressed is a team going into this game?

This is not performance.
It is risk / load.

High fatigue = execution risk, slower reactions, higher variance.

Inputs used

Fatigue is built from four simple ideas:

Schedule density (how often they played recently)

Days since last game (rest / recovery)

Back-to-back penalty

Travel load (optional, neutral for now)

Step 1: Count recent games

For each team, before a game:

games_last_7 → number of games played in last 7 days

games_last_14 → number of games played in last 14 days

This is just counting appearances in the raw game data.

Step 2: Convert counts into density scores

We do not use raw counts directly.
We map them into stress levels.

7-day density score
≤ 2 games → 10
3 games   → 40
4 games   → 75
5+ games  → 95

14-day density score
≤ 4 games → 10
5 games   → 35
6 games   → 55
7 games   → 75
8+ games  → 95

Step 3: Combine density into one number

We weight recent congestion more:

density_score =
    0.65 * density_7d_score
  + 0.35 * density_14d_score


This reflects:

Last week matters more than two weeks ago

Long stretches still matter, but less

Step 4: Days since last game (recovery)

We compute:

days_since_last_game = today - last_game_date


Then apply a recovery offset:

1 day  → 0.00   (no recovery)
2 days → 0.10
3 days → 0.25
4 days → 0.40
5+     → 0.55


This is a dampener, not a reset.

Step 5: Back-to-back logic

If:

days_since_last_game == 1


Then:

b2b = True

Adds extra load, even if density is already high

Step 6: Travel load (currently neutral)

Travel is bucketed as:

< 300 miles → 1
300–800     → 2
800+        → 3


For now, if travel is unknown:

travel_load = 1


This avoids introducing noise early.

Step 7: Raw fatigue score

We combine everything:

raw =
    density_score
  + (12 if back_to_back)
  + (travel_load * 6)
  + (10 if back_to_back AND travel_load ≥ 2)


This creates spikes when stressors collide.

Step 8: Apply recovery dampening

Final fatigue index:

fatigue_index =
    raw * (1 - recovery_offset)


Rounded to one decimal.

Important:

Recovery reduces fatigue

It never fully resets it

Step 9: Fatigue tiers (for interpretation only)
< 30  → Low
30–49 → Elevated
50–69 → High
70+   → Critical


These are labels, not used in calculations.

Output fields produced

For each team & game:

games_last_7

games_last_14

density_score

days_since_last_game

travel_miles

travel_load

recovery_offset

fatigue_index

fatigue_tier

Mental model (important)

Fatigue is stacking, not additive

Back-to-backs matter more when already dense

Recovery softens, never erases

This metric does not predict score

It predicts execution risk