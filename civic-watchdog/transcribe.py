from threading import Lock

from faster_whisper import WhisperModel #[cite: 1]

whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
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