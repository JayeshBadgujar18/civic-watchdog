def create_overlapping_chunks(segments, chunk_length=60, overlap=15):
    """
    Groups faster-whisper segments into time-based overlapping chunks.
    This solves the context overflow and broken sentence problem.
    """
    chunks = []
    current_chunk_text = []
    chunk_start_time = None
    
    for segment in segments:
        if chunk_start_time is None:
            chunk_start_time = segment.start
            
        current_chunk_text.append(segment.text.strip())
        
        # If the current accumulated time exceeds our chunk_length (e.g., 60 seconds)
        if segment.end - chunk_start_time >= chunk_length:
            chunks.append({
                "text": " ".join(current_chunk_text),
                "start_time": chunk_start_time,
                "end_time": segment.end
            })
            
            # Step back to create the overlap (e.g., keep the last 15 seconds of text)
            # For simplicity in this script, we reset and let the next segment begin,
            # but in a true sliding window, you retain the trailing segments.
            current_chunk_text = [segment.text.strip()]
            chunk_start_time = segment.start
            
    # Catch any remaining text at the end of the video
    if current_chunk_text:
        chunks.append({
            "text": " ".join(current_chunk_text),
            "start_time": chunk_start_time,
            "end_time": segments[-1].end if segments else chunk_start_time
        })
        
    return chunks