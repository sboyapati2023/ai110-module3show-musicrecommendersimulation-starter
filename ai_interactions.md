# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

I used Claude Code as an agent for two multi-step tasks.

### Task 1: Weight-shift experiment

**What task did you give the agent?**

Change the scoring weights to test how sensitive the rankings are, then prove the math still works.

**Prompts used:**

> "In recommender.py, halve the genre weights (exact 2.0→1.0, partial 1.0→0.5) and double the energy weight (1.0→2.0) without changing the other features. Then verify the math is still valid: MAX_SCORE matches the sum of each rule's maximum, a perfect song reaches MAX_SCORE, all scores stay in [0, MAX_SCORE], the explanation points sum to each score, and a hand-calculated score matches the code."

**What did the agent generate or change?**

- `src/recommender.py`: gave energy, valence and danceability their own weights (`FEATURE_WEIGHTS`), then set genre to 1.0 / 0.5 and energy to 2.0.
- Wrote a side-by-side script comparing the old and new top 5 for every profile.
- Wrote a check script that tested all 80 song scores.

**What did you verify or fix manually?**

- The top score stayed at 7.0, because genre lost 1 point and energy gained 1.
- I checked Storm Runner by hand: 1.0 + 1.0 + 2×0.99 + 0.87 + 0.89 + 0.90 = 6.64. It matched the code.
- I noticed the model card still described the old weights after the change, and had it updated.

---

### Task 2: Challenge 1, advanced song features

**What task did you give the agent?**

Add 5 or more new song attributes to the data, and make the scoring use them.

**Prompts used:**

> "Introduce 5 or more complex attributes to your dataset that are not currently present in the baseline data, such as Song Popularity (0-100), Release Decade, or Detailed Mood Tags (e.g., "nostalgic," "aggressive," "euphoric"). Update both data/songs.csv and the scoring logic in src/recommender.py so scoring accounts for the new attributes."

**What did the agent generate or change?**

It picked 5 features, each aimed at a weakness from my bias analysis:

| New column | Values | User setting | Points | Fixes |
|---|---|---|---|---|
| `popularity` | 0–100 | `target_popularity` | up to 0.5, closeness | Can ask for hits or deep cuts |
| `release_decade` | 1950–2020 | `favorite_decade` | up to 0.5; full for the same decade, 0 at 30+ years apart | Era was missing |
| `mood_tags` | 3 tags, like `uplifting;sunny;carefree` | `favorite_mood_tags` | up to 1.0, split across the user's tags | Mood was all-or-nothing (the Gym Hero problem) |
| `instrumentalness` | 0–1 | `target_instrumentalness` | up to 0.5, closeness | Study music vs. songs with vocals |
| `language` | english / spanish / instrumental | `preferred_language` | 0.5, exact match | Lyrics and language were missing |

- `data/songs.csv`: added the 5 columns for all 20 songs.
- `src/recommender.py`: loads the new columns, adds 5 new scoring rules (each one only counts if the user sets it), adds a small `_closeness()` helper, and adds `max_score(user_prefs)`, which gives each profile's best possible score.
- `src/main.py`: score bars now use each profile's own best score. Added 3 profiles that use the new features: Happy Pop + Mood Tags, 90s Nostalgia Deep Cuts, and Instrumental Study Session.
- The `Song` class got the new fields with default values, so the old tests still work.

**Results:**

- **Happy Pop + Mood Tags:** Gym Hero dropped from #3 to #4. Its tags ("driving," "aggressive") don't match "uplifting" or "sunny." Sol y Sombra, which has both tags, moved up to #3.
- **90s Nostalgia Deep Cuts:** Dusty Backroads (1990s, nostalgic, warm, wistful) won clearly.
- **Instrumental Study Session:** all 5 picks are instrumental, calm songs, led by Focus Flow.

**What did you verify or fix manually?**

