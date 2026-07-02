"""The context shelves (voices, organizations, platforms) and the frontier map.

Context entities are described, never ranked: structurally, they carry no score.
"""

from __future__ import annotations

from .common import counts, SEEDS, _load, esc, esc_verbatim, safe_url
from .shell import shell

FRONTIER_DOI = "10.5281/zenodo.21112889"  # the frontier review artefact deposit


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
        src = (f'<p class="src"><a href="{esc(safe_url(p["source_url"]))}" target="_blank" '
               f'rel="noopener noreferrer nofollow">source &#8599;</a></p>') if p.get("source_url") else ""
        return f'<div class="t">{esc(p["name"])}</div><div class="meta">{meta}</div>{kf}{bio}{src}'
    return _context_shelf("voices.html", f"Context shelf, {counts()['voices']} voices, described never ranked", "Voices", persons, render)


def page_orgs(orgs: list[dict]) -> str:
    def render(o):
        meta = esc(o.get("region", "")) + (f' &middot; verified {esc(o["last_verified"])}' if o.get("last_verified") else "")
        wi = f'<p class="desc">{esc(o["what_it_is"])}</p>' if o.get("what_it_is") else ""
        src = (f'<p class="src"><a href="{esc(safe_url(o["source_url"]))}" target="_blank" '
               f'rel="noopener noreferrer nofollow">about &#8599;</a></p>') if o.get("source_url") else ""
        return f'<div class="t">{esc(o["name"])}</div><div class="meta">{meta}</div>{wi}{src}'
    return _context_shelf("organizations.html", f"Context shelf, {counts()['orgs']} organizations, described never ranked", "Organizations", orgs, render)


def page_platforms(platforms: list[dict]) -> str:
    def render(p):
        meta = " &middot; ".join(x for x in [esc(p.get("status", "")),
                                             (f'verified {esc(p["last_verified"])}' if p.get("last_verified") else "")] if x)
        wi = f'<p class="desc">{esc(p["what_it_is"])}</p>' if p.get("what_it_is") else ""
        src = (f'<p class="src"><a href="{esc(safe_url(p["source_url"]))}" target="_blank" '
               f'rel="noopener noreferrer nofollow">about &#8599;</a></p>') if p.get("source_url") else ""
        return f'<div class="t">{esc(p["name"])}</div><div class="meta">{meta}</div>{wi}{src}'
    return _context_shelf("platforms.html", f"Context shelf, {counts()['platforms']} platforms, described never ranked", "Platforms", platforms, render)


# The frontier page's fixed prose, kept as constants so the assembling function
# stays short. Each constant is one (or, joined with \n, several) body block(s).
_FRONTIER_LEAD = (
    '<p class="lead">Every paper ends by naming what it could not do. We pooled the stated '
    "limitations and future-work of the canon's papers, coded each statement, and let the pattern "
    "show where the open frontiers lie. <b>This is an AI-synthesized reading, traceable to the "
    "authors' own words.</b></p>")
_FRONTIER_HONEST = (
    "<h2>How this was kept honest</h2>\n"
    "<p>AI is good at finding patterns. It is also good at over-claiming them. So every layer was "
    "adversarially checked before it was allowed to count: quotes verified verbatim, coding "
    "reproduced by an independent blind coder, every theme attacked by a skeptic, and ritual "
    '"further research is needed" boilerplate removed as rhetoric, never counted as evidence.</p>')
_FRONTIER_LANDSCAPE = (
    "<h2>The frontier landscape</h2>\n"
    '<p class="note">There is no single dominant frontier. Open any sub-frontier to read the '
    "papers' own words. Counts are distinct papers, at the high-substance threshold.</p>")
_FRONTIER_DERIVED = (
    "<h2>Derived frontiers</h2>\n"
    "<p>Above the sub-frontiers sit coherent problems the corpus poses in pieces across families "
    "but names nowhere. These were discovered <b>blind</b> by four independent analysts against "
    "fixed criteria, then ranked by how many independently found each.</p>")
_FRONTIER_RESULT = (
    "<h2>The one cross-paper result that held under attack</h2>\n"
    "<p><b>You cannot assure the alignment of a mechanism you cannot read.</b> Mesa-optimizers "
    "(2019) states that internals-based verification is out of reach given the limits of current "
    "transparency methods. Sleeper Agents (2024) shows that behavioural safety training cannot "
    "observe why a model behaves as it does. Interpretability is the gate between understanding a "
    "model and assuring it. Every other cross-paper bridge we tried was weakened or refuted; this "
    "one got stronger.</p>")


