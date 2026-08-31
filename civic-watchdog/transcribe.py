from threading import Lock

from faster_whisper import WhisperModel

# Use the smallest viable Whisper model for a free/demo deployment.
# This reduces RAM use substantially; the tradeoff is lower transcription quality.
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
transcription_lock = Lock()

def transcribe_meeting(file_path: str):
    """
    Transcribes municipal audio locally using faster-whisper.
    """
    print(f"Transcribing {file_path}...")
    with transcription_lock:
        segments, info = whisper_model.transcribe(file_path, beam_size=5)

        # Force the generator to evaluate before another transcription starts.
        return list(segments)