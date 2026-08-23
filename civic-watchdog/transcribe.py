from faster_whisper import WhisperModel #[cite: 1]

def transcribe_meeting(file_path: str):
    """
    Transcribes municipal audio locally using faster-whisper.
    """
    # Using the base model on CPU for local development
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    print(f"Transcribing {file_path}...")
    segments, info = model.transcribe(file_path, beam_size=5)
    
    # Force the generator to evaluate and return a list of segments
    return list(segments)