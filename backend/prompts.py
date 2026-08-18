"""System prompts and small text helpers used by the LLM copilot."""
from __future__ import annotations

EXPAND_SYSTEM = """You are a prompt engineer who specialises in text-to-music
diffusion models (MusicGen, MiniMax Music, AudioLDM). You turn short, casual
ideas from a user into a single dense paragraph that a music model will
actually respond to.

Your paragraph must include, in natural prose (no lists, no headings):
- Primary genre and 1-2 sub-genres
- Mood / emotional arc
- Approximate tempo in BPM, or a tempo feel word
- Key instruments and their timbre (e.g. "warm Rhodes electric piano",
  "punchy analog kick", "airy legato strings")
- Production era or reference ("late-90s trip-hop", "modern hyperpop")
- Mix cues ("wide stereo pads", "sidechained bass", "tape saturation")
- Structural shape if relevant ("slow intro, breakbeat drop at 30s")

Never invent lyrics. Never quote artists by name. Keep it under 90 words.
Return ONLY the paragraph — no preface, no explanation, no quotes."""

TRANSLATE_SYSTEM = """You translate short creative music-brief ideas from any
language into fluent, idiomatic English suitable for a text-to-music model
prompt. Preserve every nuance about mood, instruments and genre. Return ONLY
the English translation with no preface."""

LYRICS_SYSTEM = """You are a lyricist. Given a theme, write short song
lyrics with clear section tags on their own lines: [Verse], [Chorus],
[Bridge], [Outro]. Keep line count modest (verse ≤ 6 lines, chorus ≤ 4
lines). Language: match the theme's language unless the user asks
otherwise. Return ONLY the lyrics, nothing else."""

CRITIQUE_SYSTEM = """You are a mixing/production reviewer. Given a music
prompt (and optionally lyrics), point out what is missing that would help a
diffusion music model: instrumentation, tempo, mixing hints, arrangement.
Keep it under 80 words. Return plain prose, no lists."""

STYLE_PRESETS: dict[str, str] = {
    "lofi-hiphop": (
        "Warm dusty lo-fi hip-hop beat around 82 BPM, mellow Rhodes chords, "
        "vinyl crackle, boom-bap drums with soft-clipped kick and brushed snare, "
        "muted upright bass, jazzy 7th chord progression, tape saturation, "
        "gentle rain in the background, late-night study mood."
    ),
    "synthwave": (
        "Retro 1984 synthwave at 108 BPM, gated reverb snare, driving analog "
        "arpeggios on a Juno, wide detuned saw supersaw lead, punchy sidechained "
        "bass, cinematic FM stabs, neon-drenched nostalgic mood, long tape delay."
    ),
    "cinematic": (
        "Sweeping modern cinematic score, slow build from solo felt piano into "
        "full orchestra at 75 BPM, warm brass swells, taiko hits, hybrid "
        "percussion, soaring legato strings, choir ahs on top, subtle synth bed, "
        "emotional and hopeful, film-trailer dynamics."
    ),
    "dnb": (
        "Fast liquid drum-and-bass at 174 BPM, chopped Amen break with tight "
        "reverb, deep rolling Reese bass, lush pad chords, distant vocal chops, "
        "airy hats, atmospheric intro then hard drop, futuristic and euphoric."
    ),
    "acoustic-folk": (
        "Intimate acoustic folk ballad at 88 BPM, fingerpicked steel-string "
        "guitar, gentle brushed drums, upright bass, faint mandolin, warm room "
        "reverb, honest and emotional vocal delivery, storyteller mood."
    ),
    "trap": (
        "Modern trap beat at 140 BPM (half-time feel), booming 808 with slides, "
        "crisp trap hats with triplet rolls, dark minor piano riff, atmospheric "
        "pad, punchy snare on the 3, moody nocturnal vibe."
    ),
    "house": (
        "Warm deep house at 122 BPM, four-on-the-floor kick, snappy clap on 2/4, "
        "shuffling hats, soulful Rhodes chords, subby analog bass, filtered "
        "vocal chop hook, wide airy pads, sunset rooftop mood."
    ),
    "orchestral": (
        "Full romantic-era orchestra at 90 BPM, sweeping strings, dramatic brass "
        "counterpoint, timpani rolls, harp glissandi, woodwind flourishes, "
        "grand hall reverb, heroic and triumphant."
    ),
    "ambient": (
        "Slow-evolving ambient soundscape, no percussion, layered granular pads, "
        "field recordings of distant water, subtle bell tones, long reverb tails, "
        "meditative, drifting, 60 BPM feel."
    ),
    "phonk": (
        "Dark drift phonk at 135 BPM, cowbell pattern, distorted 808 bass, "
        "chopped Memphis vocal sample, tape hiss, aggressive but hypnotic, "
        "night-driving energy."
    ),
}


def preset_names() -> list[str]:
    return list(STYLE_PRESETS.keys())
