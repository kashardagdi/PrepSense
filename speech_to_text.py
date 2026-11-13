"""Local speech-to-text transcription for PrepSense interview answers."""

from functools import lru_cache
from pathlib import Path
import re
import tempfile
from typing import Any
import numpy as np


@lru_cache(maxsize=1)
def _load_whisper_model():
    """Load one cached multilingual Whisper model on CPU using INT8."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError(
            "Voice transcription requires faster-whisper. "
            "Install it with: python -m pip install faster-whisper"
        ) from error

    # CPU INT8 avoids competing with the local Qwen model for GPU memory.
    return WhisperModel("base", device="cpu", compute_type="int8")


# Well-known silence hallucination phrases Whisper produces when given silence or noise
HALLUCINATED_PHRASES = {
    "you", "you.", "you!", "you?", "you guys",
    "thank you", "thank you.", "thank you!", "thanks", "thanks.",
    "thanks for watching", "thanks for watching.",
    "thank you for watching", "thank you for watching.",
    "subtitles by", "subtitles by the amara.org community",
    "bye", "bye.", "goodbye", "goodbye.",
    "...", "applause", "[applause]",
}


def transcribe_audio(
    audio_file: Any,
    language: str | None = None
) -> dict:
    """
    Transcribe a Streamlit UploadedFile or file-like audio recording.

    Applies peak volume normalization to ensure quiet microphone recordings
    are clearly audible to the Whisper acoustic model, and filters out
    spurious silence hallucinations (e.g. 'You', 'Thank you').

    Returns:
        {
            "text": str,
            "language": str,
            "language_probability": float
        }
    """
    if audio_file is None:
        raise ValueError("No audio recording was supplied.")

    # Read audio bytes from the supplied object.
    if hasattr(audio_file, "getvalue"):
        audio_bytes = audio_file.getvalue()

    elif hasattr(audio_file, "read"):
        if hasattr(audio_file, "seek"):
            audio_file.seek(0)
        audio_bytes = audio_file.read()

    elif isinstance(audio_file, (bytes, bytearray)):
        audio_bytes = bytes(audio_file)

    else:
        raise TypeError(
            "Audio must be a Streamlit upload or file-like object."
        )

    if not audio_bytes:
        raise ValueError("The audio recording is empty (0 bytes).")

    temporary_path = None

    # Preserve file extension if available (e.g. .mp3, .m4a, .webm, .wav)
    suffix = ".wav"
    if hasattr(audio_file, "name") and audio_file.name:
        ext = Path(audio_file.name).suffix.lower()
        if ext in (".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".aac"):
            suffix = ext

    try:
        # Save recording to a temporary audio file.
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False
        ) as temp_file:
            temp_file.write(audio_bytes)
            temporary_path = Path(temp_file.name)

        from faster_whisper import decode_audio

        # Decode audio to 16kHz float32 mono array
        try:
            audio_data = decode_audio(str(temporary_path), sampling_rate=16000)
        except Exception as decode_err:
            raise ValueError(f"Could not decode audio format: {decode_err}") from decode_err

        if len(audio_data) == 0:
            raise ValueError("The audio recording contains no audio frames.")

        peak = float(np.max(np.abs(audio_data)))

        # Digital silence check: if peak amplitude is essentially 0, mic is muted or not sending data
        if peak < 0.003:
            raise ValueError(
                "The recording appears completely silent. "
                "Please verify your microphone is not muted and is selected as the default input device."
            )

        # Peak normalization: boost audio to 0.90 (-1 dBFS) so quiet microphones are clearly audible
        normalized_audio = (audio_data / peak) * 0.90

        model = _load_whisper_model()

        # Run transcription with VAD filter, greedy temperature 0.0, and hallucination suppression
        segments, info = model.transcribe(
            normalized_audio,
            language=language or "en",
            temperature=0.0,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400, speech_pad_ms=300),
            hallucination_silence_threshold=2.0,
            condition_on_previous_text=False,
        )

        text = " ".join(segment.text.strip() for segment in segments).strip()

        # Check for silence hallucinations
        cleaned = re.sub(r"[^\w\s]", "", text).lower().strip()
        words = cleaned.split()

        is_hallucination = (
            cleaned in HALLUCINATED_PHRASES
            or (words and all(w in ("you", "thank", "thanks", "bye") for w in words))
        )

        if is_hallucination or not text:
            raise ValueError(
                "No clear speech was detected. "
                "Please speak closer to the microphone and make sure your microphone input volume is turned up in Windows Settings."
            )

        return {
            "text": text,
            "language": getattr(info, "language", "en") or "en",
            "language_probability": float(
                getattr(info, "language_probability", 0.0) or 0.0
            ),
        }

    finally:
        # Remove temporary audio file after transcription
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
