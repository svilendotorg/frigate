# Improvements in this fork

This branch (`feat/whisper-transcription-tuning`) tunes Frigate's audio
transcription path for noisy IP-camera audio and adds the deployment
scripts we use to run Frigate as a systemd service alongside it.

Upstream: [`blakeblackshear/frigate`](https://github.com/blakeblackshear/frigate).

---

## 1. Whisper transcription tuning

### a) `afftdn + loudnorm` denoise filter on audio extraction

**File**: `frigate/util/audio.py`

Adds the FFmpeg `afftdn` (FFT-based denoiser) and `loudnorm` (EBU R128
loudness normaliser) filters to the audio extraction pipeline that feeds
Whisper. IP-camera audio is typically low-bitrate, hum-prone, and AGC-
modulated — significantly improves transcription accuracy on real-world
camera streams.

### b) Tuned post-processor

**File**: `frigate/data_processing/post/audio_transcription.py`

- Model: `Systran/faster-whisper-medium` (was `tiny` / `base` upstream)
- `vad_filter=False` — Whisper's VAD silences quiet / distant speech that
  IP cameras pick up
- `no_speech_threshold=None` — disables the decoder's internal silence
  gate, which over-aggressively suppresses faint speech

Net effect: fewer false negatives on quiet voices and outdoor camera
audio.

---

## 2. Deployment glue

`deploy/` directory (new):

| File | Destination | Purpose |
|------|-------------|---------|
| `deploy/frigate.service` | `/etc/systemd/system/frigate.service` | Run Frigate via systemd with EnvironmentFile-based config |
| `deploy/frigate-auto-transcribe.py` | `/opt/frigate-auto-transcribe.py` | Polls the Frigate API, kicks off transcription on new recordings |
| `deploy/frigate-auto-transcribe.service` | `/etc/systemd/system/frigate-auto-transcribe.service` | systemd unit for the above |
| `deploy/README.md` | — | install + ENV reference |

The auto-transcribe sidecar replaces an earlier MQTT-based trigger with
API polling (more reliable when MQTT broker is restarted; survives Frigate
API ramp-up via a 120 s ready-check loop).

---

## How to install this fork

```bash
git clone https://github.com/svilendotorg/frigate
cd frigate
# build / run the same way you'd run upstream Frigate
```

Default branch is `feat/whisper-transcription-tuning`, so the clone lands
on the patched code automatically.

To track upstream:

```bash
git remote add upstream https://github.com/blakeblackshear/frigate.git
git fetch upstream
git rebase upstream/dev
git push --force-with-lease
```

Note: upstream's primary development branch is `dev`, not `master`.
