import csv
from collections import Counter
from typing import List, Dict, Tuple, Union
from dataclasses import dataclass, field

# CSV columns that must be converted from text to numbers when loading.
INT_FIELDS = ("id", "popularity", "release_decade")
FLOAT_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness")
LIST_FIELDS = ("mood_tags",)  # stored as "tag1;tag2;tag3" in the CSV

NUMERIC_FEATURES = ("energy", "valence", "danceability")
DECADE_RANGE_YEARS = 30  # decade points fade to 0 when the song is this many years away

# Diversity penalty (Challenge 3): points taken off a candidate for EACH song by the
# same artist / in the same genre that is already in the top list. Repeats add up.
ARTIST_REPEAT_PENALTY = 1.5
GENRE_REPEAT_PENALTY = 0.75


# ---------------------------------------------------------------------------
# Scoring modes (Strategy pattern)
#
# Every mode runs the SAME scoring rules; a mode is just a named set of weights
# saying how many points each rule is worth. score_song() receives a mode and
# never needs to know which one it is, so adding a mode = adding one entry to MODES.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScoringMode:
    """One ranking strategy: a name, a short description, and the max points per rule."""
    name: str
    description: str
    weights: Dict[str, float] = field(default_factory=dict)

    def weight(self, rule: str) -> float:
        return self.weights.get(rule, 0.0)


# Rule names used in the weights:
#   genre, genre_partial, mood, energy, valence, danceability, acoustic,
#   mood_tags, popularity, decade, instrumentalness, language
BALANCED = ScoringMode(
    "balanced",
    "Default. Energy counts most; genre and mood are small bonuses.",
    {"genre": 1.0, "genre_partial": 0.5, "mood": 1.0,
     "energy": 2.0, "valence": 1.0, "danceability": 1.0, "acoustic": 1.0,
     "mood_tags": 1.0, "popularity": 0.5, "decade": 0.5, "instrumentalness": 0.5, "language": 0.5},
)
GENRE_FIRST = ScoringMode(
    "genre_first",
    "Stay in your favorite genre; sound only breaks ties within it.",
    {"genre": 4.0, "genre_partial": 2.0, "mood": 1.0,
     "energy": 1.0, "valence": 1.0, "danceability": 1.0, "acoustic": 1.0,
     "mood_tags": 0.5, "popularity": 0.5, "decade": 0.5, "instrumentalness": 0.5, "language": 0.5},
)
MOOD_FIRST = ScoringMode(
    "mood_first",
    "Match the feeling: mood, mood tags and positivity matter most, any genre is fine.",
    {"genre": 0.5, "genre_partial": 0.25, "mood": 3.0,
     "energy": 1.0, "valence": 2.0, "danceability": 0.5, "acoustic": 0.5,
     "mood_tags": 2.0, "popularity": 0.25, "decade": 0.25, "instrumentalness": 0.25, "language": 0.25},
)
ENERGY_FOCUSED = ScoringMode(
    "energy_focused",
    "Match the intensity: energy and danceability dominate (workouts, parties, focus).",
    {"genre": 0.5, "genre_partial": 0.25, "mood": 0.5,
     "energy": 4.0, "valence": 0.5, "danceability": 2.0, "acoustic": 1.0,
     "mood_tags": 0.5, "popularity": 0.25, "decade": 0.25, "instrumentalness": 0.5, "language": 0.25},
)

MODES: Dict[str, ScoringMode] = {m.name: m for m in (BALANCED, GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED)}
DEFAULT_MODE = BALANCED

# Which rule each user preference turns on (used to work out a profile's best score).
PREFERENCE_RULES = {
    "favorite_genre": "genre",
    "favorite_mood": "mood",
    "target_energy": "energy",
    "target_valence": "valence",
    "target_danceability": "danceability",
    "likes_acoustic": "acoustic",
    "favorite_mood_tags": "mood_tags",
    "target_popularity": "popularity",
    "favorite_decade": "decade",
    "target_instrumentalness": "instrumentalness",
    "preferred_language": "language",
}

ModeLike = Union[ScoringMode, str, None]


