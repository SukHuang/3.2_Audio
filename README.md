---
title: Signal Watch
emoji: sound
colorFrom: teal
colorTo: yellow
sdk: gradio
app_file: app.py
---

# Signal Watch

Signal Watch is a Track B audio application. It accepts a short microphone recording,
uses Python DSP to find the dominant frequency and relative loudness, plots the frequency
spectrum, and flags recordings whose signal exceeds the selected sensitivity.

Live Space: `https://huggingface.co/spaces/<your-account>/<your-space>`

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open the local Gradio URL, allow microphone access, record a short clip, and select
**Analyze recording**. The app also keeps a session event log and offers a CSV export.

## How it works

The waveform is normalized and transformed with a fast Fourier transform (FFT). The largest
spectrum peak is reported as the dominant frequency. The signal score is derived from RMS
amplitude and the sensitivity slider, so it is a relative indicator rather than a calibrated
decibel or confidence measurement. Results depend on microphone hardware, browser permissions,
background noise, and the recording length. No audio is persisted by this app.

## Verification

The CI workflow checks required files, installs dependencies, imports the app, compiles Python,
and runs the focused synthetic-tone tests before deployment. Deployment requires a GitHub Actions
repository secret named `HF_TOKEN` with write access to the target Space.