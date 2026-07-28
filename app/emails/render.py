from pathlib import Path
from string import Template

# app/emails/templates/ — every .html file in here is addressable by name.
TEMPLATES_DIR = Path(__file__).parent / "templates"


def render(template_name: str, **context) -> str:
    """Load templates/<template_name>.html and substitute $placeholders.

    Uses string.Template ($reset_link) instead of str.format ({reset_link})
    because HTML/CSS is full of literal braces that format() would choke on.
    substitute() (not safe_substitute) raises if a placeholder is missing —
    a typo in a template fails loudly instead of sending a broken email.
    """
    html = (TEMPLATES_DIR / f"{template_name}.html").read_text(encoding="utf-8")
    return Template(html).substitute(**context)