def get_mode(mode: ModeLike = None) -> ScoringMode:
    """Accept a ScoringMode, a mode name like "genre_first", or None (default mode)."""
    if mode is None:
        return DEFAULT_MODE
    if isinstance(mode, ScoringMode):
        return mode
    try:
        return MODES[str(mode).strip().lower()]
    except KeyError:
        raise ValueError(f"Unknown scoring mode {mode!r}. Choose from: {', '.join(MODES)}") from None


def max_score(user_prefs: Dict, mode: ModeLike = None) -> float:
    """Best possible score for THIS profile in THIS mode: only rules the user set can earn points."""
    m = get_mode(mode)
    return sum(m.weight(rule) for key, rule in PREFERENCE_RULES.items()
               if user_prefs.get(key) not in (None, "", []))


# Best possible score in the default mode when every preference is given.
MAX_SCORE = sum(DEFAULT_MODE.weight(rule) for rule in PREFERENCE_RULES.values())


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Advanced features (defaults keep older code and tests working).
    popularity: int = 50
    release_decade: int = 2020
    mood_tags: Tuple[str, ...] = ()
    instrumentalness: float = 0.0
    language: str = "english"

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read the songs CSV into a list of dicts, converting numeric columns to int/float."""
    print(f"Loading songs from {csv_path}...")
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for name in INT_FIELDS:
                row[name] = int(row[name])
            for name in FLOAT_FIELDS:
                row[name] = float(row[name])
            for name in LIST_FIELDS:
                row[name] = _parse_tags(row[name])
            songs.append(row)
    return songs

def _parse_tags(value) -> List[str]:
    """Turn "a;b" text or a list/tuple of tags into a clean lowercase list."""
    if isinstance(value, str):
        value = value.replace(",", ";").split(";")
    return [str(tag).strip().lower() for tag in value or [] if str(tag).strip()]

def _closeness(target: float, value: float, scale: float = 1.0) -> float:
    """1.0 when value == target, falling linearly to 0.0 when they are `scale` apart."""
    return max(0.0, 1.0 - abs(target - value) / scale)

def score_song(user_prefs: Dict, song: Dict, mode: ModeLike = None) -> Tuple[float, List[str]]:
    """Score one song against the user's preferences using a scoring mode; return (score, reasons)."""
    w = get_mode(mode).weight
    score = 0.0
    reasons: List[str] = []

    def add(points: float, reason: str) -> None:
        nonlocal score
        if points > 0:
            score += points
            reasons.append(f"{reason} (+{points:.2f})")

    # 1. Genre: exact match, or partial match when one name contains the other.
    user_genre = str(user_prefs.get("favorite_genre", "")).strip().lower()
    song_genre = str(song["genre"]).strip().lower()
    if user_genre and song_genre == user_genre:
        add(w("genre"), f"genre match: {song['genre']}")
    elif user_genre and (user_genre in song_genre or song_genre in user_genre):
        add(w("genre_partial"), f"related genre: {song['genre']} ~ {user_prefs['favorite_genre']}")

    # 2. Mood: exact match only.
    user_mood = str(user_prefs.get("favorite_mood", "")).strip().lower()
    if user_mood and str(song["mood"]).strip().lower() == user_mood:
        add(w("mood"), f"mood match: {song['mood']}")

    # 3. Numeric closeness: reward songs NEAR the target, not the highest values.
    for feature in NUMERIC_FEATURES:
        target = user_prefs.get(f"target_{feature}")
        if target is not None:
            add(_closeness(target, song[feature]) * w(feature),
                f"{feature} {song[feature]:.2f} vs target {target:.2f}")

    # 4. Acoustic fit: acoustic lovers get acousticness, others get its opposite.
    if "likes_acoustic" in user_prefs:
        likes = bool(user_prefs["likes_acoustic"])
        fit = song["acousticness"] if likes else 1.0 - song["acousticness"]
        label = "acoustic" if likes else "produced/electronic"
        add(fit * w("acoustic"), f"{label} sound, acousticness {song['acousticness']:.2f}")

    # 5. Mood tags: partial credit for each of the user's tags the song shares.
    user_tags = _parse_tags(user_prefs.get("favorite_mood_tags") or [])
    if user_tags:
        matched = [tag for tag in user_tags if tag in _parse_tags(song.get("mood_tags", []))]
        if matched:
            add(w("mood_tags") * len(matched) / len(user_tags),
                f"mood tags {', '.join(matched)} ({len(matched)}/{len(user_tags)})")

    # 6. Popularity: closeness on a 0-100 scale (low target = deep cuts, high = hits).
    target = user_prefs.get("target_popularity")
    if target is not None:
        add(_closeness(target, song["popularity"], scale=100) * w("popularity"),
            f"popularity {song['popularity']} vs target {target}")

    # 7. Release decade: full points for the same decade, fading to 0 at 30+ years apart.
    decade = user_prefs.get("favorite_decade")
    if decade is not None:
        add(_closeness(decade, song["release_decade"], scale=DECADE_RANGE_YEARS) * w("decade"),
            f"from the {song['release_decade']}s vs {decade}s")

    # 8. Instrumentalness: closeness on a 0-1 scale (high = no vocals, good for focus).
    target = user_prefs.get("target_instrumentalness")
    if target is not None:
        add(_closeness(target, song["instrumentalness"]) * w("instrumentalness"),
            f"instrumentalness {song['instrumentalness']:.2f} vs target {target:.2f}")

    # 9. Language: exact match only.
    language = str(user_prefs.get("preferred_language", "")).strip().lower()
    if language and str(song.get("language", "")).strip().lower() == language:
        add(w("language"), f"language: {song['language']}")

    return score, reasons

