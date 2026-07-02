"""The page shell: fixed nav, share row, and the HTML frame every page renders through."""

from __future__ import annotations

from urllib.parse import quote

from .common import DEFAULT_DESC, PAGE_DESC, VERSION, _canonical_url, esc
from .theme import JSONLD

NAV = [
    ("index.html", "Home"),
    ("search.html", "Search"),
    ("library.html", "Library"),
    ("canon-50.html", "Canon 50"),
    ("papers.html", "Papers"),
    ("frontier.html", "Frontier"),
    ("models.html", "Models"),
    ("voices.html", "Voices"),
    ("organizations.html", "Organizations"),
    ("platforms.html", "Platforms"),
    ("method.html", "Method"),
    ("challenges.html", "Challenges"),
    ("changelog.html", "Changelog"),
    ("data.html", "Data & audit"),
    ("about.html", "About"),
    ("press.html", "Press"),
]

# --- share row (inline SVG, CSP-safe: no external requests, no inline script) ---
SHARE_URL = "https://ai-canon.apparens.nl/"
SHARE_TEXT = ("The AI Canon: a free, public reference library for AI knowledge. "
              "It ranks texts, not people, and you can check every call.")
GITHUB_REPO = "https://github.com/Apparens/ai-canon"
# Brand glyphs (simple-icons paths, CC0) sized to a 24x24 viewBox; envelope is generic.
_ICONS = {
    "x": "M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.153h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z",
    "linkedin": "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z",
    "github": "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222 0 1.606-.014 2.898-.014 3.293 0 .322.216.694.825.576C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
    "email": "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4-8 5-8-5V6l8 5 8-5z",
}


def _icon(name):
    return (f'<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" '
            f'focusable="false"><path d="{_ICONS[name]}"/></svg>')


def share_row(prefix="", label="Share"):
    u, t = quote(SHARE_URL, safe=""), quote(SHARE_TEXT, safe="")
    links = [
        (f"https://x.com/intent/tweet?text={t}&url={u}", "x", "Share on X"),
        (f"https://www.linkedin.com/sharing/share-offsite/?url={u}", "linkedin", "Share on LinkedIn"),
        (f"mailto:?subject={quote('The AI Canon', safe='')}&body={t}%20{u}", "email", "Share by email"),
        (GITHUB_REPO, "github", "View the source on GitHub"),
    ]
    items = "".join(f'<a href="{href}" target="_blank" rel="noopener noreferrer" '
                    f'aria-label="{esc(lab)}" title="{esc(lab)}">{_icon(ic)}</a>'
                    for href, ic, lab in links)
    return f'<p class="share"><span class="share-l">{esc(label)}</span>{items}</p>'


def _nav(active: str, prefix: str) -> str:
    links = []
    for href, label in NAV:
        if href == "index.html":
            continue  # Home is the logo/wordmark
        cur = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{prefix}{href}"{cur}>{esc(label)}</a>')
    return f"""<nav class="top">
  <div class="row1">
    <div class="brandwrap">
      <a class="brand-logo" href="https://apparens.nl" title="Back to Apparens"><img src="{prefix}apparens-logo-white.png" alt="Apparens" width="510" height="118"></a>
      <a class="brand-name" href="{prefix}index.html">The AI Canon</a>
    </div>
    <a class="out" href="https://apparens.nl">Back to Apparens &#8594;</a>
  </div>
  <div class="row2">{"".join(links)}</div>
</nav>"""


def shell(active: str, kicker: str, title: str, body: str, *, depth: int = 0,
          canonical: str | None = None, description: str | None = None,
          og_type: str = "website") -> str:
    prefix = "../" * depth
    head_title = esc(title) if title == "The AI Canon" else esc(title) + " - The AI Canon"
    path = canonical if canonical is not None else active
    url = _canonical_url(path)
    desc = esc(description or PAGE_DESC.get(path, DEFAULT_DESC))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{head_title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{esc(url)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="The AI Canon">
<meta property="og:title" content="{head_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="https://ai-canon.apparens.nl/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The AI Canon. A reference library you can check. It ranks texts, not people. AI-modified cover image, labelled on the card.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{head_title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://ai-canon.apparens.nl/assets/og.png">
<link rel="stylesheet" href="{prefix}assets/fonts.css">
<link rel="stylesheet" href="{prefix}assets/canon.css">
<script type="application/ld+json">{JSONLD}</script>
</head><body>
{_nav(active, prefix)}
<header class="h"><div class="measure"><span class="overline">{esc(kicker)}</span><h1>{esc(title)}</h1></div></header>
<main><div class="measure">{body}</div></main>
<footer><div class="measure">
<p>The AI Canon, a public research initiative by <a href="https://apparens.nl">Apparens</a>, creator of the <a href="https://apparens.nl/app/ai-control-index">AI Control Index</a> app. Release <b class="rel">{esc(VERSION)}</b>. Challenge anything: <a href="mailto:office@apparens.nl">office@apparens.nl</a></p>
<p class="motto">Nothing is for sale. Nothing is hidden. Nothing is final.</p>
{share_row(prefix)}
<p class="fine">No cookies. No third-party tracking. No ads, affiliates, or sponsored placement, ever. The site is generated statically from the canonical JSON; the only inbound data path is the challenge mailbox. Code MIT; data CC BY 4.0 (verbatim paper abstracts excepted; those remain their authors').</p>
<p class="fine">AI use: ranks are computed, not generated. Voice biographies, many book descriptions, and the papers' one-line significance notes are AI-drafted from public sources, neutral and factual; the research frontier map comes from an AI-run, human-checked review; the cover image is AI-modified, labelled on the card. <a href="{prefix}method.html#how-made">How this was made</a>.</p>
</div></footer>
</body></html>
"""