- **No regressions.** The 4 original profiles gave exactly the same songs and scores as before. Their best score is still 7.
- **Why the per-profile max matters.** The full maximum went from 7 to 10. Without `max_score()`, old profiles would show bars out of 10, with points they could never earn. That would make every result look worse than it is.
- **Math checks on 140 scores** (7 profiles × 20 songs): every score is between 0 and that profile's max, the "why" points add up to each score, and a perfect song reaches the max.
- **Hand calculation.** Dusty Backroads for 90s Nostalgia: mood 1.0 + energy 2×0.92 + acoustic 0.64 + tags 1.0 + decade 0.5 + popularity 0.39 + language 0.5 = 5.87. It matched the code.
- **Edge cases.** The decade score fades correctly (10 years apart = 0.33 points, 30 years = 0). Tags typed as text ("Uplifting, SUNNY") score the same as a list.
- **The 2 existing tests pass.**
- **The data is made up.** Popularity, decades and tags were chosen by the agent to fit each song's genre and mood. They are believable, not real. I reviewed them to make sure they made sense (for example, the jazz song is from the 1960s and the synthwave song from the 1980s).
- **Remaining issue.** Gym Hero only dropped one spot. It still scores high on energy and danceability. Mood tags help, but they're worth only 1 point.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

The **Strategy pattern**, used for Challenge 2 (multiple scoring modes).

Each scoring mode is a strategy. The scoring code takes a strategy and uses it, without knowing which one it got. I built 4 modes:

| Mode | Idea | What changes |
|---|---|---|
| `balanced` | Default. Same results as before. | Energy 2, genre 1, mood 1 |
| `genre_first` | Stay in your favorite genre. | Genre 4, sound features 1 each |
| `mood_first` | Match the feeling, any genre. | Mood 3, mood tags 2, positivity 2, genre 0.5 |
| `energy_focused` | Match the intensity. | Energy 4, danceability 2, labels 0.5 |

**How did AI help you brainstorm or implement it?**

Prompt:

> "Build two or more different ranking strategies (e.g., "Genre-First," "Mood-First," or "Energy-Focused") so a user can switch between modes in main.py. Brainstorm a design pattern (like a simple "Strategy" pattern) that keeps the code modular."

The AI compared 3 options:

1. **`if mode == ...` inside `score_song`.** Fast to write. But every new mode means editing the scoring code, and the function keeps growing.
2. **One class per mode, each with its own `score()` method (classic Strategy).** Very flexible. But all my modes use the *same* 9 rules, just with *different weights*. So every class would repeat the same code.
3. **Strategy as data.** Each mode is a small `ScoringMode` object with a name, a description, and a weights table. One `score_song` function runs the rules using whatever mode it's given. A `MODES` dictionary lets `main.py` pick a mode by name.

We picked **option 3**. The key insight from the brainstorm: my modes differ in *how much* each rule counts, not in *what* the rules are. So the strategy only needs to hold the weights. If I ever need a mode with truly different logic, it can still become its own class.

The AI then refactored the code, added the command-line switch, and wrote a script to check the math in every mode.

**How does the pattern appear in your final code?**

- [`ScoringMode`](src/recommender.py): a small frozen dataclass. This is the strategy.
- `BALANCED`, `GENRE_FIRST`, `MOOD_FIRST`, `ENERGY_FOCUSED`: the 4 concrete strategies.
- `MODES`: a lookup table from name to mode. **Adding a mode = adding one entry here.**
- `get_mode()`: accepts a mode object, a name like `"genre_first"`, or nothing (gives the default). Unknown names give a clear error.
- `score_song(user_prefs, song, mode)` and `recommend_songs(..., mode)`: the "context" that uses whatever strategy it receives. The scoring rules never check which mode is active.
- `max_score(user_prefs, mode)`: the best possible score depends on the mode, so the score bars stay accurate.
- [`main.py`](src/main.py): switch modes with the `MODE` setting at the top, or from the command line:
  - `python3 -m src.main --mode genre_first`
  - `python3 -m src.main --compare` shows the top 5 of every mode side by side
  - `python3 -m src.main --list-modes`

**What I verified:**

- **No regressions.** `balanced` mode gives exactly the same scores as before the refactor, for all 7 profiles.
- **Math checks on 560 scores** (4 modes × 7 profiles × 20 songs): every score stays between 0 and the profile's max for that mode, and the "why" points add up to each score.
- **Hand calculation.** Storm Runner, Deep Intense Rock, `genre_first`: 4 + 1 + 0.99 + 0.87 + 0.89 + 0.90 = 8.65. It matched the code.
- **Bad input.** A typo like `--mode loud` is rejected with the list of valid modes.
- **The 2 existing tests pass.**

**What I noticed when comparing modes:**

