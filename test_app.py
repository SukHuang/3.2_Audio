import numpy as np

from app import analyze_audio


def test_analyze_audio_finds_tone_and_bounds_score():
    sample_rate = 16_000
    samples = np.sin(2 * np.pi * 440 * np.arange(sample_rate) / sample_rate)
    result = analyze_audio((sample_rate, samples), sensitivity=0.35)

    assert abs(result["frequency"] - 440) < 2
    assert 0 <= result["score"] <= 100
    assert result["alert"] is True


def test_analyze_audio_handles_missing_input():
    assert "No recording" in analyze_audio(None, sensitivity=0.35)["status"]