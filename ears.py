import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
import re

# ── Model ─────────────────────────────────────────────────────────────────────
# "small" is much more accurate than "base" on CPU.
# Downloads ~460MB once, then cached forever.
model = WhisperModel("small", device="cpu", compute_type="int8")
print("[EARS] Whisper 'small' ready.")

# ── Audio constants ───────────────────────────────────────────────────────────
SAMPLE_RATE         = 16000
CHUNK_DURATION      = 0.05          # 50ms chunks
MAX_RECORD_SECONDS  = 30
MIN_SPEECH_SECONDS  = 0.4           # Ignore bursts shorter than this

# ── VAD thresholds (set by calibrate_microphone at startup) ───────────────────
# These are overwritten at runtime — do not tune manually.
SILENCE_THRESHOLD   = 0.025         # RMS below this = silence
SPEECH_THRESHOLD    = 0.045         # RMS above this = definitely speaking

# Pre-roll: audio captured BEFORE speech is detected, so first syllable
# is never lost. 0.5s gives a comfortable buffer.
PRE_ROLL_SECONDS    = 0.5
PRE_ROLL_CHUNKS     = int(PRE_ROLL_SECONDS / CHUNK_DURATION)

# How long quiet must last before we consider the sentence finished.
SILENCE_DURATION    = 1.8           # seconds — generous to avoid cutting off

# Smooth RMS over N chunks to avoid reacting to single noise spikes.
RMS_SMOOTH_WINDOW   = 5

# ── Wake word patterns ────────────────────────────────────────────────────────
WAKE_WORD_PATTERNS = [
    re.compile(r"\bhey\s+kora\b",       re.IGNORECASE),
    re.compile(r"\bhi\s+kora\b",        re.IGNORECASE),
    re.compile(r"\bwake\s+up\s+kora\b", re.IGNORECASE),
    re.compile(r"\bkora\s+wake\s+up\b", re.IGNORECASE),
]

# ── Whisper hallucination filter ──────────────────────────────────────────────
HALLUCINATION_PHRASES = {
    "thanks for watching", "you", ".", "..", "...", "hmm", "um", "uh", "ah", "oh",
    "thank you for watching", "please subscribe", "see you next time",
}


# ─────────────────────────────────────────────────────────────────────────────
#  MIC CALIBRATION  —  called once at startup
# ─────────────────────────────────────────────────────────────────────────────

def calibrate_microphone(duration: float = 2.0) -> None:
    """
    Measure your room's background noise and automatically set
    SILENCE_THRESHOLD and SPEECH_THRESHOLD to correct values.

    Without this, the hardcoded defaults may be wrong for your mic.
    """
    global SILENCE_THRESHOLD, SPEECH_THRESHOLD

    print(f"\n[EARS] ── Mic calibration ──")
    print(f"[EARS] Measuring background noise for {duration:.0f}s — please stay quiet...")

    chunk_size = int(SAMPLE_RATE * CHUNK_DURATION)
    num_chunks = int(duration / CHUNK_DURATION)
    rms_values = []

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
            for _ in range(num_chunks):
                chunk, _ = stream.read(chunk_size)
                rms = float(np.sqrt(np.mean(chunk.flatten() ** 2)))
                rms_values.append(rms)
    except Exception as e:
        print(f"[EARS] Calibration failed ({e}) — using defaults.")
        return

    noise_floor = float(np.percentile(rms_values, 80))  # 80th percentile = stable noise estimate
    SILENCE_THRESHOLD = max(0.008, noise_floor * 2.0)    # 2x noise floor = silence boundary
    SPEECH_THRESHOLD  = max(0.015, noise_floor * 3.5)    # 3.5x noise floor = clear speech

    print(f"[EARS] Noise floor : {noise_floor:.5f}")
    print(f"[EARS] Silence < {SILENCE_THRESHOLD:.5f}")
    print(f"[EARS] Speech  > {SPEECH_THRESHOLD:.5f}")
    print(f"[EARS] ── Calibration done ──\n")


# ─────────────────────────────────────────────────────────────────────────────
#  MIC TEST  —  run this manually to diagnose issues
# ─────────────────────────────────────────────────────────────────────────────

def test_microphone(duration: float = 5.0) -> None:
    """
    Run this manually to see live RMS readings from your mic.
    Speak normally and check what values appear — use them to tune thresholds.

    Usage:  python -c "from ears import test_microphone; test_microphone()"
    """
    print(f"\n[MIC TEST] Speak normally for {duration:.0f}s — watch your RMS values:")
    print(f"           Current thresholds → silence={SILENCE_THRESHOLD:.5f}  speech={SPEECH_THRESHOLD:.5f}")
    print(f"           If your speech RMS is BELOW speech threshold, thresholds are too high.\n")

    chunk_size = int(SAMPLE_RATE * CHUNK_DURATION)
    total      = int(duration / CHUNK_DURATION)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        for i in range(total):
            chunk, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(chunk.flatten() ** 2)))
            bar = "█" * int(rms * 500)
            label = "SPEECH" if rms > SPEECH_THRESHOLD else ("noise" if rms > SILENCE_THRESHOLD else "quiet")
            print(f"  RMS {rms:.5f}  {bar:<30}  [{label}]")


