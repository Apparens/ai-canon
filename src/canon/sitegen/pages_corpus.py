"""The corpus shelves: home, Canon 50, per-work pages, papers, library, models."""

from __future__ import annotations

from urllib.parse import quote

from ..textnorm import fold
from .common import (counts, HUMILITY, POSITIONING, SEEDS, VERSION, _abs_source, _abstracts, _load,
                     _scenarios, esc, esc_verbatim, safe_url)
from .shell import shell


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
  <div class="stat"><b>{counts()["books"]}</b><span>candidate books, all described</span></div>
  <div class="stat"><b>{counts()["papers"]}</b><span>papers, 1943-2026</span></div>
  <div class="stat"><b>{counts()["voices"]}</b><span>voices, described, never ranked</span></div>
  <div class="stat"><b>{counts()["orgs"]}</b><span>organizations</span></div>
  <div class="stat"><b>{counts()["platforms"]}</b><span>platforms</span></div>
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
    _ab = _abstracts().get(work_id)
    if _ab:
        head.append(f'<details class="abs" open><summary>Abstract</summary>'
                    f'<p>{esc_verbatim(_ab["text"])}{_abs_source(_ab)}</p></details>')
    if p.get("conflict_flag"):
        head.append('<p class="note flag">Conflict of interest declared for this work.</p>')
    blocks = ["".join(head)]
    for scenario in sorted(per_scenario):
        row = per_scenario[scenario]
        blocks.append(f'<h2>{esc(scenario.replace("_"," ").title())}, score {row["score"]:.4f}</h2>')
        rows = ["<table><thead><tr><th>Metric</th><th>Status</th><th>Value</th><th>Norm.</th>"
                "<th>Weight</th><th>Contribution</th><th>Source</th><th>Confidence</th>"
                "<th>License</th><th>Provenance</th></tr></thead><tbody>"]
        for c in row["components"]:
            if c.get("status") == "present":
                prov = c.get("provenance_url", "")
                prov_a = f'<a href="{esc(safe_url(prov))}" rel="nofollow noopener">link</a>' if prov else "none"
                rows.append(
                    f'<tr><td class="mono">{esc(c["metric"])}</td><td>present</td>'
                    f'<td class="num">{esc(c.get("value",""))}</td><td class="num">{esc(c.get("normalized",""))}</td>'
                    f'<td class="num">{esc(c.get("weight",""))}</td><td class="num">{esc(c.get("contribution",""))}</td>'
                    f'<td>{esc(c.get("source",""))}</td><td>{esc(c.get("confidence",""))}</td>'
                    f'<td>{esc(c.get("license_note",""))}</td><td>{prov_a}</td></tr>'
                )
            else:
                rows.append(
                    f'<tr class="miss"><td class="mono">{esc(c["metric"])}</td><td>missing</td>'
                    f'<td colspan="3">recorded as missing, penalized by rule, never imputed</td>'
                    f'<td class="num">&minus;{esc(c.get("missing_data_penalty",""))}</td><td colspan="4">{esc(c.get("note",""))}</td></tr>'
                )
        rows.append("</tbody></table>")
        blocks.append("".join(rows))
    subject = f"Challenge rank: {work_id}"
    challenge_href = esc(f"mailto:office@apparens.nl?subject={quote(subject, safe='')}")
    blocks.append(f'<p class="note"><b>{esc(HUMILITY)}</b></p>')
    blocks.append(
        f'<p class="note">Disagree with this rank or a number? <a href="{challenge_href}">Challenge it</a> '
        "with your evidence. Every challenge gets a public identifier and a published resolution.</p>"
    )
    wt = (p.get("canonical_title") or work_id)
    work_desc = (f"Evidence and ranking for {wt} in The AI Canon: every harvested metric, its "
                 "source and provenance, the weights applied, and any missing-data penalty.")
    # shell() owns title escaping: pass the raw title, or & in a title double-escapes.
    return shell("canon-50.html", "Score breakdown", wt,
                 "".join(blocks), depth=1,
                 canonical=f"work/{work_id}.html", description=work_desc, og_type="article")


