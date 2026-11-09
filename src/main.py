"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs

Usage (run from the project folder):
  python3 -m src.main                         # all profiles, default mode
  python3 -m src.main --mode genre_first      # switch scoring mode
  python3 -m src.main --profile "Chill Lofi"  # just one profile
  python3 -m src.main --compare               # top 5 of every mode, side by side
  python3 -m src.main --list-modes            # show the available modes
  python3 -m src.main --diverse               # penalize repeated artists/genres in the top 5
  python3 -m src.main --detailed              # long "card" view instead of tables
"""

import argparse
import textwrap

from src.recommender import MODES, get_mode, load_songs, max_score, recommend_songs
from src.table_view import recommendations_table, summary_table

# Scoring mode used when --mode is not given. Change it here, or pass --mode on the command line.
# Options: "balanced", "genre_first", "mood_first", "energy_focused"
MODE = "balanced"

# Diversity penalty: True = repeated artists/genres in the top 5 lose points. Or pass --diverse.
DIVERSE = False


# Taste profiles to test the recommender with.
# Categorical features are scored as exact matches;
# numeric targets (0.0-1.0) reward songs that are CLOSE to the value.
PROFILES = {
    # Default profile: happy pop, lively but not all-out intense.
    "Upbeat Pop Listener": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.70,
        "target_valence": 0.80,
        "target_danceability": 0.80,
        "likes_acoustic": False,
    },
    # Workout pop: maximum energy and groove, electronic production.
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "intense",
        "target_energy": 0.90,
        "target_valence": 0.75,
        "target_danceability": 0.85,
        "likes_acoustic": False,
    },
    # Study/background music: calm, mellow, warm acoustic texture.
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.35,
        "target_valence": 0.60,
        "target_danceability": 0.55,
        "likes_acoustic": True,
    },
    # Heavy and dark: very high energy, low positivity, not built for dancing.
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.92,
        "target_valence": 0.35,
        "target_danceability": 0.55,
        "likes_acoustic": False,
    },
    # --- Profiles using the advanced features (Challenge 1) ---
    # Same as Upbeat Pop, plus detailed mood tags and a taste for well-known songs.
    "Happy Pop + Mood Tags": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.70,
        "target_valence": 0.80,
        "target_danceability": 0.80,
        "likes_acoustic": False,
        "favorite_mood_tags": ["uplifting", "sunny"],
        "target_popularity": 75,
    },
    # Warm, nostalgic 90s-era songs that are less mainstream.
    "90s Nostalgia Deep Cuts": {
        "favorite_mood": "nostalgic",
        "target_energy": 0.50,
        "likes_acoustic": True,
        "favorite_mood_tags": ["nostalgic", "warm", "wistful"],
        "favorite_decade": 1990,
        "target_popularity": 35,
        "preferred_language": "english",
    },
    # Calm music with no vocals, for deep focus.
    "Instrumental Study Session": {
        "target_energy": 0.35,
        "likes_acoustic": True,
        "favorite_mood_tags": ["calm", "focused"],
        "target_instrumentalness": 0.90,
        "preferred_language": "instrumental",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("--mode", default=MODE, choices=list(MODES), help="scoring mode")
    parser.add_argument("--profile", choices=list(PROFILES), help="run only this profile")
    parser.add_argument("--compare", action="store_true", help="show every mode side by side")
    parser.add_argument("--list-modes", action="store_true", help="list scoring modes and exit")
    parser.add_argument("--diverse", action="store_true", default=DIVERSE,
                        help="penalize repeated artists/genres in the top results")
    parser.add_argument("--detailed", action="store_true",
                        help="show the long card view instead of tables")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_modes:
        for mode in MODES.values():
            print(f"{mode.name:<15} {mode.description}")
        return

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    profiles = {args.profile: PROFILES[args.profile]} if args.profile else PROFILES

    summary = []
    for profile_name, user_prefs in profiles.items():
        if args.compare:
            print_mode_comparison(profile_name, user_prefs, songs, args.diverse)
            continue
        recommendations = recommend_songs(user_prefs, songs, k=5, mode=args.mode, diverse=args.diverse)
        if args.detailed:
            print_recommendations(profile_name, user_prefs, recommendations, args.mode, args.diverse)
        else:
            print_recommendations_table(profile_name, user_prefs, recommendations, args.mode, args.diverse)
        summary.append((profile_name, recommendations, max_score(user_prefs, args.mode)))

    if len(summary) > 1:
        print()
        print(f" SUMMARY  [mode: {mode_label(args.mode, args.diverse)}]")
        print(summary_table(summary))


def mode_label(mode: str, diverse: bool) -> str:
    return get_mode(mode).name + (", diverse" if diverse else "")


def print_recommendations_table(
    profile_name: str, user_prefs: dict, recommendations: list, mode: str = MODE, diverse: bool = False
) -> None:
    """Print one profile's top results as a table, with the reasons for every score."""
    prefs_line = " · ".join(
        f"{key.removeprefix('favorite_').removeprefix('target_')}={value}"
        for key, value in user_prefs.items()
    )
    print()
    print(f" {profile_name}  [mode: {mode_label(mode, diverse)}]")
    print(textwrap.fill(prefs_line, 96, initial_indent=" ", subsequent_indent=" "))
    print(recommendations_table(recommendations, max_score(user_prefs, mode)))


def print_mode_comparison(profile_name: str, user_prefs: dict, songs: list, diverse: bool = False) -> None:
    """Print one compact column of top-5 titles per scoring mode."""
    col = 20
    results = {name: recommend_songs(user_prefs, songs, k=5, mode=name, diverse=diverse) for name in MODES}
    print()
    print(f" {profile_name}" + ("  [diverse]" if diverse else ""))
    print(" " + "".join(f"{name:<{col}}" for name in MODES))
    for rank in range(5):
        row = [results[name][rank][0]["title"][: col - 2] for name in MODES]
        print(" " + "".join(f"{title:<{col}}" for title in row))


WIDTH = 64
BAR_LENGTH = 20


def score_bar(score: float, best: float) -> str:
    """Draw a text bar showing how close a score is to the best possible score."""
    filled = round(BAR_LENGTH * score / best) if best else 0
    return "█" * filled + "░" * (BAR_LENGTH - filled)


def print_recommendations(
    profile_name: str, user_prefs: dict, recommendations: list, mode: str = MODE, diverse: bool = False
) -> None:
    """Print the profile and each (song, score, explanation) in a readable block."""
    # Drop the "favorite_"/"target_" prefixes so the profile fits on one line.
    prefs_line = " · ".join(
        f"{key.removeprefix('favorite_').removeprefix('target_')}={value}"
        for key, value in user_prefs.items()
    )

    print()
    print("═" * WIDTH)
    print(f" Top {len(recommendations)} for: {profile_name}  [mode: {mode_label(mode, diverse)}]")
    print(textwrap.fill(prefs_line, WIDTH, initial_indent=" ", subsequent_indent=" "))
    print("═" * WIDTH)

    best = max_score(user_prefs, mode)  # only the rules this profile uses can earn points
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print()
        print(f" #{rank}  {song['title']} — {song['artist']}")
        print(f"     {song['genre']} · {song['mood']}")
        print(f"     Score: {score:.2f} / {best:.2f}  {score_bar(score, best)}")
        print("     Why:")
        for reason in explanation.split("; "):
            print(f"       • {reason}")
        print(" " + "─" * (WIDTH - 1))


if __name__ == "__main__":
    main()
