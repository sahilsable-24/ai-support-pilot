


def chunk_text(
        pages: list[tuple[int,str]],
        chunk_size: int=500,
        overlap: int=50,
) -> list[dict]:

    chunks = []
    chunk_index = 0

    for page_number,text in pages:
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk_content = text[start:end]

            chunks.append({
                "page": page_number,
                "content": chunk_content,
                "chunk_index": chunk_index
            })

            chunk_index += 1

            start += chunk_size - overlap

    return chunks