def create_overlapping_chunks(segments, chunk_length=60, overlap=15):
    """
    Groups faster-whisper segments into time-based overlapping chunks.
    This solves the context overflow and broken sentence problem.
    """
    segments = list(segments)
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