def chunked(iterable, size):
    chunk = []

    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


if __name__ == "__main__":
    print(list(chunked(range(10), 3)))
    print(list(chunked("abcdefgh", 3)))