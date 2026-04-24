# Frigate Custom Deployment

Custom patches and deployment scripts for Frigate NVR on Proxmox LXC.

## Patches

### `frigate/util/audio.py`
Adds `afftdn+loudnorm` denoise filter to ffmpeg audio extraction before transcription.
Significantly improves Whisper accuracy on noisy IP camera audio.

### `frigate/data_processing/post/audio_transcription.py`
- Model: `medium` (Systran/faster-whisper-medium)
- `vad_filter=False` — VAD silences quiet/distant speech on camera audio
- `no_speech_threshold=None` — disables decoder's internal silence gate

## Files

| File | Destination |
|------|-------------|
| `deploy/frigate-auto-transcribe.py` | `/opt/frigate-auto-transcribe.py` |
| `deploy/frigate-auto-transcribe.service` | `/etc/systemd/system/frigate-auto-transcribe.service` |
| `deploy/frigate.service` | `/etc/systemd/system/frigate.service` |

## Environment Variables

All secrets go in `/etc/frigate.env` (not committed to git):

```env
FRIGATE_MQTT_HOST=<mqtt-hostname>
FRIGATE_MQTT_PORT=1883
FRIGATE_MQTT_USER=<mqtt-username>
FRIGATE_MQTT_PASSWORD=<mqtt-password>
FRIGATE_CAMERA_PASSWORD=<camera-password>
FRIGATE_API_URL=http://127.0.0.1:5000
```

## Deployment

```bash
# 1. Copy service files
cp deploy/frigate-auto-transcribe.py /opt/frigate-auto-transcribe.py
cp deploy/frigate-auto-transcribe.service /etc/systemd/system/
cp deploy/frigate.service /etc/systemd/system/

# 2. Populate /etc/frigate.env with secrets (see above)

# 3. Apply source patches (re-apply after Frigate upgrade)
cp frigate/util/audio.py /opt/frigate/frigate/util/audio.py
cp frigate/data_processing/post/audio_transcription.py \
   /opt/frigate/frigate/data_processing/post/audio_transcription.py

# 4. Enable and start services
systemctl daemon-reload
systemctl enable --now frigate frigate-auto-transcribe
```

## Frigate Config

`/config/config.yml` uses `{FRIGATE_*}` substitution for secrets.
See `/config/.gitignore` — `secrets.yaml` is excluded if present.

## Notes

- `model_cache/` is at `/config/model_cache/` — not committed
- Whisper medium downloads automatically on first start (~1.4 GB)
- GPU inference via CUDA — requires NVIDIA driver passthrough in LXC
