"""Input parsers — bytes/text → forge IR.

Each parser is a single `parse(source: str | bytes, source_uri: str) -> Model`
function. The CLI / server picks a parser based on file extension or content
sniffing and hands it the raw bytes from whichever Source adapter loaded them.
"""
