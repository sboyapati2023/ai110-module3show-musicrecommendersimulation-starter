# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Goal / Task

VibeMatch suggests songs a listener will probably like.

The listener describes their taste. The system scores every song in the catalog. It returns the top 5 songs, best first.

Each song comes with a short list of reasons. So you can always see *why* it was picked.

---

## 3. Data Used

- **Size:** 20 made-up songs in `data/songs.csv`. I did not add or remove any.
- **Features:** genre, mood, energy, positivity (valence), danceability, acousticness, and tempo. All number features go from 0 to 1, except tempo.
- **Not used:** tempo and artist. Tempo mostly repeats energy.

**Limits:**

- 17 genres for 20 songs. Most genres have just 1 song. Only lofi (3) and pop (2) have more.
- 16 moods. Only "chill," "happy," and "intense" appear more than once.
- Nothing is quieter than energy 0.20. So there is no real sleep or meditation music.
- Acoustic songs are always quiet. Electronic songs are always loud. There are no loud acoustic songs and no quiet electronic songs.
- No lyrics, language, decade, or popularity.

---

## 4. Algorithm Summary

Think of a judge with a scorecard. The judge checks each song against what the listener asked for and adds up points. The best possible score is 7.

| Rule | Points |
|---|---|
| Genre matches exactly | 1 |
| Genre is a close relative (like "indie pop" for a pop fan) | 0.5 |
| Mood matches exactly | 1 |
| Energy is close to what the listener wants | up to 2 |
| Positivity is close | up to 1 |
| Danceability is close | up to 1 |
| Sound fits (acoustic for acoustic fans, electronic for everyone else) | up to 1 |

**"Close" is the key idea.** If you ask for medium energy, a medium song scores high. A very loud song scores lower, even though it has "more" energy.

**Energy counts the most.** At first, genre was worth 2 and energy 1. Genre labels were deciding too much. So I swapped them (see Evaluation).

**Sound matters more than labels.** Labels are worth 2 points. Sound is worth 5. A song with the right label but the wrong sound can lose.

---

## 5. Observed Behavior / Biases

**Main bias: calm music gets counted twice.**

In this catalog, energy and acousticness measure almost the same thing. Acoustic songs are quiet. Electronic songs are loud. So a fan of calm, acoustic music gets up to 3 points from one quality. Their lists look great.

But a fan of *loud* acoustic music (like folk-rock) asks for something that doesn't exist here. Their best match only reaches 72% of the top score. The system quietly hands them a slow folk song instead. And `likes_acoustic` is just yes or no, so nobody can ask for "somewhere in between."

**Other patterns I saw:**

- **Gym Hero shows up everywhere.** This pop workout song made 3 of the 4 lists. It's close on almost every number, so it fits many people "pretty well."
- **Middle-of-the-road songs win more.** I simulated 5,000 random listeners. Kitchen Window made 38% of their top-5 lists. Neon Cathedral made only 13%. A fair share is 25%.
- **Labels are all-or-nothing.** "Metal" is no closer to "rock" than jazz is. "Angry" is no closer to "intense" than "chill" is.
- **Small genres lose out.** A lofi fan gets 3 matching songs. A jazz fan gets 1, then random-ish picks.
- **Mistakes fail silently.** A mood typo is ignored. Typing "False" as text counts as *yes*. Asking for −1 songs returns 19. Nothing crashes, so it's easy to miss.
- **Filter bubble.** The same profile always gets the same 5 songs. Nothing stops one artist from filling the list.

---

## 6. Evaluation Process

### Profiles I tested

**4 everyday listeners:**

- **Upbeat Pop:** happy pop, fairly lively, electronic.
- **High-Energy Pop:** intense pop for workouts.
- **Chill Lofi:** calm, acoustic study music.
- **Deep Intense Rock:** loud, dark rock.

**Tricky profiles,** built to fool the system:

- A sad mood with very high energy.
- A genre that isn't in the catalog (k-pop, punk).
- A one-letter genre ("r").
- A typo in the mood ("happpy").
- Numbers outside 0 to 1.
- An empty profile.
- Settings typed as text instead of numbers or yes/no.

### What I checked

- Would a real listener like this top 5?
- Does the #1 song make sense?
- Do the points in each "why" list add up to the score?

### What worked

- Every everyday profile got the obvious best song at #1 (6.6 to 6.9 out of 7).
- Chill Lofi was the best list. All 3 lofi songs came first, then calm acoustic songs.

### What surprised me

- Gym Hero ranked #2 for the rock fan. Its "intense" label beat a metal song that actually sounds closer.
- By sound alone, that metal song (Ashfall Requiem) fits the rock fan *better* than the #1 song. The #1 song only wins because of its labels.
- The one-letter genre "r" gave points to rock, r&b, and reggae.

### Experiment: weight shift

I halved genre (2 → 1) and doubled energy (1 → 2). The top score stayed at 7.

- No #1 song changed. 4 of 20 top-5 spots did.
- **Better:** For Upbeat Pop, the happy song Rooftop Lights moved above Gym Hero. Sol y Sombra joined the list.
- **Worse:** For Deep Intense Rock, a cheerful EDM song joined at #5 just for being loud.
- I checked the math on all 80 scores. Every score stayed between 0 and 7. A hand calculation matched the code.

### Comparing profiles side by side