def page_frontier() -> str:
    d = _load(SEEDS.parent / "frontier.json")
    cov, rel, disc = d["coverage"], d["reliability"], d["discovery"]
    n_sub = sum(len(f["subs"]) for f in d["families"])
    b = []
    b.append(_FRONTIER_LEAD)
    b.append(f'<div class="statgrid">'
             f'<div class="stat"><b>{esc(cov["papers_with_frontier"])}</b><span>papers with a specific open problem</span></div>'
             f'<div class="stat"><b>{esc(cov["high_substance"])}</b><span>high-substance frontier statements</span></div>'
             f'<div class="stat"><b>{esc(cov["ritual_pct"])}%</b><span>ritual boilerplate, filtered out</span></div>'
             f'<div class="stat"><b>{n_sub}</b><span>sub-frontiers, in {len(d["families"])} families</span></div></div>')
    b.append(_FRONTIER_HONEST)
    b.append(f'<div class="statgrid">'
             f'<div class="stat"><b>0</b><span>fabricated quotes across four audits</span></div>'
             f'<div class="stat"><b>{rel["family"]:.2f}</b><span>inter-coder agreement, family level (Cohen kappa)</span></div>'
             f'<div class="stat"><b>{rel["subtheme"]:.2f}</b><span>agreement on the fine sub-frontier label</span></div>'
             f'<div class="stat"><b>2-3x</b><span>over-claim caught in un-audited aggregation</span></div></div>')
    b.append(_FRONTIER_LANDSCAPE)
    for fam in d["families"]:
        b.append(f'<div class="ffam"><h2>{esc(fam["name"])}</h2>'
                 f'<span class="fc">{esc(fam["papers"])} papers</span></div>')
        for s in fam["subs"]:
            quotes = "".join(
                f'<li><span class="q">&ldquo;{esc_verbatim(q["text"])}&rdquo;</span>'
                f'<span class="src">{esc(q["title"])} ({esc(q["year"])})</span></li>' for q in s["quotes"])
            b.append(f'<details class="fd"><summary><span class="sn">{esc(s["name"])}</span>'
                     f'<span class="sc">{esc(s["papers"])} papers</span></summary>'
                     f'<p class="fblurb">{esc(s["blurb"])}</p><ul class="fq">{quotes}</ul></details>')
    b.append(_FRONTIER_DERIVED)
    for f in d["derived_research"]:
        b.append(f'<div class="dcard"><div class="dhead"><b>{esc(f["name"])}</b>'
                 f'<span class="dt">{esc(f["convergence"])} analysts</span></div>'
                 f'<p>{esc(f["definition"])}</p></div>')
    for f in d["derived_applied"]:
        parents = ", ".join(esc(p.replace("-", " ")) for p in f.get("derived_from", []))
        b.append(f'<div class="dcard app"><div class="dhead"><b>{esc(f["name"])}</b>'
                 f'<span class="dt">applied, analyst-nominated</span></div>'
                 f'<p>{esc(f["definition"])}</p>'
                 f'<p class="dfrom">Shown as an applied response to the research frontiers it depends on '
                 f'({parents}), never asserted as their peer.</p></div>')
    b.append(_FRONTIER_RESULT)
    b.append("<h2>What the frontier is already attracting</h2>")
    b.append(f"<p>Each frontier's open question becomes a search for the recent work the canon does not yet "
             f"contain. That search returned <b>{esc(disc['off_canon'])} verified off-canon papers</b>, and "
             f"<b>{esc(disc['active'])} of {esc(disc['units'])}</b> frontiers are judged active. The canon is "
             f"extended with what its own open questions surface.</p>")
    b.append('<div class="note flag"><b>How to read this.</b> The families, sub-frontiers, and derived '
             "frontiers are an AI-synthesized reading of the papers' own limitation and future-work "
             "sentences, adversarially audited and human-reviewed. Every count links to verbatim source "
             "statements. This is an interpretive synthesis, not a ranking, and not a claim about which "
             "research is most important. It reads the open-access, machine-readable core of the corpus "
             f"({cov['papers_reviewed']} of {cov['of_total']} papers), not all of AI. Method and full "
             f'artefact package: <a href="https://doi.org/{FRONTIER_DOI}">Zenodo</a>.</div>')
    return shell("frontier.html", "Research frontier", "What the canon has not solved", "\n".join(b))
