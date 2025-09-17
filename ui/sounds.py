"""Sound utilities for AnimalFramework (UI).
Provides two short SFX:
  - play_chime(): soft, pleasant chime that rises in pitch per correct click
  - play_error(): short, descending double‑chirp for incorrect choices

Includes a test helper:
  - test_sound_sequence(n=6, interval=0.25, play_sound=play_chime)

If audio deps/backends are unavailable, functions degrade gracefully.
Requires (optional):
    pip install numpy simpleaudio

Run test:
    SOUND_DEBUG=1 python -m ui.sounds error
"""
from __future__ import annotations
import os
import sys
import time
import tempfile
import subprocess
import wave
from typing import Optional, Callable

# Optional deps
try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # type: ignore

try:
    import simpleaudio as sa  # type: ignore
except Exception:
    sa = None  # type: ignore

# Debug toggle via functions
SOUND_VERBOSE = False

def enable_debug():
    global SOUND_VERBOSE
    SOUND_VERBOSE = True

def disable_debug():
    global SOUND_VERBOSE
    SOUND_VERBOSE = False

def _dbg(msg: str) -> None:
    if SOUND_VERBOSE:
        print(f"[ui.sounds][debug] {msg}")

_click_count = 0


def _np_available() -> bool:
    ok = np is not None
    _dbg(f"NumPy available: {ok}")
    return ok


def _play_pcm(audio_int16, sample_rate: int):
    """Best‑effort playback: try simpleaudio; fall back to OS player (afplay/aplay/PowerShell)."""
    _dbg("_play_pcm called")
    if sa is not None:
        try:
            _dbg("trying simpleaudio.play_buffer")
            return sa.play_buffer(audio_int16, num_channels=1, bytes_per_sample=2, sample_rate=sample_rate)
        except Exception as e:
            _dbg(f"simpleaudio failed: {e}")
            print(f"[ui.sounds] simpleaudio failed: {e}")
    # Fallback: write temp WAV and use OS player
    try:
        _dbg("falling back to temp WAV + OS player")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name
        _dbg(f"temp wav: {tmp_path}")
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        if sys.platform == 'darwin':
            _dbg("using afplay")
            subprocess.Popen(['afplay', tmp_path])
        elif sys.platform.startswith('linux'):
            _dbg("using aplay")
            subprocess.Popen(['aplay', tmp_path])
        elif os.name == 'nt':
            _dbg("using powershell SoundPlayer")
            subprocess.Popen(['powershell', '-c', f"(New-Object Media.SoundPlayer '{tmp_path}').PlaySync();"])  # blocking
        else:
            print(f"[ui.sounds] WAV written to {tmp_path}")
        return None
    except Exception as e:
        _dbg(f"fallback playback failed: {e}")
        print(f"[ui.sounds] Fallback playback failed: {e}")
        return None


def reset_chime_counter() -> None:
    """Reset the chime pitch counter (call at the start of a new round)."""
    global _click_count
    _click_count = 0
    _dbg("reset_chime_counter() called")


def play_chime(
    base_freq: float = 523.25,
    semitone_step: float = 1.059,
    duration: float = 0.18,
    sample_rate: int = 22_050,
    gain: float = 0.40,
):
    """Play a soft chime sound, rising in pitch with each correct click."""
    global _click_count
    _dbg("play_chime() invoked")
    if not _np_available():
        print("[ui.sounds] NumPy unavailable; cannot synthesize chime.")
        return None
    try:
        # Use the current counter as the step *before* incrementing so a fresh round
        # starts exactly at the base frequency.
        step_idx = _click_count % 12
        freq = float(base_freq) * (float(semitone_step) ** step_idx)
        _click_count += 1
        _dbg(f"chime freq={freq:.2f}Hz, duration={duration}s, sr={sample_rate}")
        t = np.linspace(0.0, float(duration), int(sample_rate * duration), False)
        waveform = gain * np.sin(2.0 * np.pi * freq * t)
        envelope = np.exp(-3.2 * t)
        waveform *= envelope
        audio = (waveform * 32767).astype(np.int16)
        _dbg("playing chime via _play_pcm")
        return _play_pcm(audio, sample_rate)
    except Exception as e:
        _dbg(f"play_chime exception: {e}")
        print(f"[ui.sounds] Could not play chime: {e}")
        return None


