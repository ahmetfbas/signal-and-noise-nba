What this metric tries to answer

Did a team perform better or worse than what game conditions suggested?

PvE is context-adjusted performance.

Not:

final score

win/loss

raw margin

But:

performance relative to expectation

High-level idea

For each team in a game:

PvE = Actual Margin − Expected Margin


So:

Positive PvE → outperformed conditions

Negative PvE → underperformed conditions

Step 1: Actual margin

Very simple:

actual_margin = team_points − opponent_points


Examples:

Win by 10 → +10

Lose by 6 → −6

No tricks here.

Step 2: Expected margin (the important part)

Expected margin is built from three components:

Recent form vs opponent strength

Home / Away adjustment

Fatigue adjustment

expected_margin =
    base_form_diff
  + home_away_adjustment
  + fatigue_adjustment

Step 3: Base form difference

This answers:

Ignoring venue and fatigue, how good is this team compared to the opponent lately?

3.1 Build recent form window

We look at the last 15 days, excluding today’s game.

Only completed games.

3.2 Adjust past margins by opponent strength

For each past game:

Take raw margin

Identify opponent

Look up opponent’s recent form

Apply scaling factor

factor = clamp((opponent_form + K) / K, 0.5, 1.5)
adjusted_margin = raw_margin × factor


Where:

K = 10


Meaning:

Beating strong teams counts more

Beating weak teams counts less

Blowouts are dampened

3.3 Average adjusted margins

For a team:

team_form = average(adjusted_margins)


Do this for both teams, then:

base_form_diff = team_form − opponent_form


This is the core expectation.

Step 4: Home / Away adjustment

Simple, fixed assumption:

HOME_ADVANTAGE = +2.0 points


So:

Home team → +2

Away team → −2

This is intentionally conservative.

Step 5: Fatigue adjustment

Fatigue reduces expected performance.

We normalize fatigue:

normalized_fatigue = min(fatigue_index / 100, 1)


Then apply:

fatigue_adjustment = − normalized_fatigue × 6


Meaning:

Fresh team → near 0 impact

Extremely fatigued → up to −6 points

Step 6: Final expected margin

Putting it together:

expected_margin =
    base_form_diff
  + home_away_adjustment
  + fatigue_adjustment


Rounded to 2 decimals.

Step 7: Compute PvE

Final calculation:

pve = actual_margin − expected_margin


Examples:

Actual	Expected	PvE	Meaning
+12	+6	+6	Strong overperformance
+4	+8	−4	Underperformed
−5	−2	−3	Worse than expected loss
Output fields produced

Per team, per game:

actual_margin

base_form_diff

home_away

fatigue_adj

expected_margin

pve

Mental model (important)

PvE isolates execution

It removes:

opponent strength

venue

fatigue

Wins can have negative PvE

Losses can have positive PvE

PvE answers:

“Given the situation, how well did you actually play?”