# ─────────────────────────────────────────────────────────────────────────────
#  AUDIO HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(audio: np.ndarray) -> np.ndarray:
    """Scale to full amplitude range so Whisper gets a clear signal."""
    peak = np.max(np.abs(audio))
    if peak < 1e-6:
        return audio
    return (audio / peak * 0.95).astype(np.float32)


def _smooth_rms(history: list) -> float:
    window = history[-RMS_SMOOTH_WINDOW:]
    return sum(window) / len(window) if window else 0.0


def _is_hallucination(text: str) -> bool:
    cleaned = text.strip().lower().strip(".,!?-–— ")
    return cleaned in HALLUCINATION_PHRASES or len(cleaned) < 2


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN LISTENER
# ─────────────────────────────────────────────────────────────────────────────

def listen() -> str:
    """
    Record one voice command and return transcribed text.

    Design principles:
    - Dynamic thresholds from calibration (not hardcoded guesses)
    - Pre-roll buffer so first syllable is never cut
    - Smoothed RMS to ignore brief noise spikes
    - Generous 1.8s silence window — doesn't cut you off mid-sentence
    - Audio normalised before Whisper sees it
    - NO Silero VAD filter (it was too aggressive, cutting real words)
    - NO best_of=5 (ran Whisper 5× on CPU — very slow)
    - Hallucination filter removes noise-only outputs
    """
    filename = "temp_audio.wav"
    print(f"\n--- Listening  [silence<{SILENCE_THRESHOLD:.4f}  speech>{SPEECH_THRESHOLD:.4f}] ---")

    pre_roll       = []
    audio_chunks   = []
    rms_history    = []
    silent_time    = 0.0
    speech_started = False
    total_time     = 0.0
    chunk_size     = int(SAMPLE_RATE * CHUNK_DURATION)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        while total_time < MAX_RECORD_SECONDS:
            chunk, _ = stream.read(chunk_size)
            chunk     = chunk.flatten()
            total_time += CHUNK_DURATION

            rms      = float(np.sqrt(np.mean(chunk ** 2)))
            rms_history.append(rms)
            smoothed = _smooth_rms(rms_history)

            if not speech_started:
                pre_roll.append(chunk.copy())
                if len(pre_roll) > PRE_ROLL_CHUNKS:
                    pre_roll.pop(0)

                if smoothed > SPEECH_THRESHOLD:
                    speech_started = True
                    audio_chunks.extend(pre_roll)   # Don't lose pre-roll audio
                    audio_chunks.append(chunk.copy())
                    print(f"  ▶ speech  RMS={smoothed:.4f}")

            else:
                audio_chunks.append(chunk.copy())

                if smoothed < SILENCE_THRESHOLD:
                    silent_time += CHUNK_DURATION
                    if silent_time >= SILENCE_DURATION:
                        print(f"  ■ silence  ({len(audio_chunks)*CHUNK_DURATION:.1f}s captured)")
                        break
                else:
                    if silent_time > 0:
                        print(f"  ▶ resumed  RMS={smoothed:.4f}")
                    silent_time = 0.0

    if not speech_started or len(audio_chunks) < int(MIN_SPEECH_SECONDS / CHUNK_DURATION):
        return ""

    # Save clean audio
    raw   = np.concatenate(audio_chunks, axis=0)
    clean = _normalize(raw)
    sf.write(filename, clean, SAMPLE_RATE)

    # Transcribe — simple, fast, no extra passes
    segments, _ = model.transcribe(
        filename,
        language    = "en",
        beam_size   = 5,
        best_of     = 1,                        # 1 pass only — fast on CPU
        vad_filter  = False,                    # OFF — was cutting real words
        condition_on_previous_text = False,     # No bleed between calls
        no_speech_threshold        = 0.4,       # More lenient — trust the audio
        log_prob_threshold         = -1.5,      # More lenient — accept quiet speech
        compression_ratio_threshold = 2.8,
    )

    text = " ".join(seg.text for seg in segments).strip()

    if os.path.exists(filename):
        os.remove(filename)

    if _is_hallucination(text):
        print(f"  [hallucination discarded: '{text}']")
        return ""

    if text:
        print(f"[HEARD]: {text}")
    return text


# ─────────────────────────────────────────────────────────────────────────────
#  WAKE WORD
# ─────────────────────────────────────────────────────────────────────────────

def extract_wake_command(text: str):
    if not text:
        return None
    normalized = " ".join(text.strip().split())
    for pattern in WAKE_WORD_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return normalized[match.end():].strip(" ,.!?-")
    return None