- The #1 song is almost always the same in every mode. Modes mostly reshuffle places #2 to #5.
- `genre_first` pulls Gym Hero back up to #2 for happy-pop fans. It's pop, and genre now counts most.
- `mood_first` does *not* fix Gym Hero for the rock fan. Its "intense" mood label is worth even more in that mode. It also lets in a blues song (Rust and Whiskey) for the rock fan, just because it sounds dark.
- `energy_focused` is the only mode that changes a #1: Library Rain beats Focus Flow for Instrumental Study Session.
- Profiles with no favorite genre (90s Nostalgia, Instrumental Study) look almost the same in `balanced` and `genre_first`. That makes sense: there's no genre to put first.

---

## Diversity and Fairness Logic (Challenge 3)

**What task did you give the agent?**

Stop the top 5 from filling up with songs by the same artist or in the same genre.

**Prompt used:**

> "In recommender.py, add a diversity penalty to recommend_songs. Build the top-k list one song at a time instead of just sorting. Before each pick, lower every remaining song's score by 1.5 points for each song by the **same artist** already in the list, and by 0.75 points for each song of the **same genre** already in the list. Pick the highest adjusted score, and keep ties in their original order. Add a reason like 'diversity penalty: artist LoRoom already in list (−1.50)' so the penalty is visible. Make it optional (off by default), so earlier results stay reproducible, and add a switch in main.py. Then verify: with the penalty off, results are identical to before; with it on, no artist appears twice unless nothing else is close; and the 'why' points still add up to each score."

**How the rule works:**

1. Score every song as usual.
2. Pick the best song. Nothing is in the list yet, so #1 never gets a penalty.
3. For each next pick, subtract points from every remaining song:
   - **1.5 points** for each song by the same artist already picked.
   - **0.75 points** for each song in the same genre already picked.
   - Repeats add up: a third lofi song loses 1.5, not 0.75.
4. Pick the highest adjusted score. Repeat until there are 5 songs.

The artist penalty is bigger because two songs by one artist feel more repetitive than two songs in one genre. A lofi fan *wants* some lofi.

**What did the agent generate or change?**

- `src/recommender.py`:
  - `ARTIST_REPEAT_PENALTY = 1.5` and `GENRE_REPEAT_PENALTY = 0.75`, at the top so they're easy to change.
  - `diversity_penalty(song, picked)`: works out the penalty and the reason text.
  - `_pick_diverse()`: builds the list one pick at a time.
  - `recommend_songs(..., diverse=False)`: new option. Off by default.
- `src/main.py`: a `DIVERSE = False` setting at the top, and a `--diverse` flag. It works with every scoring mode and with `--compare`.

Usage: `python3 -m src.main --diverse` or `python3 -m src.main --diverse --mode genre_first`

**Results (balanced mode):**

| Profile | Before | After `--diverse` |
|---|---|---|
| Chill Lofi | 3 lofi songs, 2 by LoRoom | 2 lofi songs, 1 by LoRoom. Focus Flow drops out, Kitchen Window (folk) joins. |
| Instrumental Study Session | LoRoom at #1 and #2, 3 lofi songs | Midnight Coding drops out. Ambient, jazz and classical move up. |
| Happy Pop + Mood Tags | Gym Hero at #4 | **Gym Hero drops out.** It's the second pop song, so it loses 0.75. Paper Crowns (hip-hop) joins. |
| High-Energy Pop | Sunrise City at #2 | Sunrise City drops to #4 (second pop song). |
| Upbeat Pop, Deep Intense Rock, 90s Nostalgia | — | Unchanged. They were already varied enough. Gym Hero survives in Upbeat Pop by just 0.02 points. |

**What did you verify or fix manually?**

- **Off = unchanged.** With the penalty off, all 28 lists (4 modes × 7 profiles) match a plain sort exactly.
- **#1 never changes,** since nothing is in the list yet when it's picked.
- **The "why" points still add up,** now counting the minus lines too.
- **A penalty never raises a score.** No song is listed twice, and every list still has 5 songs.
- **Hand checks.** Chill Lofi: Midnight Coding after Library Rain = 6.46 − 0.75 = 5.71, which matches the code. Focus Flow as the 3rd pick = 1.5 (LoRoom once) + 2 × 0.75 (lofi twice) = 3.0 penalty, which also matches.
- **Variety went up.** Across all 28 diverse lists, only **1 repeated artist** is left. It's `genre_first` mode for Chill Lofi, where a lofi match is worth 4 points, so Focus Flow survives a 3.0 penalty. That's what a "stay in my genre" listener asked for, so I kept it.
- **The 2 existing tests pass.**

