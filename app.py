"""Live microphone audio analyzer for a Hugging Face Gradio Space."""

from __future__ import annotations

import csv
import io
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gradio as gr
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def analyze_audio(audio: str | tuple[int, np.ndarray] | None, sensitivity: float) -> dict[str, Any]:
    """Extract dominant frequency and energy from a recorded audio clip."""
    if audio is None:
        return {"status": "No recording yet. Start the microphone and record a short clip."}

    if isinstance(audio, tuple):
        sample_rate, samples = audio
    else:
        import wave

        with wave.open(str(audio), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            samples = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)

    samples = np.asarray(samples, dtype=np.float32)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if samples.size == 0 or sample_rate <= 0:
        return {"status": "The recording was empty or could not be read."}

    samples /= max(float(np.max(np.abs(samples))), 1.0)
    rms = float(np.sqrt(np.mean(samples**2)))
    decibels = 20 * math.log10(max(rms, 1e-6))
    window = np.hanning(samples.size)
    spectrum = np.abs(np.fft.rfft(samples * window))
    frequencies = np.fft.rfftfreq(samples.size, 1 / sample_rate)
    peak_index = int(np.argmax(spectrum[1:]) + 1) if spectrum.size > 1 else 0
    dominant_frequency = float(frequencies[peak_index])
    score = min(100.0, max(0.0, 100 * (rms / max(sensitivity, 0.01))))
    alert = score >= 100.0

    return {
        "status": "SPIKE ALERT: unusually loud signal" if alert else "Signal within the selected range",
        "sample_rate": int(sample_rate),
        "duration": samples.size / sample_rate,
        "rms": rms,
        "decibels": decibels,
        "frequency": dominant_frequency,
        "score": score,
        "alert": alert,
        "frequencies": frequencies,
        "spectrum": spectrum,
    }


def render_result(audio: Any, sensitivity: float, history: list[dict[str, Any]] | None):
    result = analyze_audio(audio, sensitivity)
    history = history or []
    if "score" not in result:
        return None, result["status"], history, None

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    history = history + [{
        "time": timestamp,
        "frequency_hz": round(result["frequency"], 1),
        "level_db": round(result["decibels"], 1),
        "score": round(result["score"], 1),
        "alert": "YES" if result["alert"] else "no",
    }]
    figure, axis = plt.subplots(figsize=(9, 3.5))
    axis.plot(result["frequencies"], result["spectrum"], color="#0f766e", linewidth=1)
    axis.set(xlim=(0, min(result["sample_rate"] / 2, 8000)), xlabel="Frequency (Hz)", ylabel="Magnitude")
    axis.grid(alpha=0.2)
    figure.tight_layout()
    message = (
        f"### {result['status']}\n"
        f"Dominant frequency: **{result['frequency']:.1f} Hz** | "
        f"Level: **{result['decibels']:.1f} dBFS** | "
        f"Signal score: **{result['score']:.0f}/100**"
    )
    return figure, message, history, export_history(history)


def export_history(history: list[dict[str, Any]] | None):
    if not history:
        return None
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=history[0].keys())
    writer.writeheader()
    writer.writerows(history)
    export_path = Path(tempfile.gettempdir()) / "audio-analyzer-events.csv"
    export_path.write_text(output.getvalue(), encoding="utf-8", newline="")
    return str(export_path)


with gr.Blocks(title="Signal Watch") as demo:
    gr.Markdown("# Signal Watch\nA small microphone signal monitor for frequency and volume spikes.")
    history_state = gr.State([])
    with gr.Row():
        microphone = gr.Audio(sources=["microphone"], type="filepath", label="Record a sample")
        sensitivity = gr.Slider(0.05, 1.0, value=0.35, step=0.05, label="Alert sensitivity")
    analyze_button = gr.Button("Analyze recording", variant="primary")
    status = gr.Markdown("Record a clip to begin.")
    spectrum_plot = gr.Plot(label="Frequency spectrum")
    gr.Markdown("## Event log")
    events = gr.Dataframe(headers=["time", "frequency_hz", "level_db", "score", "alert"], label="Recent analyses")
    download = gr.File(label="CSV export")
    gr.Markdown(
        "## How it works\n"
        "The app normalizes the microphone waveform, calculates a fast Fourier transform, "
        "and reports the strongest frequency. The score is a relative RMS loudness indicator, "
        "not a calibrated sound-level measurement. Browser permission, background noise, and "
        "microphone hardware affect the result."
    )
    analyze_button.click(
        render_result,
        inputs=[microphone, sensitivity, history_state],
        outputs=[spectrum_plot, status, history_state, download],
    ).then(lambda rows: rows, inputs=history_state, outputs=events)


if __name__ == "__main__":
    demo.launch()