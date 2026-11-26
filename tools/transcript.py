"""Get the spoken words of a video, with times.

  python tools/transcript.py <YouTube URL | video file> <output json>

1. YouTube URL: the video's own captions (pip install youtube-transcript-api), manual
   captions first, then auto-generated; Hindi or English.
2. Video file: local speech-to-text with faster-whisper (pip install faster-whisper),
   if installed. Slow on a laptop CPU (roughly the video's length or more).
   Also measures the sound itself with ffmpeg (no Python package needed), in "audio":
   has_audio (is there an audio track), duration_s, silent_s (quieter than -50 dB),
   speech_s (time covered by speech segments; null without faster-whisper) and
   other_sound_s (sound that is neither speech nor silence: music or effects).
   With onnxruntime installed, the sound is also tagged by YAMNet (Google's AudioSet tagger,
   521 sound classes; model downloaded once into tools/models/): "tags" gives the seconds
   heard as speech, music and singing, so music is detected, not guessed.
Writes {"source": .., "language": .., "segments": [{"start": .., "end": .., "text": ..}], "audio": {..}}.
Use the video file that frames.py saved (media/<id>/video.mp4) to get both words and sound.
If no route works, it exits with a message: mark audio parameters as not visible.
The agent translates Hindi / Hinglish lines itself and keeps the original text.
"""
import json, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

import numpy as np

YAMNET_URL = "https://huggingface.co/andrelgomes/yamnet-onnx/resolve/main/yamnet.onnx"
YAMNET_CLASSES = {"speech": 0, "singing": 27, "music": 132}  # AudioSet class indices
YAMNET_HOP_S = 0.48  # one score row per 0.48 s of sound
TAG_THRESHOLD = 0.3


def youtube(url):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        sys.exit("youtube-transcript-api not installed (pip install youtube-transcript-api)")
    vid = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
    if not vid:
        sys.exit("no YouTube video id in the URL")
    try:
        t = YouTubeTranscriptApi().fetch(vid.group(1), languages=["en", "en-IN", "hi"])
    except Exception as e:
        sys.exit(f"no captions available: {type(e).__name__}")
    segs = [{"start": round(s.start, 2), "end": round(s.start + s.duration, 2), "text": s.text} for s in t]
    return {"source": "youtube captions", "language": t.language_code, "segments": segs}


def sound(path):
    """Audio track facts from ffprobe/ffmpeg, or None when ffmpeg is not installed."""
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        return None
    probe = lambda *a: subprocess.run(["ffprobe", "-v", "error", *a, "-of", "csv=p=0", path],
                                      capture_output=True, text=True).stdout.strip()
    duration = float(probe("-show_entries", "format=duration") or 0)
    if not probe("-select_streams", "a", "-show_entries", "stream=index"):
        return {"has_audio": False, "duration_s": round(duration, 2), "silent_s": round(duration, 2)}
    log = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-50dB:d=0.5", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    silent = sum(min(e, duration) - s for s, e in zip(starts, ends + [duration] * (len(starts) - len(ends))))
    return {"has_audio": True, "duration_s": round(duration, 2), "silent_s": round(max(silent, 0), 2)}


def yamnet_session():
    try:
        import onnxruntime
    except ImportError:
        return None
    path = Path(__file__).resolve().parent / "models" / "yamnet.onnx"
    if not path.exists():
        try:
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(urllib.request.urlopen(YAMNET_URL, timeout=120).read())
        except OSError:
            return None
    return onnxruntime.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def tag_sound(wave, session):
    """Seconds of speech, music and singing in a 16 kHz mono waveform (YAMNet scores >= 0.3)."""
    scores = session.run(None, {session.get_inputs()[0].name: wave.astype(np.float32)})[0]
    return {f"{name}_s": round(float((scores[:, i] >= TAG_THRESHOLD).sum() * YAMNET_HOP_S), 2)
            for name, i in YAMNET_CLASSES.items()}


def pcm16k(path):
    """The sound as a 16 kHz mono float32 waveform, decoded by ffmpeg."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def tags(path):
    session = yamnet_session()
    if session is None:
        return None
    wave = pcm16k(path)
    return {**tag_sound(wave, session), "detector": "yamnet"} if len(wave) else None


def video_file(path):
    audio = sound(path)
    if audio and not audio["has_audio"]:
        return {"source": "no audio track", "language": None, "segments": [], "audio": audio}
    if audio:
        audio["tags"] = tags(path)  # null when onnxruntime or the model is missing
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        if audio is None:
            sys.exit("neither faster-whisper nor ffmpeg is installed - mark audio parameters as not visible")
        # sound facts without words
        return {"source": "ffmpeg only (faster-whisper not installed: words not transcribed)", "language": None,
                "segments": [], "audio": {**audio, "speech_s": None, "other_sound_s": None}}
    model = WhisperModel("small", device="cpu", compute_type="int8")
    # Decode with ffmpeg ourselves: faster-whisper's own decoder (PyAV) breaks on newer PyAV versions.
    wave = pcm16k(path) if audio else None
    # condition_on_previous_text=False: with it on, Whisper can stop decoding mid-video (C1-1, boat run).
    segs, info = model.transcribe(wave if wave is not None and len(wave) else path, vad_filter=True,
                                  condition_on_previous_text=False)
    segments = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
    if audio:
        speech = round(sum(s["end"] - s["start"] for s in segments), 2)
        audio = {**audio, "speech_s": speech,
                 "other_sound_s": round(max(audio["duration_s"] - audio["silent_s"] - speech, 0), 2)}
    return {"source": "faster-whisper small", "language": info.language if segments else None,
            "segments": segments, "audio": audio}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    src = sys.argv[1]
    data = youtube(src) if re.match(r"https?://(www\.|m\.)?(youtube\.com|youtu\.be)/", src) else video_file(src)
    Path(sys.argv[2]).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(data['segments'])} segments ({data['source']}, {data['language']}) -> {sys.argv[2]}")