**Trade-offs I noticed:**

- **Fairness vs. accuracy.** A lofi fan now gets 2 lofi songs instead of 3. More variety means some "best fit" songs get pushed out. That's why I made it optional.
- **The penalty sizes are a judgment call.** 1.5 and 0.75 worked here. But with energy worth 2 points, a small penalty can be outweighed (Gym Hero in Upbeat Pop survived by 0.02).
- **Scores can't go below 0.** If a penalty is bigger than a song's score, it shows 0. The "why" points won't add up in that rare case.
- **It only looks at the current list.** It can't stop the *same* songs from showing up for every user. That's a bigger fairness problem (see the 5,000-listener test in the model card).

---

## Visual Summary Table (Challenge 4)

**What task did you give the agent?**

Make the terminal output easier to read with a table, and keep the reasons for each score visible.

**Prompt used:**

> "Suggest a way to show the top 5 recommendations in main.py as a readable terminal table, using tabulate or plain ASCII formatting. The table **must include the reasons for each score**, one reason per line inside the cell, next to rank, title, artist, genre/mood and score. Keep the current detailed view available, don't add a hard dependency (fall back to plain ASCII if tabulate isn't installed), and keep it under about 100 characters wide."

**What the AI suggested:**

- **Option A: `tabulate`.** Easy to use, and it handles cells with several lines well. But it's an extra library. It wasn't installed on my machine.
- **Option B: a small hand-made ASCII table.** No install needed, but more code to write.
- **Chosen: both.** The code uses `tabulate` if it's installed and falls back to the built-in table otherwise. So the project runs anywhere with nothing to install.

**What did the agent generate or change?**

- New file `src/table_view.py`:
  - `ascii_table()`: draws a boxed table with `┌─┬─┐` lines. Long text wraps inside its cell.
  - `make_table()`: uses `tabulate` (`fancy_grid` style) if available, otherwise `ascii_table()`.
  - `recommendations_table()`: one row per song with **#, Song / Artist, Genre / Mood, Score + mini bar, and Why**. Every reason gets its own line, including diversity penalties.
  - `summary_table()`: one row per profile with its #1 pick, score, % of a perfect score, and the rest of the top 5.
- `src/main.py`:
  - The table is now the **default view**, with a summary table at the end.
  - `--detailed` brings back the old long "card" view.
  - Works with `--mode`, `--diverse` and `--profile`.

Example row:

```
┌────┬─────────────────────┬──────────────┬─────────────┬──────────────────────────────────────────┐
│ #  │ Song / Artist       │ Genre / Mood │ Score       │ Why (reasons for the score)              │
├────┼─────────────────────┼──────────────┼─────────────┼──────────────────────────────────────────┤
│ 2  │ Rooftop Lights      │ indie pop    │ 7.48 / 8.50 │ • related genre: indie pop ~ pop (+0.50) │
│    │ Indigo Parade       │ happy        │ █████████░  │ • mood match: happy (+1.00)              │
│    │                     │              │             │ • energy 0.76 vs target 0.70 (+1.88)     │
```

**What did you verify or fix manually?**

- **Every reason is in the table.** A check script confirmed that each song's title, score and *every* reason appear in its table, for all 7 profiles, with the diversity penalty both on and off.
- **No ragged edges.** Every line of each table is the same width.
- **Width.** The first version was too wide. The score "6.83 / 7.00" wrapped onto two lines, and the summary table was 105 characters. I had the column widths adjusted. Now every view (default, `--diverse`, `--mode mood_first`, `--detailed`) is at most 100 characters wide.
- **A measuring mistake.** My first width check said 300 characters. That was counting *bytes*: each box-drawing character is 3 bytes. Counting characters gave the real width of 100.
- **Score bars can't break.** They stay 10 characters wide even for a 0 score, a negative score, or a max of 0.
- **The 2 existing tests pass.**

**Limits:**

- Long reasons like "produced/electronic sound, acousticness 0.18 (+0.82)" still wrap onto two lines. Shorter reason text would make the table tighter.
- The table is long: about 370 lines for all 7 profiles. Use `--profile "Chill Lofi"` to see just one, or read the summary table at the end.
- `tabulate` is optional, so it's not in `requirements.txt`. Install it with `pip install tabulate` to get its style instead.