def play_error(
    start_freq: float = 400.0,
    end_freq: float = 300.0,
    duration: float = 0.2,
    sample_rate: int = 44_100,
    gain: float = 0.55,
    second_start: float = 200.0,
    second_end: float = 100.0,
):
    """Play a short, descending double‑chirp for incorrect choices."""
    _dbg("play_error() invoked")
    _dbg(f"play_error params: start={start_freq}, end={end_freq}, duration={duration}, sr={sample_rate}, gain={gain}, second=({second_start}->{second_end})")
    if not _np_available():
        print("[ui.sounds] NumPy unavailable; cannot synthesize error sound.")
        return None
    try:
        # First descending chirp
        t = np.linspace(0.0, float(duration), int(sample_rate * duration), False)
        freqs = np.linspace(float(start_freq), float(end_freq), t.size)
        phase = 2.0 * np.pi * np.cumsum(freqs) / float(sample_rate)
        waveform = gain * np.sin(phase)
        envelope = np.exp(-3.5 * t)
        waveform *= envelope
        audio = (waveform * 32767).astype(np.int16)
        _dbg("playing first chirp")
        _play_pcm(audio, sample_rate)
        time.sleep(0.1)
        _dbg("gap 100ms between chirps done")
        # Second descending chirp
        freqs2 = np.linspace(float(second_start), float(second_end), t.size)
        phase2 = 2.0 * np.pi * np.cumsum(freqs2) / float(sample_rate)
        waveform2 = gain * np.sin(phase2)
        envelope2 = np.exp(-3.5 * t)
        waveform2 *= envelope2
        audio2 = (waveform2 * 32767).astype(np.int16)
        _dbg("playing second chirp")
        return _play_pcm(audio2, sample_rate)
    except Exception as e:
        _dbg(f"play_error exception: {e}")
        print(f"[ui.sounds] Could not play error sound: {e}")
        return None


def test_sound_sequence(
    n: int = 6,
    interval: float = 0.25,
    play_sound: Callable[[], Optional[object]] = play_chime,
) -> None:
    """Play a short sequence of sounds for manual testing."""
    _dbg(f"test_sound_sequence(n={n}, interval={interval}, fn={getattr(play_sound, '__name__', play_sound)})")
    reset_chime_counter()
    for _ in range(max(1, int(n))):
        po = play_sound()
        # If simpleaudio returned a PlayObject, let it finish politely
        try:
            if hasattr(po, 'wait_done'):
                po.wait_done()
        except Exception:
            pass
        time.sleep(max(0.05, float(interval)))


if __name__ == "__main__":  # Manual CLI audition: python -m ui.sounds [mode] [n] [interval]
    enable_debug()
    if not _np_available():
        print("[ui.sounds] NumPy unavailable (install: pip install numpy; simpleaudio optional)")
        sys.exit(0)
    args = [a.lower() for a in sys.argv[1:]]
    mode = args[0] if args else "chime"
    try:
        n = int(args[1]) if len(args) > 1 else 6
    except Exception:
        n = 6
    try:
        interval = float(args[2]) if len(args) > 2 else 0.25
    except Exception:
        interval = 0.25
    if mode not in {"chime", "error", "both"}:
        print("Usage: python -m ui.sounds [chime|error|both] [n] [interval]")
        sys.exit(2)
    if mode in {"chime", "both"}:
        _dbg("__main__: starting chime sequence")
        print(f"Playing chime sequence (n={n}, interval={interval})...")
        test_sound_sequence(n, interval, play_chime)
    # if mode in {"error", "both"}:
    #     _dbg("__main__: starting error sequence")
    #     print(f"Playing error sequence (n={n}, interval={interval})...")
    #     test_sound_sequence(n, interval, play_error)
    print("Done.")