def page_papers(papers: dict, scored: set) -> str:
    abstracts = _abstracts()  # cached; tolerates a missing file (declared gap)
    n_abs = sum(1 for pid in papers if pid in abstracts)
    rows = [f'<p class="note">All {len(papers)} papers: the seed corpus plus recent work surfaced by the '
            '<a href="frontier.html">frontier review</a>, an AI-run, human-checked literature review that '
            "nominates candidates and scores nothing. <b>Listing means candidacy, not canonical status.</b> "
            "Papers with harvested evidence link to their breakdown; the rest are an honestly-declared "
            "coverage gap, not a zero. "
            f'Expand "Abstract" to read the paper in its own words ({n_abs} of {len(papers)} available; the '
            "remainder are pre-digital or closed-access, where no open abstract exists). Abstracts are the "
            "authors' verbatim text, quoted with their source; they are not covered by the site's CC BY "
            "data license.</p>",
            "<table><thead><tr><th>#</th><th>Paper</th><th>Year</th><th>Venue</th><th>Evidence</th></tr></thead><tbody>"]
    for pid in sorted(papers):
        p = papers[pid]
        ed = p.get("editorial", {})
        is_scored = pid in scored
        title = (f'<a href="work/{esc(pid)}.html">{esc(p["canonical_title"])}</a>'
                 if is_scored else esc(p["canonical_title"]))
        sig = f'<div class="meta">{esc(ed["significance"])}</div>' if ed.get("significance") else ""
        ab = abstracts.get(pid)
        absd = (f'<details class="abs"><summary>Abstract</summary>'
                f'<p>{esc_verbatim(ab["text"])}{_abs_source(ab)}</p></details>'
                if ab else "")
        ev = '<span class="tag">scored</span>' if is_scored else '<span class="tag miss">no evidence yet</span>'
        rows.append(
            f'<tr id="{esc(pid)}"><td class="num">{esc(pid.split("-")[-1])}</td><td>{title}{sig}{absd}</td>'
            f'<td class="num">{esc(p.get("year",""))}</td><td>{esc(ed.get("venue",""))}</td><td>{ev}</td></tr>'
        )
    rows.append("</tbody></table>")
    return shell("papers.html", "Shelf", "Papers", "".join(rows))


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
    return shell("library.html", f"The library, {len(books)} candidate works", "Library", body)


def _model_slug(name: str) -> str:
    """Stable anchor slug for a model, shared by the models page and the search index."""
    return "model-" + fold(name).replace(" ", "-")


def page_models(midx: dict, papers: dict, scored: set) -> str:
    """A derived INDEX (not a ranking, not a scored entity): model -> its paper(s)
    in the canon -> an external link. The card-only frontier is shown as a declared gap."""

    def resolve(sub):
        q = fold(sub)
        for p in papers.values():
            if q and q in fold(p["canonical_title"]):
                return p["id"]
        return None

    models = midx["models"]
    order = ["United States", "China", "Europe (France)", "Canada", "UAE"]
    countries = [c for c in order if any(m["country"] == c for m in models)]
    for m in models:
        if m["country"] not in countries:
            countries.append(m["country"])

    body = [
        f'<p class="lead">{esc(midx["note"])}</p>',
        f'<p class="note">Indexed as of {esc(midx["as_of"])}. This is a way in, not a leaderboard; '
        f'for the live, exhaustive tracker see <a href="{esc(safe_url(midx["epoch_url"]))}" target="_blank" '
        f'rel="noopener noreferrer nofollow">Epoch AI &#8599;</a>.</p>',
    ]
    for c in countries:
        cm = [m for m in models if m["country"] == c]
        withp = sum(1 for m in cm if m["paper"])
        body.append(f'<h2>{esc(c)} <span class="muted">({len(cm)} models, {withp} with a paper here)</span></h2>')
        labs = []
        for m in cm:
            if m["lab"] not in labs:
                labs.append(m["lab"])
        for lab in labs:
            body.append(f'<h3>{esc(lab)}</h3>')
            for m in cm:
                if m["lab"] != lab:
                    continue
                pid = resolve(m["paper"]) if m["paper"] else None
                if pid:
                    href = f"work/{esc(pid)}.html" if pid in scored else f"papers.html#{esc(pid)}"
                    plink = f'<a href="{href}">paper in the canon</a>'
                else:
                    plink = '<span class="gap">no paper, system card only</span>'
                ext = (f' &middot; <a href="{esc(safe_url(m["ext"]))}" target="_blank" '
                       f'rel="noopener noreferrer nofollow">model &#8599;</a>') if m.get("ext") else ""
                body.append(f'<div class="entry" id="{_model_slug(m["name"])}"><div class="t">{esc(m["name"])}</div>'
                            f'<div class="meta">{plink}{ext}</div></div>')
    return shell("models.html", "Models, indexed by their paper", "Models", "".join(body))