def _key(value) -> str:
    return str(value).strip().lower()

def diversity_penalty(
    song: Dict, picked: List[Dict],
    artist_penalty: float = ARTIST_REPEAT_PENALTY, genre_penalty: float = GENRE_REPEAT_PENALTY,
) -> Tuple[float, List[str]]:
    """Points to subtract from `song` because its artist/genre already appear in `picked`."""
    artists = Counter(_key(s["artist"]) for s in picked)
    genres = Counter(_key(s["genre"]) for s in picked)
    penalty, reasons = 0.0, []
    repeats = artists[_key(song["artist"])]
    if repeats and artist_penalty:
        penalty += repeats * artist_penalty
        reasons.append(f"diversity penalty: artist {song['artist']} already in list x{repeats} "
                       f"(-{repeats * artist_penalty:.2f})")
    repeats = genres[_key(song["genre"])]
    if repeats and genre_penalty:
        penalty += repeats * genre_penalty
        reasons.append(f"diversity penalty: genre {song['genre']} already in list x{repeats} "
                       f"(-{repeats * genre_penalty:.2f})")
    return penalty, reasons

def _pick_diverse(ranked: List[Tuple[Dict, float, List[str]]], k: int) -> List[Tuple[Dict, float, List[str]]]:
    """Greedy re-rank: pick one song at a time, penalizing artists/genres already picked."""
    remaining, picked = list(ranked), []
    while remaining and len(picked) < k:
        chosen = [s for s, _, _ in picked]
        best_i, best = 0, None
        for i, (song, score, reasons) in enumerate(remaining):
            penalty, notes = diversity_penalty(song, chosen)
            adjusted = max(0.0, score - penalty)
            if best is None or adjusted > best[1]:  # strict ">" keeps ties in ranked order
                best_i, best = i, (song, adjusted, reasons + notes)
        picked.append(best)
        remaining.pop(best_i)
    return picked

def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5, mode: ModeLike = None, diverse: bool = False
) -> List[Tuple[Dict, float, str]]:
    """Score every song with the chosen mode, rank highest first, return the top k as (song, score, explanation).

    With diverse=True, songs whose artist or genre is already in the list lose points
    (ARTIST_REPEAT_PENALTY / GENRE_REPEAT_PENALTY per repeat), so the top k is more varied.
    """
    m = get_mode(mode)  # resolve once so an unknown mode fails before any scoring

    # 1. Judge: one (song, score, reasons) tuple per song.
    scored = [(song, *score_song(user_prefs, song, m)) for song in songs]

    # 2. Rank: highest score first. sorted() is stable, so ties keep catalog order,
    #    and it returns a new list, so `songs` itself is never reordered.
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)

    # 3. Pick: top k (optionally re-ranked for variety), with a readable explanation.
    top = _pick_diverse(ranked, k) if diverse else ranked[:k]
    return [
        (song, score, "; ".join(reasons) or "no strong match with your preferences")
        for song, score, reasons in top
    ]
