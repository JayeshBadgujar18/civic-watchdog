from config import (
    CHUNK_LENGTH_SECONDS,
    CHUNK_OVERLAP_SECONDS,
    TEXT_CHUNK_OVERLAP,
    TEXT_CHUNK_SIZE,
)


def create_overlapping_chunks(
    segments,
    chunk_length=CHUNK_LENGTH_SECONDS,
    overlap=CHUNK_OVERLAP_SECONDS,
):
    """
    Groups faster-whisper segments into time-based overlapping chunks.
    This solves the context overflow and broken sentence problem.
    """
    segments = sorted(segments, key=lambda segment: segment.start)
    if not segments:
        return []
    if overlap < 0 or overlap >= chunk_length:
        raise ValueError("overlap must be >= 0 and smaller than chunk_length")

    chunks = []
    step = chunk_length - overlap
    first_start = segments[0].start
    final_end = segments[-1].end
    chunk_start = first_start

    while chunk_start < final_end:
        chunk_end = chunk_start + chunk_length
        window_segments = [
            segment for segment in segments
            if segment.start < chunk_end and segment.end > chunk_start
        ]
        if window_segments:
            chunks.append({
                "text": " ".join(segment.text.strip() for segment in window_segments),
                "start_time": chunk_start,
                "end_time": min(chunk_end, final_end),
            })
        chunk_start += step

    return chunks


def create_text_chunks(text, chunk_size=TEXT_CHUNK_SIZE, overlap=TEXT_CHUNK_OVERLAP):
    """Split long transcript text into overlapping retrieval-sized chunks."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start
        characters = 0
        while end < len(words):
            next_size = characters + len(words[end]) + (1 if end > start else 0)
            if next_size > chunk_size and end > start:
                break
            characters = next_size
            end += 1
        chunks.append({
            "text": " ".join(words[start:end]),
            "start_time": 0,
            "end_time": 0,
        })
        if end == len(words):
            break
        overlap_words = 0
        overlap_characters = 0
        while end - overlap_words - 1 >= start and overlap_characters < overlap:
            overlap_words += 1
            overlap_characters += len(words[end - overlap_words]) + 1
        start = max(start + 1, end - overlap_words)

    return chunks