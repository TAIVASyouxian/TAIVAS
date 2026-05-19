"""Markdown export helpers for TAIVAS."""


def build_markdown_report(title, sections):
    """Build simple markdown from a title and ordered section mapping/list."""
    lines = [f"# {title}", ""]
    if isinstance(sections, dict):
        iterable = sections.items()
    else:
        iterable = sections
    for heading, body in iterable:
        lines.extend([f"## {heading}", str(body), ""])
    return "\n".join(lines).strip() + "\n"
