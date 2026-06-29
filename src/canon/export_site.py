"""Stage C - static site generator (CAN-21..25).

Reads data/releases/<version>/ + data/seeds/ + scenarios.yaml + CHANGELOG.md and
emits plain, framework-free HTML into site/. The whole public site is generated
from the canonical JSON: there is no app server and no live database, so nothing
can leak or be injected (master doc, Part V). Output is deterministic.

The visual language mirrors apparens.nl (apparens-design-system.css): deep-blue
fixed nav with the white wordmark, white body, orange #B8430A accents, DM Serif
Display headings, DM Sans body. House style: no em-dashes in copy.

Pages generated (the homepage is generated too, in the same design):
  index.html             the manifesto + the live Canon-50 teaser
  canon-50.html          three scenario views; each rank links to its breakdown
  work/<id>.html         the per-work trust surface (every metric + provenance)
  papers.html            all 162 papers, honest about scored-vs-seed status
  method.html            the 8 rules, ontology, weighting scenarios, missing-data rule
  challenges.html        the challenge protocol + log (the differentiator; empty for now)
  changelog.html         rendered from CHANGELOG.md
  data.html              the downloadable audit package + one-command reproduce
  audit/                 copied release + seed JSON (openly downloadable)
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

import yaml

from . import METHOD_VERSION, ONTOLOGY_VERSION

_ROOT = Path(__file__).resolve().parents[2]
SITE = _ROOT / "site"
SEEDS = _ROOT / "data" / "seeds"
RELEASES = _ROOT / "data" / "releases"
VERSION = "pilot-v0.1"

NAV = [
    ("index.html", "Home"),
    ("search.html", "Search"),
    ("library.html", "Library"),
    ("canon-50.html", "Canon 50"),
    ("papers.html", "Papers"),
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

# The verbatim positioning line (A2) and humility clause (E5), used as-is.
CONCEPT_DOI = "10.5281/zenodo.21042034"  # always resolves to the latest method version
POSITIONING = ("The AI Canon is a free, method-backed reference library for AI "
               "knowledge. It ranks texts, not people. It invites correction. It sells nothing.")
HUMILITY = ("A rank is not a verdict on intrinsic worth. It is a transparent output of "
            "declared evidence, weights, and missing-data rules at a specific release date.")

_STYLE = """
:root{--deep:#051C2C;--navy:#0A2540;--mid:#1A3A5C;--white:#fff;--g100:#F5F5F5;
--g200:#EAEAEA;--g300:#D4D4D4;--g500:#6B6B6B;--g700:#333;--ice:#E8F0FE;--cream:#F5F0E8;
--orange:#B8430A;--orange-hover:#9E3908;--orange-dark:#E65710;--teal:#135975}
*{margin:0;padding:0;box-sizing:border-box}
html{font-size:18px;-webkit-font-smoothing:antialiased;scroll-behavior:smooth}
body{font-family:"DM Sans",-apple-system,BlinkMacSystemFont,sans-serif;color:var(--g700);
background:var(--white);line-height:1.5;padding-top:86px}
[id]{scroll-margin-top:96px}
.measure{max-width:1080px;margin:0 auto;padding:0 32px}
/* Body links are underlined so they are distinguishable without relying on color
   (WCAG 1.4.1). Nav, brand, pills, and table-cell links opt out below. */
a{color:var(--orange);text-decoration:underline}
a:hover{color:var(--orange-hover)}
:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
/* fixed two-tier nav */
nav.top{position:fixed;top:0;left:0;right:0;z-index:100;background:var(--deep);
border-bottom:1px solid rgba(255,255,255,.08)}
nav.top .row1{max-width:1080px;margin:0 auto;padding:0 32px;height:50px;display:flex;
align-items:center;justify-content:space-between}
nav.top .brandwrap{display:flex;align-items:center;gap:11px}
nav.top .brand-logo img{height:26px;width:auto;display:block}
nav.top .brand-logo,nav.top .brand-name{text-decoration:none}
nav.top .brand-logo:hover,nav.top .brand-name:hover{text-decoration:none}
nav.top .brand-name{color:#fff;font-family:"DM Serif Display",serif;font-weight:400;font-size:18px}
nav.top .row1 .out{color:var(--orange-dark);font-size:.82rem;text-decoration:none;font-weight:600}
nav.top .row2{max-width:1080px;margin:0 auto;padding:0 32px;height:38px;display:flex;
flex-wrap:wrap;align-items:center;gap:22px;border-top:1px solid rgba(255,255,255,.06)}
nav.top .row2 a{font-size:.82rem;color:rgba(255,255,255,.7);text-decoration:none}
nav.top .row2 a:hover{color:#fff}
nav.top .row2 a[aria-current=page]{color:#fff;border-bottom:2px solid var(--orange-dark);padding-bottom:2px}
/* header band */
header.h{background:var(--white);padding:44px 0 26px;border-bottom:1px solid var(--g200)}
.overline{font-size:.8rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange)}
h1{font-family:"DM Serif Display",serif;font-weight:400;font-size:clamp(2rem,5vw,3rem);
line-height:1.1;letter-spacing:-.02em;margin:10px 0;color:var(--deep)}
h2{font-family:"DM Serif Display",serif;font-weight:400;font-size:1.6rem;line-height:1.25;margin:34px 0 12px;color:var(--deep)}
h3{font-size:.8rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange);margin:24px 0 8px}
p{margin:10px 0;color:var(--g700)}main{padding:30px 0 70px}
.lead{font-size:1.18rem;color:var(--g500);line-height:1.6;max-width:46ch}
.lead b{color:var(--deep);font-weight:500}
/* callout */
.note{background:var(--ice);border-left:3px solid var(--orange);padding:14px 20px;margin:20px 0;font-size:.95rem;color:var(--g700)}
.note.flag{background:#FCEEE6}
/* tables */
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:.9rem}
th{text-align:left;font-size:.7rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
color:var(--g500);border-bottom:2px solid var(--navy);padding:9px 10px}
td{padding:9px 10px;border-bottom:1px solid var(--g200);vertical-align:top;color:var(--g700)}
tr:hover td{background:var(--g100)}
td.rank,td.num{font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--g500)}
td a{color:var(--deep);font-weight:500;text-decoration:none}td a:hover{color:var(--orange)}
.tag{font-size:.68rem;padding:2px 9px;border:1px solid var(--g300);border-radius:20px;color:var(--g500);white-space:nowrap}
.flag{color:var(--orange);font-weight:600}
.scn{margin:26px 0;border:1px solid var(--g200);border-radius:6px;background:var(--white);
box-shadow:0 1px 3px rgba(0,0,0,.05);padding:6px 22px 18px}
.scn h2{margin-top:18px}
.miss{color:var(--g500)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;color:var(--g500)}
ol,ul{margin:10px 0 10px 22px}li{margin:6px 0}
/* homepage two-column + stats */
.cols{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--g200);border-radius:6px;overflow:hidden;margin:22px 0}
.cols>div{padding:22px 24px}
.cols>div:first-child{border-right:1px solid var(--g200)}
.cols ul{list-style:none;margin:8px 0 0}
.cols li{padding:8px 0;border-top:1px solid var(--g200);font-size:.92rem}
.cols li:first-child{border-top:0}
.cols .not li{color:var(--g500)}
@media(max-width:680px){.cols{grid-template-columns:1fr}.cols>div:first-child{border-right:0;border-bottom:1px solid var(--g200)}}
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--g200);border:1px solid var(--g200);border-radius:6px;overflow:hidden;margin:22px 0}
.statgrid .stat{background:#fff;padding:18px 16px}
.statgrid .stat b{display:block;font-family:"DM Serif Display",serif;font-weight:400;font-size:1.8rem;color:var(--deep);line-height:1.05}
.statgrid .stat span{font-size:.8rem;color:var(--g500)}
.pill{display:inline-block;background:var(--orange);color:#fff !important;font-size:.85rem;font-weight:600;padding:9px 18px;border-radius:3px;text-decoration:none;margin-top:6px}
.pill:hover{background:var(--orange-hover);text-decoration:none}
/* library filter bar + cards */
.filters{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0;padding:14px 16px;background:var(--g100);border:1px solid var(--g200);border-radius:6px}
.filters label{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--g500);display:flex;flex-direction:column;gap:4px}
.filters select,.filters input{font:inherit;font-size:.85rem;padding:6px 8px;border:1px solid var(--g300);border-radius:4px;background:#fff;color:var(--g700);min-width:150px}
.count{font-size:.8rem;color:var(--g500);margin:8px 0}
.entry{border-bottom:1px solid var(--g200);padding:14px 0}
.entry .t{font-family:"DM Serif Display",serif;font-size:1.1rem;color:var(--deep)}
.entry .meta{font-size:.8rem;color:var(--g500);margin:3px 0}
.entry .desc{font-size:.92rem;margin-top:6px}
.entry .bio{font-size:.9rem;color:var(--g500);margin-top:6px;max-width:72ch;line-height:1.55}
.entry .pending{font-size:.85rem;color:var(--g500);font-style:italic;margin-top:6px}
.badge{display:inline-block;font-size:.62rem;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:20px;border:1px solid var(--g300);color:var(--g500);margin-left:6px}
.shelf-cat{font-family:"DM Serif Display",serif;font-size:1.25rem;color:var(--deep);margin:30px 0 6px;border-bottom:2px solid var(--orange);display:inline-block;padding-bottom:2px}
/* global search */
.search-wrap{margin:18px 0}
#sq{width:100%;font:inherit;font-size:1.25rem;padding:16px 18px;border:1px solid var(--g300);border-radius:8px;background:#fff;color:var(--deep)}
#sq:focus{outline:2px solid var(--orange);border-color:var(--orange)}
.sresult{display:block;border-bottom:1px solid var(--g200);padding:13px 2px;text-decoration:none}
.sresult:hover{text-decoration:none;background:var(--g100)}
.sresult .st{font-family:"DM Serif Display",serif;font-size:1.1rem;color:var(--deep)}
.sresult .ss{font-size:.85rem;color:var(--g500);margin-top:2px}
.schip{display:inline-block;font-size:.62rem;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:20px;border:1px solid var(--g300);color:var(--g500);margin-left:8px;vertical-align:middle}
.pullquote{font-family:"DM Serif Display",serif;font-size:1.3rem;line-height:1.35;color:var(--deep);border-left:3px solid var(--orange);padding:4px 0 4px 18px;margin:16px 0}
.sharebox{background:var(--g100);border:1px solid var(--g200);border-radius:6px;padding:18px 22px;margin:18px 0}
.sharebox p{margin:8px 0}.sharebox ul{margin:8px 0 8px 20px}
/* footer */
footer{background:var(--deep);color:rgba(255,255,255,.78);padding:40px 0 34px;margin-top:40px;font-size:.85rem}
footer p{color:rgba(255,255,255,.82)}
footer .measure{max-width:1080px}
footer a{color:#fff}footer a:hover{color:#fff}
footer .fine{font-size:.62rem;color:rgba(255,255,255,.62);line-height:1.7;margin-top:16px;
padding-top:14px;border-top:1px solid rgba(255,255,255,.12);max-width:820px}
"""


def esc(x) -> str:
    # House style: no em-dashes in copy. Normalize at the rendering boundary so
    # even verbatim seed text (descriptions, significance lines) cannot show one.
    # html.escape(quote=True) neutralizes < > & " ' so no data field can break out
    # of text or an attribute (XSS defense in depth).
    text = html.escape(str(x if x is not None else ""), quote=True)
    return text.replace(" — ", ", ").replace("—", ", ").replace("–", "-")


# Only these URL schemes may appear in a generated href/src; anything else
# (javascript:, data:, vbscript:, file:, ...) collapses to "#". Defense in depth:
# a data-derived link (e.g. a metric's provenance_url) cannot become script.
_SAFE_SCHEMES = ("https://", "http://", "mailto:")


def safe_url(u) -> str:
    s = str(u or "").strip()
    if s.lower().startswith(_SAFE_SCHEMES):
        return s
    # Allow purely relative links (no scheme); reject any colon before the first
    # slash, which signals a scheme that is not on the allow-list.
    if ":" not in s.split("/", 1)[0]:
        return s
    return "#"


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


def shell(active: str, kicker: str, title: str, body: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    head_title = esc(title) if title == "The AI Canon" else esc(title) + " - The AI Canon"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{head_title}</title>
<meta name="description" content="The AI Canon is a free, method-backed reference library for AI knowledge. It ranks texts, not people.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The AI Canon">
<meta property="og:title" content="{head_title}">
<meta property="og:description" content="{esc(POSITIONING)}">
<meta property="og:url" content="https://ai-canon.apparens.nl/">
<meta property="og:image" content="https://ai-canon.apparens.nl/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The AI Canon. A reference library you can check. It ranks texts, not people.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{head_title}">
<meta name="twitter:description" content="{esc(POSITIONING)}">
<meta name="twitter:image" content="https://ai-canon.apparens.nl/assets/og.png">
<link rel="stylesheet" href="{prefix}assets/fonts.css">
<link rel="stylesheet" href="{prefix}assets/canon.css">
</head><body>
{_nav(active, prefix)}
<header class="h"><div class="measure"><span class="overline">{esc(kicker)}</span><h1>{esc(title)}</h1></div></header>
<main><div class="measure">{body}</div></main>
<footer><div class="measure">
<p>The AI Canon, an <a href="https://apparens.nl">Apparens</a> public research initiative. Release <b style="color:#fff;font-weight:600">{esc(VERSION)}</b>. Challenge anything: <a href="mailto:office@apparens.nl">office@apparens.nl</a></p>
<p style="margin-top:6px">Nothing is for sale. Nothing is hidden. Nothing is final.</p>
<p class="fine">No cookies. No third-party tracking. No ads, affiliates, or sponsored placement, ever. The site is generated statically from the canonical JSON; the only inbound data path is the challenge mailbox.</p>
</div></footer>
</body></html>
"""


def _write(rel_path: str, content: str) -> None:
    out = SITE / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def _load(path: Path):
    return json.loads(path.read_text("utf-8"))


def _papers_index() -> dict:
    return {p["id"]: p for p in _load(SEEDS / "papers.json")}


def _scenarios() -> dict:
    return yaml.safe_load((_ROOT / "scenarios.yaml").read_text("utf-8"))


def _teaser_rows(rankings: dict, papers: dict, n: int = 3) -> str:
    out = []
    for r in rankings.get("paper__academic", [])[:n]:
        title = esc(papers.get(r["work_id"], {}).get("canonical_title", r["work_id"]))
        out.append(
            f'<tr><td class="rank">{r["rank"]:03d}</td>'
            f'<td><a href="work/{esc(r["work_id"])}.html">{title}</a></td>'
            f'<td class="num">{esc(papers.get(r["work_id"], {}).get("year",""))}</td>'
            f'<td class="num">{r["score"]:.4f}</td>'
            f'<td class="mono">citations, recency</td></tr>'
        )
    return "".join(out)


# --- pages ------------------------------------------------------------------


def page_home(release: dict, rankings: dict, papers: dict, coverage: dict) -> str:
    teaser = _teaser_rows(rankings, papers)
    body = f"""
<p class="lead">{esc(POSITIONING)}</p>

<h2>Check the math, not the curator.</h2>
<p>Curation of AI knowledge has collapsed into affiliate listicles and opinion threads while the field itself compounds. The Canon's claim is narrow and testable: knowledge curation can be made <b>auditable, reproducible, and challengeable</b>. Which works belong to the canon of AI is decided by published method and verifiable evidence (citations, library holdings, syllabus adoption, sustained readership), never by taste alone, and never by anything money can buy.</p>
<p>The list is not the product. The method is the product. The list is its first proof.</p>

<div class="cols">
  <div><h3>The Canon is</h3><ul>
    <li>A curated, multilingual library of the books, papers, reports, and standards that define the AI field</li>
    <li>Evidence-ranked within each domain, under a published method and weights</li>
    <li>Versioned: every release tagged, every change logged, every rank movement traceable</li>
    <li>Open to challenge from anyone, with public resolutions</li>
    <li>Free, permanently</li>
  </ul></div>
  <div class="not"><h3>The Canon is not</h3><ul>
    <li>A ranking of people or companies. Voices and organizations are described, never scored</li>
    <li>A recommendation engine, a review site, or a bookstore</li>
    <li>A leaderboard across domains. A standard is never ranked against a novel</li>
    <li>Sponsored, affiliated, or advertised. No entry can be bought or featured</li>
    <li>Finished. It is maintained, corrected, and re-released</li>
  </ul></div>
</div>

<h2>The first ranking is live, and you can check the math.</h2>
<p class="note">Pilot release <b>{esc(VERSION)}</b>. It ranks the <b>papers</b> domain under three published weighting scenarios, and it survived a two-iteration adversarial review (GATE A: pass). It is deliberately narrow and honest about it: books carry no harvested metrics yet, two evidence signals are live, coverage is partial, and every gap is declared rather than zero-filled. A rank is not a verdict on worth. It is a transparent output of declared evidence, weights, and missing-data rules at this release.</p>
<table><thead><tr><th>Rank</th><th>Paper (academic view)</th><th>Year</th><th>Score</th><th>Evidence</th></tr></thead><tbody>{teaser}</tbody></table>
<p><a class="pill" href="canon-50.html">See the full Canon 50 &#8594;</a></p>

<div class="statgrid">
  <div class="stat"><b>573</b><span>candidate books (250 described)</span></div>
  <div class="stat"><b>162</b><span>seed papers, 1943-2025</span></div>
  <div class="stat"><b>184</b><span>voices, described, never ranked</span></div>
  <div class="stat"><b>133</b><span>organizations</span></div>
  <div class="stat"><b>90</b><span>platforms</span></div>
  <div class="stat"><b>172</b><span>verified authored-by edges</span></div>
</div>
<p class="note"><b>Coverage, stated plainly.</b> The corpus is strong in English. The multilingual layer is in development, and the Chinese-language spine is a known gap. We will not describe the Canon as worldwide until that gap is closed. Chinese-literate readers are invited to nominate works and contest rankings through the <a href="challenges.html">challenge protocol</a>, with evidence and with credit.</p>

<h2>Rules the ranking cannot break</h2>
<p>The full method is published with each release and is itself versioned. In brief: scoring is deterministic, every number carries its provenance, missing evidence is recorded and penalized rather than invented, domains never cross-rank, people are context and never contestants, and a rank is an output of declared evidence and weights, not a verdict on worth. Read the <a href="method.html">full method and weighting scenarios</a>.</p>

<h2>Disagreement is a feature. File it.</h2>
<p>Anyone may challenge any entry, rank, metric, category, or method rule, including ours. A challenge is contested against the cited evidence, not against opinion. Every challenge gets a public identifier and a published resolution. See the <a href="challenges.html">challenge protocol and log</a>, or download the <a href="data.html">audit package</a> and rebuild the ranking yourself.</p>

<h2>Honest about cadence. Absolute about conduct.</h2>
<p>Every update is logged. Every correction is traceable. Every ranking can be challenged. The library is maintained as capacity allows, without deadlines we would resent, and without commercial influence of any kind. What is promised without qualification: <b>no advertising, no affiliate links, no sponsored placement, no paid inclusion, ever.</b> Nothing in this library is for sale, which is precisely why it can be trusted.</p>
"""
    return shell("index.html", "An Apparens public research initiative", "The AI Canon", body)


def page_canon50(release: dict, rankings: dict, papers: dict) -> str:
    scn_doc = _scenarios()
    parts = [
        '<p class="note">Pilot release <b>%s</b>. This ranks the <b>papers</b> domain only. '
        "Books carry no harvested metrics yet. Two signals are harvested (all-time citations and "
        "recent-citation momentum); coverage is partial and every gap is declared rather than "
        "zero-filled. A rank is not a verdict on worth. It is a transparent output of declared "
        "evidence, weights, and missing-data rules at this release date.</p>" % esc(VERSION),
        f'<p class="note"><b>{esc(HUMILITY)}</b></p>',
    ]
    for scenario in sorted(scn_doc["scenarios"]):
        rows = rankings.get(f"paper__{scenario}", [])
        desc = scn_doc["scenarios"][scenario].get("description", "")
        body = [
            f'<div class="scn"><h2>{esc(scenario.replace("_", " ").title())}</h2>',
            f'<p class="mono">{esc(desc)}</p>',
            "<table><thead><tr><th>Rank</th><th>Paper</th><th>Year</th><th>Score</th><th>Evidence</th></tr></thead><tbody>",
        ]
        for r in rows:
            p = papers.get(r["work_id"], {})
            present = [c["metric"] for c in r["components"] if c.get("status") == "present"]
            ev = ", ".join(present) or "none"
            flag = ' <span class="flag" title="conflict of interest declared">&#9873;</span>' if r.get("conflict_flag") else ""
            body.append(
                f'<tr><td class="rank">{r["rank"]:03d}</td>'
                f'<td><a href="work/{esc(r["work_id"])}.html">{esc(p.get("canonical_title",""))}</a>{flag}</td>'
                f'<td class="num">{esc(p.get("year",""))}</td>'
                f'<td class="num">{r["score"]:.4f}</td>'
                f'<td class="mono">{esc(ev)}</td></tr>'
            )
        body.append("</tbody></table></div>")
        parts.append("".join(body))
    div = release.get("divergence", {}).get("paper", {})
    parts.append(
        f'<p class="note">{esc(div.get("note",""))} '
        f'Each rank links to its full score breakdown: every metric, its source, retrieval date, and weight.</p>'
    )
    return shell("canon-50.html", "Canon 50, pilot", "The Canon 50", "".join(parts))


def page_work(work_id: str, per_scenario: dict, papers: dict) -> str:
    p = papers.get(work_id, {})
    ed = p.get("editorial", {})
    head = [
        f'<p class="mono">{esc(work_id)} &middot; paper &middot; {esc(p.get("year",""))}</p>',
        f'<p>{esc(ed.get("authors",""))}</p>',
    ]
    if ed.get("significance"):
        head.append(f'<p>{esc(ed["significance"])}</p>')
    if p.get("conflict_flag"):
        head.append('<p class="note flag">Conflict of interest declared for this work.</p>')
    blocks = ["".join(head)]
    for scenario in sorted(per_scenario):
        row = per_scenario[scenario]
        blocks.append(f'<h2>{esc(scenario.replace("_"," ").title())}, score {row["score"]:.4f}</h2>')
        rows = ["<table><thead><tr><th>Metric</th><th>Status</th><th>Value</th><th>Norm.</th>"
                "<th>Weight</th><th>Contribution</th><th>Source</th><th>Confidence</th><th>Provenance</th></tr></thead><tbody>"]
        for c in row["components"]:
            if c.get("status") == "present":
                prov = c.get("provenance_url", "")
                prov_a = f'<a href="{esc(safe_url(prov))}" rel="nofollow noopener">link</a>' if prov else "none"
                rows.append(
                    f'<tr><td class="mono">{esc(c["metric"])}</td><td>present</td>'
                    f'<td class="num">{esc(c.get("value",""))}</td><td class="num">{esc(c.get("normalized",""))}</td>'
                    f'<td class="num">{esc(c.get("weight",""))}</td><td class="num">{esc(c.get("contribution",""))}</td>'
                    f'<td>{esc(c.get("source",""))}</td><td>{esc(c.get("confidence",""))}</td><td>{prov_a}</td></tr>'
                )
            else:
                rows.append(
                    f'<tr class="miss"><td class="mono">{esc(c["metric"])}</td><td>missing</td>'
                    f'<td colspan="3">recorded as missing, penalized by rule, never imputed</td>'
                    f'<td class="num">&minus;{esc(c.get("missing_data_penalty",""))}</td><td colspan="3">{esc(c.get("note",""))}</td></tr>'
                )
        rows.append("</tbody></table>")
        blocks.append("".join(rows))
    subject = f"Challenge rank: {work_id}"
    body = f"mailto:office@apparens.nl?subject={esc(subject)}"
    blocks.append(f'<p class="note"><b>{esc(HUMILITY)}</b></p>')
    blocks.append(
        f'<p class="note">Disagree with this rank or a number? <a href="{body}">Challenge it</a> '
        "with your evidence. Every challenge gets a public identifier and a published resolution.</p>"
    )
    return shell("canon-50.html", "Score breakdown", esc(p.get("canonical_title", work_id)),
                 "".join(blocks), depth=1)


def page_papers(papers: dict, scored: set) -> str:
    rows = ['<p class="note">All 162 seed papers. <b>Seed status means candidacy, not canonical '
            "status.</b> Papers with harvested evidence link to their breakdown; the rest are an "
            "honestly-declared coverage gap, not a zero.</p>",
            "<table><thead><tr><th>#</th><th>Paper</th><th>Year</th><th>Venue</th><th>Evidence</th></tr></thead><tbody>"]
    for pid in sorted(papers):
        p = papers[pid]
        ed = p.get("editorial", {})
        is_scored = pid in scored
        title = (f'<a href="work/{esc(pid)}.html">{esc(p["canonical_title"])}</a>'
                 if is_scored else esc(p["canonical_title"]))
        sig = f'<div class="meta">{esc(ed["significance"])}</div>' if ed.get("significance") else ""
        ev = '<span class="tag">scored</span>' if is_scored else '<span class="tag miss">no evidence yet</span>'
        rows.append(
            f'<tr id="{esc(pid)}"><td class="num">{esc(pid.split("-")[-1])}</td><td>{title}{sig}</td>'
            f'<td class="num">{esc(p.get("year",""))}</td><td>{esc(ed.get("venue",""))}</td><td>{ev}</td></tr>'
        )
    rows.append("</tbody></table>")
    return shell("papers.html", "Shelf", "Papers", "".join(rows))


def page_method() -> str:
    rules = [
        "Deterministic scoring. Identical inputs and weights produce identical ranks; reproducible from the audit package with one command.",
        "Provenance on every number: source, retrieved_at, confidence, licence note. A number without provenance does not exist.",
        "No silent imputation. Missing evidence is recorded as missing and penalized by a published rule, never estimated.",
        "Domains never cross-rank. Books, papers, reports, and standards are scored within their own domain.",
        "Each language ecosystem scores within itself first. Coverage gaps are declared, not hidden.",
        "People are context, not contestants. Persons, organizations, and platforms carry no score, ever.",
        "Manual decisions are records. Every override carries a written rationale and is published; Apparens-authored works are flagged.",
        "Humility on rank. A rank is a transparent output of declared evidence, weights, and missing-data rules at a release date, not a verdict on intrinsic worth.",
    ]
    scn = _scenarios()
    body = ["<h2>Rules the ranking cannot break</h2><ol>"]
    body += [f"<li>{esc(r)}</li>" for r in rules]
    body.append("</ol>")
    body.append(f'<h2>Ontology v{esc(ONTOLOGY_VERSION)} (frozen)</h2>'
                '<p>Canonical entities (book, paper, report, standard) are scored within their domain. '
                'Context entities (person, organization, platform) are described, never ranked: '
                'structurally, they carry no score field. Governance records (releases, challenges, '
                'overrides) are append-only.</p>')
    body.append("<h2>Weighting scenarios</h2>")
    metric_names = sorted({m for s in scn["scenarios"].values() for m in s["weights"]})
    head = "".join(f"<th>{esc(m)}</th>" for m in metric_names)
    body.append(f"<table><thead><tr><th>Scenario</th>{head}</tr></thead><tbody>")
    for name in sorted(scn["scenarios"]):
        w = scn["scenarios"][name]["weights"]
        cells = "".join(f'<td class="num">{esc(w.get(m,"."))}</td>' for m in metric_names)
        body.append(f'<tr><td class="mono">{esc(name)}</td>{cells}</tr>')
    body.append("</tbody></table>")
    body.append(f'<p class="note">Missing-data penalty factor: <b>{esc(scn.get("missing_data_penalty_factor"))}</b>. '
                f'Normalization: <b>{esc(scn.get("normalization"))}</b>. method_version <b>{esc(METHOD_VERSION)}</b>. '
                "These are pilot placeholder weights; every change ships with a changelog entry.</p>")
    body.append("<h2>What each signal means</h2><ul>"
                "<li><b>citation_count</b>: all-time citations from OpenAlex (CC0). The scale of scholarly impact.</li>"
                "<li><b>readership_persistence</b>: the number of distinct years a work keeps being cited "
                "(from OpenAlex counts_by_year). A longevity proxy: a work cited across many years scores "
                "higher than a one-year spike. It rewards enduring use, not recent volume.</li>"
                "<li><b>library_holdings</b>, <b>syllabus_adoptions</b>: declared but not yet harvested for "
                "the pilot (WorldCat / Open Syllabus drops pending). Works are penalized for them by rule, "
                "never imputed.</li></ul>")
    body.append("<h2>Declared deferred capabilities</h2>"
                "<p>The method names these now and does not pretend they are done. Each is deferred openly, "
                "not silently stubbed:</p><ul>"
                "<li><b>Per-ecosystem normalization (rule 5)</b>: scoring runs per domain today. Per-language "
                "normalization activates only once works from more than one ecosystem enter a scored domain. "
                "Until then the site does not claim worldwide or present-tense multilingual coverage; the "
                "Chinese spine (28 works) is a declared gap.</li>"
                "<li><b>A fuller longevity proxy</b>: library holdings over time, edition count, and continued "
                "availability, to complement readership_persistence.</li>"
                "<li><b>Book scoring</b>: books are curated and browsable now but not yet scored; the pilot "
                "ranks papers only.</li></ul>")
    body.append("<h2>Cite this method</h2>"
                f'<p>The method is documented in a citable note (<i>Corpus Cognitivum</i>), '
                f'archived with a DOI: <a href="https://doi.org/{esc(CONCEPT_DOI)}">'
                f'doi.org/{esc(CONCEPT_DOI)}</a> (concept DOI, always the latest version). '
                "It is licensed CC BY 4.0.</p>"
                "<p class=\"mono\">Janssen, J. (2026). The AI Canon: a method for auditable knowledge "
                f"curation (Corpus Cognitivum). Apparens. https://doi.org/{esc(CONCEPT_DOI)}</p>")
    return shell("method.html", "Method statement", "Method", "".join(body))


def page_challenges() -> str:
    body = (
        '<p class="note">Anyone may challenge any entry, rank, metric, category, or method rule, '
        "including ours. A challenge is contested against the cited evidence, not against opinion.</p>"
        "<h2>Protocol</h2><ol>"
        "<li>Send the target, your claim, and your evidence to <a href=\"mailto:office@apparens.nl\">office@apparens.nl</a>.</li>"
        "<li>Acknowledgement within 7 days; each challenge receives a public identifier.</li>"
        "<li>Resolution against the data: upheld challenges change the next release; rejected challenges are answered with the evidence.</li>"
        "<li>All challenges and resolutions remain visible permanently.</li></ol>"
        "<h2>Challenge log</h2>"
        '<p class="mono miss">No challenges resolved yet. This log is append-only and will record every one.</p>'
    )
    return shell("challenges.html", "Challenge protocol", "Challenges", body)


def page_changelog() -> str:
    md = (_ROOT / "CHANGELOG.md").read_text("utf-8")
    out, in_list = [], False
    for line in md.splitlines():
        if line.startswith("### "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("# "):
            continue
        elif line.strip().startswith("- "):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{esc(line.strip()[2:])}</li>")
        elif line.strip():
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{esc(line)}</p>")
    if in_list:
        out.append("</ul>")
    return shell("changelog.html", "Append-only", "Changelog", "".join(out))


def page_data(release: dict, coverage: dict) -> str:
    body = [
        '<p class="note">The proof ships with the claim. Every release is downloadable as an audit '
        "package: the corpus snapshot, the weights, the per-work breakdowns, and the one command that "
        "reproduces the ranking. If you cannot rebuild the rank from the package, the release is defective.</p>",
        "<h2>This release</h2>",
        f'<p class="mono">version <b>{esc(release["version"])}</b> &middot; corpus_hash <b>{esc(release["corpus_hash"][:24])}</b> &middot; '
        f'method_version {esc(release["method_version"])}</p>',
        f'<p>Metrics: <b>{esc(coverage.get("metrics_total"))}</b> '
        f'({", ".join(f"{esc(k)}: {esc(v)}" for k,v in coverage.get("by_metric_name",{}).items())}); '
        f'declared gaps: {esc(coverage.get("openalex_gaps"))}.</p>',
        "<h2>Downloads</h2><ul>"
        f'<li><a href="audit/{esc(VERSION)}/audit-bundle.zip"><b>audit-bundle.zip</b></a>, the self-contained '
        "offline package: pipeline code, weights, pinned data, release outputs, and a one-command "
        "reproduce script. Rebuild this release with no repo and no network.</li>"
        f'<li><a href="audit/{esc(VERSION)}/release.json">release.json</a>, the governance record</li>'
        f'<li><a href="audit/{esc(VERSION)}/coverage.json">coverage.json</a>, declared gaps</li>'
        f'<li><a href="audit/{esc(VERSION)}/rankings/">rankings/</a>, Top-50 per scenario</li>'
        f'<li><a href="audit/{esc(VERSION)}/breakdowns/">breakdowns/</a>, per-work evidence</li>'
        '<li><a href="audit/seeds/papers.json">papers.json</a>, the paper corpus (open JSON)</li>'
        "</ul>",
        "<h2>Reproduce</h2>"
        '<p class="mono">make install &amp;&amp; make assemble &amp;&amp; make release &amp;&amp; make verify-release</p>'
        "<p>The last command rebuilds this release from the pinned inputs and asserts the corpus_hash "
        "and rankings are bit-identical. A mismatch means the release is defective, and we want the challenge.</p>",
    ]
    return shell("data.html", "Data & audit", "Data & audit", "".join(body))


_LIB_FILTER_JS = """
(function(){
  var q=document.getElementById('q'),cat=document.getElementById('fcat'),
      lang=document.getElementById('flang'),
      cnt=document.getElementById('cnt'),items=[].slice.call(document.querySelectorAll('.entry'));
  function apply(){
    var t=(q.value||'').toLowerCase(),c=cat.value,l=lang.value,n=0;
    items.forEach(function(e){
      var ok=(!c||e.dataset.cat===c)&&(!l||e.dataset.lang===l)&&(!t||e.dataset.text.indexOf(t)>-1);
      e.style.display=ok?'':'none'; if(ok)n++;
    });
    cnt.textContent=n+' of '+items.length+' works shown';
  }
  [q,cat,lang].forEach(function(el){el.addEventListener('input',apply)});
  apply();
})();
"""


def page_library(books: list[dict]) -> str:
    cats = sorted({b["editorial"].get("category", "") for b in books if b["editorial"].get("category")})
    langs = sorted({b.get("language", "") for b in books if b.get("language")})

    def opts(values):
        return "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in values)

    head = (
        '<p class="note"><b>Seed status means candidacy, not canonical status.</b> Inclusion in '
        "the seed corpus asserts nothing; it marks a work as a candidate for scoring. Descriptions "
        "are shown where written and marked pending otherwise, never invented. Books are not yet "
        "scored (harvesting deferred), so nothing here is ranked.</p>"
        '<div class="filters">'
        '<label>Search<input id="q" type="search" placeholder="title or author"></label>'
        f'<label>Category<select id="fcat"><option value="">All</option>{opts(cats)}</select></label>'
        f'<label>Language<select id="flang"><option value="">All</option>{opts(langs)}</select></label>'
        "</div>"
        f'<p class="count" id="cnt">{len(books)} works</p>'
    )
    entries = []
    for b in sorted(books, key=lambda x: x["id"]):
        ed = b["editorial"]
        text = f'{b["canonical_title"]} {ed.get("author","")}'.lower().replace('"', "")
        flag = ' <span class="badge flag">conflict of interest declared</span>' if b["conflict_flag"] else ""
        meta = " &middot; ".join(
            x for x in [esc(ed.get("author", "")), esc(b.get("year", "")), esc(b.get("language", "")),
                        esc(ed.get("category", ""))] if x
        )
        desc = (f'<p class="desc">{esc(ed["description"])}</p>' if ed.get("description")
                else '<p class="pending">Description pending.</p>')
        entries.append(
            f'<div class="entry" id="{esc(b["id"])}" data-cat="{esc(ed.get("category",""))}" data-lang="{esc(b.get("language",""))}" '
            f'data-text="{esc(text)}">'
            f'<div class="t">{esc(b["canonical_title"])}{flag}</div>'
            f'<div class="meta">{meta}</div>'
            f'{desc}</div>'
        )
    body = head + "".join(entries) + '<script src="assets/canon.js" defer></script>'
    return shell("library.html", "The library, 573 candidate works", "Library", body)


def _context_shelf(active, kicker, title, rows, render) -> str:
    """Render a context shelf grouped by category, alphabetical within category,
    labelled described-never-ranked. rows: list of dicts; render(row) -> inner HTML."""
    note = ('<p class="note">These are <b>context entities</b>: described, <b>never ranked</b>. '
            "They carry no score, by construction. Listed alphabetically within each category, "
            "with a last-verified date where known.</p>")
    by_cat: dict[str, list] = {}
    for r in rows:
        by_cat.setdefault(r.get("category") or "Uncategorized", []).append(r)
    out = [note]
    for cat in sorted(by_cat):
        out.append(f'<div class="shelf-cat">{esc(cat)}</div>')
        for r in sorted(by_cat[cat], key=lambda x: (x.get("name") or "").lower()):
            out.append(f'<div class="entry" id="{esc(r.get("id",""))}">{render(r)}</div>')
    return shell(active, kicker, title, "".join(out))


def page_voices(persons: list[dict]) -> str:
    def render(p):
        meta = " &middot; ".join(x for x in [esc(p.get("anchor_affiliation", "")), esc(p.get("region", "")),
                                             (f'verified {esc(p["last_verified"])}' if p.get("last_verified") else "")] if x)
        kf = f'<p class="desc">{esc(p["known_for"])}</p>' if p.get("known_for") else ""
        bio = f'<p class="bio">{esc(p["bio"])}</p>' if p.get("bio") else ""
        return f'<div class="t">{esc(p["name"])}</div><div class="meta">{meta}</div>{kf}{bio}'
    return _context_shelf("voices.html", "Context shelf, 184 voices, described never ranked", "Voices", persons, render)


def page_orgs(orgs: list[dict]) -> str:
    def render(o):
        meta = esc(o.get("region", "")) + (f' &middot; verified {esc(o["last_verified"])}' if o.get("last_verified") else "")
        wi = f'<p class="desc">{esc(o["what_it_is"])}</p>' if o.get("what_it_is") else ""
        return f'<div class="t">{esc(o["name"])}</div><div class="meta">{meta}</div>{wi}'
    return _context_shelf("organizations.html", "Context shelf, 133 organizations, described never ranked", "Organizations", orgs, render)


def page_platforms(platforms: list[dict]) -> str:
    def render(p):
        meta = " &middot; ".join(x for x in [esc(p.get("status", "")),
                                             (f'verified {esc(p["last_verified"])}' if p.get("last_verified") else "")] if x)
        wi = f'<p class="desc">{esc(p["what_it_is"])}</p>' if p.get("what_it_is") else ""
        return f'<div class="t">{esc(p["name"])}</div><div class="meta">{meta}</div>{wi}'
    return _context_shelf("platforms.html", "Context shelf, 90 platforms, described never ranked", "Platforms", platforms, render)


def page_press() -> str:
    quotes = [
        "Every AI reading list asks you to trust the curator. This one asks you to check the math.",
        "I will rank texts. I will not rank human beings, and the system is built so I cannot start.",
        "A canon you can check is worth more than a canon you must believe.",
        "You cannot understand AI today by reading only what was written in English. So the Chinese works go in the spine, not the appendix.",
    ]
    body = [
        f'<p class="lead">{esc("The AI Canon is a free, public reference library of the texts that define artificial intelligence, built on an open method that lets anyone check, question, and overturn its judgments. It ranks texts, not people. It sells nothing. It is built by Jeroen Janssen, founder of the Dutch AI governance firm Apparens.")}</p>',
        "<h2>Why it is worth covering</h2>",
        f'<p>{esc("The literature of AI has outgrown anyone\'s ability to read it, and the maps that exist are mostly commercial: affiliate reading lists, vendor guides, influencer rankings. They ask the reader to trust the curator. Almost none show their work. The AI Canon is built the opposite way. Every ranking is produced by a published method, every number carries its source and date, and anyone can download the audit file and rebuild the result themselves. The premise is that curation of knowledge can be made auditable, the way an account can be audited, rather than taken on faith.")}</p>',
        "<h2>What is genuinely new here, and verifiable</h2>",
        f'<p>{esc("Three things, each checkable rather than asserted. First, it ranks texts and refuses to rank people: the voices and organizations in the field are described, never scored, and the data model has no way to rank a human being. Second, it is checkable end to end: the method, the corpus, the weights, and the audit files are public, and every rank links to the evidence that produced it. Third, it invites correction as a feature, not a complaint box: anyone can formally challenge any ranking or omission with evidence, and every challenge and its resolution is published in a permanent, public log.")}</p>',
        "<h2>The China and United States angle</h2>",
        f'<p>{esc("Most maps of AI thought only see half the field. You cannot understand artificial intelligence in 2026 by reading only what was written in English. The AI Canon is built, as a published rule, to score Chinese-language works within their own publishing and citation ecosystem before any cross-language comparison, rather than against English metrics that would erase them. That rule is written into the method; the mechanism that enforces it, and the Chinese corpus it needs, are still being built. Today the scored pilot is English-language papers, and the Chinese section is thin and openly under construction, with the project actively recruiting Chinese-literate scholars and readers to help build and verify it. The story is not a finished global canon. It is a Western-built reference work that is structurally committed to including China and is openly asking Chinese experts to help, at a moment when most Western and Chinese AI discourse barely acknowledge each other.")}</p>',
        "<h2>Quotable, attributable to Jeroen Janssen</h2>",
    ]
    body += [f'<p class="pullquote">{esc(q)}</p>' for q in quotes]
    body += [
        "<h2>What you can verify before you publish</h2>",
        f'<p>{esc("The method, the ontology, the full corpus, and the audit files are open. The challenge log is public. There is no advertising, no affiliate income, and no paid placement anywhere in the project, by design and by rule. It is a non-commercial public good; there is nothing to buy and no upsell to find.")}</p>',
        f'<p>{esc("The builder\'s own book, The AI Accountability Trap, is in the corpus and carries a visible conflict flag, scored by the same rules as everything else, with no exemption and no boost.")}</p>',
        "<h2>Contact</h2>",
        '<p>Jeroen Janssen, Apparens (Deventer, Netherlands). <a href="mailto:office@apparens.nl">office@apparens.nl</a>.</p>',
        '<p>If you want to share this rather than write about it, see the <a href="share.html">share page</a>.</p>',
    ]
    return shell("press.html", "For press and writers", "Press", "".join(body))


def page_share() -> str:
    body = [
        f'<p class="lead">{esc("Use any of this freely. The only thing asked is that you keep it honest, which is easy here, because the honest version is the interesting one. Do not call it the world\'s first or the definitive anything. It has not earned those words yet, and the fact that it refuses to claim them is part of what makes it worth sharing.")}</p>',
        "<h2>The problem it speaks to, in one breath</h2>",
        f'<p>{esc("There is too much to read, you cannot tell who to trust, and almost every reading list you have ever seen was either someone\'s opinion or someone\'s affiliate income. Meanwhile the field itself has split in two, English and Chinese, and most maps only show you one half.")}</p>',
        "<h2>The turn</h2>",
        f'<p>{esc("Someone built a reference library for the whole field that you can actually check. It ranks the texts, not the people. Every ranking shows its evidence. You are invited to prove it wrong, in public. It is free, it is built to include both the American and Chinese literature, and it sells you nothing.")}</p>',
        "<h2>A drop-in post you can adapt</h2>",
        '<div class="sharebox">'
        f'<p>{esc("Most “best AI books” lists are either someone\'s opinion or someone\'s affiliate link.")}</p>'
        f'<p>{esc("I just came across something different: The AI Canon. A free, public reference library of the texts that define AI, built on an open method you can actually inspect.")}</p>'
        f'<p>{esc("What makes it stand out to me:")}</p><ul>'
        f'<li>{esc("It ranks texts, not people. The thinkers and labs are described, never ranked against each other.")}</li>'
        f'<li>{esc("You can check every judgment. The method, the data, and the audit files are public, and each ranking links to the evidence behind it.")}</li>'
        f'<li>{esc("It invites you to prove it wrong. Disagree with a ranking? File a challenge with evidence. Every challenge and its resolution is published.")}</li>'
        f'<li>{esc("It takes China seriously. It is built to include the Chinese-language literature in the core, not as a footnote, and it is openly recruiting Chinese-reading contributors to help finish that work.")}</li>'
        f'<li>{esc("It sells nothing. No ads, no affiliate links, no paywall.")}</li></ul>'
        f'<p>{esc("In a field where everyone is selling certainty, a reference you are allowed to argue with feels genuinely new.")}</p>'
        f'<p>{esc("[link] Worth a look if you are trying to figure out what to read and who to trust in AI.")}</p>'
        "</div>",
        "<h2>If you want a sharper, shorter version</h2>",
        '<div class="sharebox">'
        f'<p>{esc("Someone built an AI reading canon you are actually allowed to argue with.")}</p>'
        f'<p>{esc("It ranks texts, not people. It shows its evidence for every call. It is built to include the American and Chinese literature, with the Chinese section still under construction. It invites public challenges and publishes every resolution. And it sells nothing, no ads, no affiliate links.")}</p>'
        f'<p>{esc("“A canon you can check is worth more than a canon you must believe.”")}</p>'
        f'<p>{esc("[link]")}</p>'
        "</div>",
        "<h2>One honest note for whoever shares it</h2>",
        f'<p>{esc("The rankings are still in pilot and the Chinese section is still being built. If you want to help with the second part and you read Chinese, that is an open invitation, not a disclaimer. Saying so out loud tends to make the post better, not worse.")}</p>',
    ]
    return shell("share.html", "If you want to share this", "Share", "".join(body))


_SEARCH_JS = """
(function(){
  var idx=window.CANON_INDEX||[];
  var q=document.getElementById('sq'),out=document.getElementById('sresults'),cnt=document.getElementById('scount');
  var TYPE={book:'Book',paper:'Paper',voice:'Voice',organization:'Organization',platform:'Platform'};
  var CAP=80;
  function render(term){
    term=(term||'').trim().toLowerCase();out.textContent='';
    if(!term){cnt.textContent=idx.length+' entries in the corpus. Start typing to search.';return;}
    var hits=[];
    for(var i=0;i<idx.length&&hits.length<CAP;i++){var e=idx[i];if((e.l+' '+(e.s||'')).toLowerCase().indexOf(term)>-1)hits.push(e);}
    cnt.textContent=hits.length+(hits.length>=CAP?'+':'')+' result'+(hits.length===1?'':'s');
    hits.forEach(function(e){
      var a=document.createElement('a');a.className='sresult';a.href=e.u;
      var t=document.createElement('div');t.className='st';t.textContent=e.l;
      var chip=document.createElement('span');chip.className='schip';chip.textContent=TYPE[e.t]||e.t;t.appendChild(chip);
      a.appendChild(t);
      if(e.s){var s=document.createElement('div');s.className='ss';s.textContent=e.s;a.appendChild(s);}
      out.appendChild(a);
    });
  }
  q.addEventListener('input',function(){render(q.value);});
  var pre=new URLSearchParams(location.search).get('q');if(pre)q.value=pre;
  render(q.value);q.focus();
})();
"""


def page_about() -> str:
    def p(text):
        return "<p>" + esc(text) + "</p>"
    body = [
        '<p class="lead">Why this exists, what it is, and how to read it.</p>',

        "<h2>Why I built it</h2>",
        p("The literature of artificial intelligence is now larger than any one person can hold, "
          "and the maps we have are mostly selling something. Affiliate lists, vendor reading "
          "guides, threads ranked by who shouted loudest. Each asks you to trust the curator. "
          "Almost none let you check the curator's work."),
        p("I build governance for a living. My one rule is that governance is not what you claim, "
          "it is what you can prove. A field this consequential deserves a reference work held to "
          "the same standard: a library whose every judgment can be inspected, questioned, and "
          "overturned with evidence. So I built the thing I wanted to exist and could not find. "
          "Not to own it. To give it."),
        p("This is a public good. It is free, it always will be, and nothing in it is for sale."),

        "<h2>What I built</h2>",
        p("A reference library of the texts that define artificial intelligence: the books, the "
          "papers, and the standards that shaped how we think, build, and govern it. Alongside the "
          "texts, a curated record of the people, organizations, and platforms that form the "
          "field's context."),
        p("The rankings get the attention, but they are not the product. The library is the "
          "product. A ranking is one view of it, produced by a published method at a fixed date. "
          "The method is the part that matters. Anyone can assert that a book is important. The "
          "Canon shows its reasoning, names its sources, and invites you to prove it wrong."),
        p("So the Canon is a reference work first and a ranking second. It answers why a text "
          "matters, what underpins it, and how it relates to the rest, before it answers which one "
          "is first."),

        "<h2>How it is constructed</h2>",
        p("Two kinds of thing live here, and they are treated differently on purpose."),
        "<p><b>Texts are scored.</b> " + esc(
            "Books, papers, reports, and standards are ranked by evidence: citations, library "
            "holdings, syllabus adoption, sustained readership over time. The scoring is "
            "deterministic, which means the same inputs always produce the same result, and anyone "
            "holding the audit file can rebuild a ranking exactly. Every number carries its source, "
            "its date, and its confidence. Where evidence is missing, that absence is recorded and "
            "counted, never guessed. A standard is never ranked against a novel; each kind of text "
            "is judged within its own domain, because comparing them would be meaningless.") + "</p>",
        "<p><b>People are not scored.</b> " + esc(
            "The voices, organizations, and platforms are described and categorized, never ranked. "
            "There is no score field for a person anywhere in the system. This is built into the "
            "foundation, not added as a courtesy. I will rank texts. I will not rank human beings, "
            "and the structure makes it impossible to start.") + "</p>",
        "<p><b>The method is open.</b> " + esc(
            "The corpus, the ontology, the weights, and the audit files are all public. The strength "
            "of this project is not a secret formula. It is the labour of careful curation, the "
            "discipline of showing the work, and the growing record of challenges met in the open. "
            "Those cannot be copied by reading the method. They can only be earned by doing the "
            "work.") + "</p>",
        "<p><b>A word on honesty about coverage.</b> " + esc(
            "The Canon is strong in English. Its multilingual layer is still in development, and its "
            "Chinese-language spine is a known gap. Until that gap is closed, this is not a "
            "worldwide canon, and it will not call itself one. I would rather state the limit "
            "plainly than claim a completeness I have not earned.") + "</p>",

        "<h2>How it is maintained</h2>",
        p("By a person, with help from machines that are not allowed to decide anything."),
        p("I adjudicate every challenge myself, against the evidence, and publish the resolution. "
          "I write the descriptions. Automated tools harvest the data, watch for changes, and "
          "propose updates, but no ranking ever moves without a human reviewing and approving it. "
          "The tools observe, assess, and escalate. They do not act. That distinction is the whole "
          "point of a canon you can trust rather than an algorithm you must accept."),
        p("Every change is logged and nothing is ever quietly altered. Corrections become new "
          "versions; the old ones remain visible. I do not promise a schedule, because a schedule I "
          "would resent is a promise I would break. I promise the discipline instead: every update "
          "logged, every correction traceable, every ranking open to challenge, and no commercial "
          "influence of any kind, ever. The changelog is the proof. It cannot lie about whether the "
          "work is being done."),

        "<h2>Sources and acknowledgments</h2>",
        p("The candidate corpus was seeded, with gratitude, from curated reading lists: Jurgen "
          "Appelo's AI reading list, the Monett Critical-AI reading list (14th edition), and the "
          "project's own candidate hunt. Seeding from a list is candidacy for scoring, not an "
          "endorsement by those curators, and it carries no weight in any ranking. The full "
          "per-work source is kept in the downloadable corpus data for transparency."),

        "<h2>Who it is for</h2>",
        p("One library, many doors. A student opens it to find what to learn and in what order. A "
          "professor opens it to find what to teach. A journalist opens it to find who and what to "
          "research, and the record of who got things wrong. An investor opens it to read the "
          "landscape. An author or editor opens it to find the works that endure. A practitioner "
          "opens it to find the standards that govern their work."),
        p("It is not built to flatter any of them, and not built to convert anyone into a customer, "
          "because there is nothing to buy. It is built to be useful and honest to all of them at "
          "once, the way a good library is."),

        "<h2>How it should be interpreted</h2>",
        p("A rank is not a verdict on intrinsic worth. It is a transparent output of declared "
          "evidence, weights, and missing-data rules, at a specific release date. Read it as "
          "exactly that, and no more."),
        p("A high rank means a text scored well on the evidence the method measured, under one set "
          "of weights, on one day. Change the weights and the order changes, which is why three "
          "different weightings are published rather than one. A low rank, or an absence, is not a "
          "judgment that a work is bad. It may mean the evidence is thin, the work is recent, or "
          "the method does not yet see it well. Inclusion in the seed corpus means a work is a "
          "candidate, not that it is canonical."),
        p("If you disagree, you are not a nuisance. You are the mechanism. The Canon improves by "
          "being contested, and a challenge you can file is worth more than a ranking you are asked "
          "to believe."),

        "<h2>What you can do with it</h2>",
        p("If you are here to learn AI, start with the library, not the ranking. Pick the domain "
          "you care about, governance or deep learning or the economics of automation, and read "
          "the texts that have endured there, in the order their descriptions suggest. Use the "
          "rankings as a second opinion, not a syllabus. Follow the connections: a book leads to "
          "the papers under it, the papers to the people who wrote them, the people to the "
          "institutions they work in. The structure is a map of how the field thinks, and you can "
          "walk it. Download the whole corpus as open data and keep it. It is yours."),
        p("If you find yourself here as a subject, an author whose book is listed or a voice in the "
          "field, two things are true. You are not being ranked against your peers. The people on "
          "this list are described, never scored, and never placed above or below one another. And "
          "your entry is built from public, professional, bibliographic facts, held to the same "
          "standard as everything else. If something about your entry is wrong, a misattributed "
          "work, an outdated affiliation, a description that misses the mark, tell me, and it will "
          "be corrected in the open through the same challenge process as any other claim. If you "
          "believe a text's rank or its absence is unjust, contest it with evidence, and the "
          "resolution will be published whether it goes your way or not. What you cannot do is buy "
          "your way up, or have a rival quietly removed, because no one can, and that is precisely "
          "what makes your presence here mean something."),

        '<p class="note">Nothing is for sale. Nothing is hidden. Nothing is final. '
        'Challenge anything: <a href="mailto:office@apparens.nl">office@apparens.nl</a></p>',
    ]
    return shell("about.html", "The AI Canon", "Statement", "".join(body))


def page_search() -> str:
    body = (
        '<p class="note">Search the whole corpus: 573 books, 162 papers, and the voices, '
        "organizations, and platforms. Every result links to its entry. The search runs entirely "
        "in your browser; nothing typed here is sent anywhere.</p>"
        '<div class="search-wrap"><input id="sq" type="search" autocomplete="off" '
        'placeholder="Search titles, authors, names..." aria-label="Search the corpus"></div>'
        '<p class="count" id="scount"></p>'
        '<div id="sresults"></div>'
        '<script src="assets/search-index.js" defer></script>'
        '<script src="assets/search.js" defer></script>'
    )
    return shell("search.html", "Search the corpus", "Search", body)


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(buf.getvalue(), encoding="utf-8")


# Cloudflare Pages _headers. Strict CSP with NO unsafe-inline anywhere: all CSS
# and JS are external 'self' files, fonts are self-hosted, the only image is the
# self logo. default-src 'none' denies everything not explicitly allowed. There is
# no backend, no form, no third-party request, so connect/form/frame all close.
_HEADERS = """/*
  Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'; upgrade-insecure-requests
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
  X-Frame-Options: DENY
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Resource-Policy: same-origin
  Permissions-Policy: accelerometer=(), autoplay=(), camera=(), display-capture=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=(), interest-cohort=()
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
"""


def build() -> dict:
    # Externalized assets so the CSP can forbid inline script and style entirely.
    _write("assets/canon.css", _STYLE.strip() + "\n")
    _write("assets/canon.js", _LIB_FILTER_JS.strip() + "\n")
    _write("_headers", _HEADERS)

    release = _load(RELEASES / VERSION / "release.json")
    rankings = {
        p.stem: _load(p) for p in sorted((RELEASES / VERSION / "rankings").glob("*.json"))
    }
    breakdowns = {
        p.stem: _load(p) for p in sorted((RELEASES / VERSION / "breakdowns").glob("*.json"))
    }
    papers = _papers_index()
    scored = set(breakdowns)
    coverage = _load(RELEASES / VERSION / "coverage.json")
    books = _load(SEEDS / "books.json")
    persons = _load(SEEDS / "persons.json")
    orgs = _load(SEEDS / "orgs.json")
    platforms = _load(SEEDS / "platforms.json")

    _write("index.html", page_home(release, rankings, papers, coverage))
    _write("library.html", page_library(books))
    _write("canon-50.html", page_canon50(release, rankings, papers))
    for wid, per_scenario in breakdowns.items():
        _write(f"work/{wid}.html", page_work(wid, per_scenario, papers))
    _write("papers.html", page_papers(papers, scored))
    _write("voices.html", page_voices(persons))
    _write("organizations.html", page_orgs(orgs))
    _write("platforms.html", page_platforms(platforms))
    _write("method.html", page_method())
    _write("challenges.html", page_challenges())
    _write("changelog.html", page_changelog())
    _write("data.html", page_data(release, coverage))
    _write("about.html", page_about())
    _write("press.html", page_press())
    _write("share.html", page_share())

    # Global search: an embedded index (so the strict CSP needs no connect-src) + a self script.
    si = []
    for b in books:
        ed = b["editorial"]
        meta = " · ".join(x for x in [ed.get("author", ""), str(b.get("year") or ""), ed.get("category", "")] if x)
        si.append({"t": "book", "l": b["canonical_title"], "s": meta, "u": "library.html#" + b["id"]})
    for pid in sorted(papers):
        p = papers[pid]
        ed = p.get("editorial", {})
        u = f"work/{pid}.html" if pid in scored else "papers.html#" + pid
        meta = " · ".join(x for x in [str(p.get("year") or ""), ed.get("venue", "")] if x)
        si.append({"t": "paper", "l": p["canonical_title"], "s": meta, "u": u})
    for o in persons:
        si.append({"t": "voice", "l": o["name"], "s": o.get("known_for") or o.get("anchor_affiliation") or "", "u": "voices.html#" + o["id"]})
    for o in orgs:
        si.append({"t": "organization", "l": o["name"], "s": o.get("what_it_is") or "", "u": "organizations.html#" + o["id"]})
    for o in platforms:
        si.append({"t": "platform", "l": o["name"], "s": o.get("what_it_is") or "", "u": "platforms.html#" + o["id"]})
    idx_js = ("window.CANON_INDEX=" + json.dumps(si, ensure_ascii=False, separators=(",", ":"))
              .replace("</", "<\\/") + ";\n")
    _write("assets/search-index.js", idx_js)
    _write("assets/search.js", _SEARCH_JS.strip() + "\n")
    _write("search.html", page_search())

    # Copy the audit package + open corpus so they are publicly downloadable.
    audit_rel = SITE / "audit" / VERSION
    if audit_rel.exists():
        shutil.rmtree(audit_rel)
    shutil.copytree(RELEASES / VERSION, audit_rel)
    seeds_out = SITE / "audit" / "seeds"
    seeds_out.mkdir(parents=True, exist_ok=True)
    for name in ("papers.json", "books.json", "persons.json", "orgs.json", "platforms.json"):
        shutil.copy(SEEDS / name, seeds_out / name)
    # Open CSV mirrors of the corpus (longevity / consumable without the site).
    _write_csv(seeds_out / "books.csv",
               ["id", "title", "author", "year", "language", "category", "source", "conflict_flag"],
               [[b["id"], b["canonical_title"], b["editorial"].get("author", ""), b.get("year", ""),
                 b.get("language", ""), b["editorial"].get("category", ""),
                 b["editorial"].get("source", ""), b["conflict_flag"]] for b in books])
    _write_csv(seeds_out / "papers.csv",
               ["id", "title", "authors", "year", "venue", "category"],
               [[p["id"], p["canonical_title"], p["editorial"].get("authors", ""), p.get("year", ""),
                 p["editorial"].get("venue", ""), p["editorial"].get("category", "")] for p in papers.values()])

    summary = {"pages": 13 + len(breakdowns), "work_pages": len(breakdowns), "version": VERSION}
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build()