| Profile | #1 | #2 | #3 | #4 | #5 |
|---|---|---|---|---|---|
| Upbeat Pop | Sunrise City | Rooftop Lights | Gym Hero | Paper Crowns | Sol y Sombra |
| High-Energy Pop | Gym Hero | Sunrise City | Storm Runner | Rooftop Lights | Neon Cathedral |
| Chill Lofi | Library Rain | Midnight Coding | Focus Flow | Spacewalk Thoughts | Coffee Shop Stories |
| Deep Intense Rock | Storm Runner | Gym Hero | Ashfall Requiem | Night Drive Loop | Neon Cathedral |

**Upbeat Pop vs. High-Energy Pop.** Same two pop songs on top, but swapped. The happy fan gets the "happy" song first. The workout fan gets the louder "intense" song first. The workout list also adds a loud rock song. Makes sense: only mood and energy changed.

**Why does Gym Hero show up for someone who wants Happy Pop?** Picture a checklist with six boxes. Gym Hero is pop. It sounds cheerful. It's very danceable. It's electronic. Its energy is a bit high, but close enough. That's five boxes. It only misses one: its mood label says "intense," not "happy." A person can hear that a workout song feels different. The system only sees a song that's close on almost every number. So it lands at #3. The math is right. The numbers just can't tell "pumped up" from "happy."

**Upbeat Pop vs. Chill Lofi.** No songs in common. One wants loud and electronic. The other wants quiet and acoustic. Makes sense: they come from opposite ends of the catalog.

**Upbeat Pop vs. Deep Intense Rock.** Both want loud, electronic music, so both lists are loud. The difference is positivity. The pop fan gets bright songs. The rock fan gets dark ones, like an angry metal song. Makes sense: positivity separates party music from heavy music.

**High-Energy Pop vs. Chill Lofi.** Total opposites. Every pop pick has energy 0.76 or more. Every lofi pick has 0.42 or less. Makes sense: energy is the biggest factor, so nothing else can pull these lists together.

**High-Energy Pop vs. Deep Intense Rock.** The most alike: both want intense, loud music. They share 3 songs. #1 goes to whichever song matches the genre. The pop fan also gets bright, danceable songs. The rock fan gets the dark metal song. One miss: a cheerful EDM song shows up for the rock fan just for being loud.

**Chill Lofi vs. Deep Intense Rock.** No songs in common. They disagree on energy, sound, and positivity all at once. Makes sense: the system really does separate very different listeners.

---

## 7. Intended Use and Non-Intended Use

**Designed for:**

- Classroom learning about how recommenders work.
- Trying out scoring rules and seeing how rankings change.
- Finding bias and edge cases in a simple system.

**Not meant for:**

- Real listeners or a real music app. The catalog is tiny and made up.
- Learning someone's taste over time. It can't see what you play or skip.
- Any decision that matters. It doesn't check its input, so mistakes slip through quietly.
- Listeners whose taste doesn't fit the catalog, like fans of loud acoustic music or genres it doesn't have.

---

## 8. Ideas for Improvement

1. **Partial credit for related genres and moods.** For example, metal is 70% like rock, and "angry" is 70% like "intense." That would fix the Gym Hero problem.
2. **Let listeners pick an acoustic level from 0 to 1, not just yes or no.** That stops calm music from being counted twice.
3. **More variety and input checks.** Allow at most one song per artist, add one "discovery" slot, and warn about typos and bad values.

---

## 9. Personal Reflection

*Draft: edit this section into your own words before submitting.*

**Biggest learning moment**

It came when I broke down the rock fan's #1 song, Storm Runner. I added up only the "sound" points. A metal song, Ashfall Requiem, actually fit better. Storm Runner won only because its labels said "rock" and "intense." That's when I saw that my weights weren't neutral. Every number I picked decided whose taste wins. Later I found that energy and acousticness were basically the same thing in my data. So calm-music fans got points twice. Nothing looked broken. The bias was hiding in plain sight.

**How AI tools helped, and when I double-checked**

AI helped me move fast. It suggested tricky test profiles I wouldn't have thought of, like typing "False" as text. It wrote quick scripts to run them. It also ran a 5,000-listener simulation that showed which songs get recommended too often. I could never have counted that by hand.

But I had to double-check it often:

- **Numbers.** I only trusted a claim after seeing it in real output. I checked one score by hand (Storm Runner = 6.64), and it matched the code.
- **Examples that didn't fit my data.** The assignment's example bias was "too much pop." But my catalog has 17 genres in 20 songs. Pop isn't the problem. I had to find the real bias myself.
- **Docs drifting from code.** After I changed the weights, my model card still described the old ones. I had to catch that and fix it.
- **Taste.** AI can't hear music. When it said a list "felt right," that was a guess from the numbers. I had to judge that part myself.
- **Wording.** One draft said Gym Hero's energy was "only a little higher" than the target. It was 0.23 higher. Small words can hide real gaps.

**How simple algorithms still "feel" like recommendations**

My system is just addition. No learning, no data about real people. But the lists still felt smart. The Chill Lofi list looked like a playlist I'd actually save. I think the "why" list does a lot of the work. Reading "energy 0.35 vs target 0.35" makes a pick feel thought-through. That also made me a little uneasy. When Gym Hero showed up for a happy-pop fan, the reasons still sounded convincing. A confident explanation can make a weak pick seem right. Real apps probably feel smart for some of the same reasons.

**What I'd try next**

- A "similar genres and moods" table, so metal gets partial credit for rock fans.
- An acoustic level from 0 to 1, so calm music stops counting twice.
- One "discovery" slot in every top 5, to break the filter bubble.
- Re-running the 5,000-listener test after each change, to check whether it really got fairer.
