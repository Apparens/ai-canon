"""The meta pages: method, challenges, changelog, data, about, press, share, search.

Mostly fixed prose. The long page bodies live in module-level constants so each
assembling function stays small; the strings themselves are unchanged.
"""

from __future__ import annotations

from .. import METHOD_VERSION, ONTOLOGY_VERSION
from .common import counts, CONCEPT_DOI, VERSION, _ROOT, _scenarios, esc
from .shell import share_row, shell

_METHOD_RULES = [
    "Deterministic scoring. Identical inputs and weights produce identical ranks; reproducible from the audit package with one command.",
    "Provenance on every number: source, retrieved_at, confidence, licence note. A number without provenance does not exist.",
    "No silent imputation. Missing evidence is recorded as missing and penalized by a published rule, never estimated.",
    "Domains never cross-rank. Books, papers, reports, and standards are scored within their own domain.",
    "Each language ecosystem scores within itself first. Coverage gaps are declared, not hidden.",
    "People are context, not contestants. Persons, organizations, and platforms carry no score, ever.",
    "Manual decisions are records. Every override carries a written rationale and is published; Apparens-authored works are flagged.",
    "Humility on rank. A rank is a transparent output of declared evidence, weights, and missing-data rules at a release date, not a verdict on intrinsic worth.",
]

_METHOD_SIGNALS = (
    "<h2>What each signal means</h2><ul>"
    "<li><b>citation_count</b>: all-time citations from OpenAlex (CC0). The scale of scholarly impact.</li>"
    "<li><b>readership_persistence</b>: the number of distinct years a work keeps being cited "
    "(from OpenAlex counts_by_year). A longevity proxy: a work cited across many years scores "
    "higher than a one-year spike. It rewards enduring use, not recent volume.</li>"
    "<li><b>library_holdings</b>, <b>syllabus_adoptions</b>: declared but not yet harvested for "
    "the pilot (WorldCat / Open Syllabus drops pending). Works are penalized for them by rule, "
    "never imputed.</li></ul>")

_METHOD_DEFERRED = (
    "<h2>Declared deferred capabilities</h2>"
    "<p>The method names these now and does not pretend they are done. Each is deferred openly, "
    "not silently stubbed:</p><ul>"
    "<li><b>Per-ecosystem normalization (rule 5)</b>: scoring runs per domain today. Per-language "
    "normalization activates only once works from more than one ecosystem enter a scored domain. "
    "Until then the site does not claim worldwide or present-tense multilingual coverage. The "
    "Chinese-language spine is now a curated 63 books, but it carries no harvested metrics yet "
    "(the Chinese citation ecosystem is a separate, deferred harvester), so it is browsable, not scored.</li>"
    "<li><b>A fuller longevity proxy</b>: library holdings over time, edition count, and continued "
    "availability, to complement readership_persistence.</li>"
    "<li><b>Book scoring</b>: books are curated and browsable now but not yet scored; the pilot "
    "ranks papers only.</li></ul>")

_METHOD_NOT_HERE = (
    '<h2 id="not-here">What is not here, and why</h2>'
    "<p>A reference is defined as much by what it excludes as by what it lists. These gaps "
    "are deliberate and declared, not oversights.</p><ul>"
    "<li><b>The closed frontier ships no papers.</b> Many of the most capable 2025 models, "
    "including the latest GPT, Claude, Gemini, Grok, and Llama releases, are documented only "
    "by a system card or a blog post, not a paper. A canon of the literature cannot rank "
    "what was never written down. We note this not as a complaint but as a finding: the "
    "most-discussed models are increasingly the least-documented, and open-weight and "
    "Chinese labs now carry most of the published record.</li>"
    "<li><b>Models are not entities; their papers are.</b> The Canon ranks texts, not "
    "products. A model enters only through a primary paper or technical report. Where a "
    "model has none, it is absent by design, however important it is.</li>"
    "<li><b>Stable sources are preferred.</b> We cite arXiv or a DOI wherever possible, "
    "because those are permanent and versioned. A few significant reports exist only as a "
    "PDF on a company's own site, such as Baidu's ERNIE 4.5. We include those sparingly and "
    "flag them, since vendor links can change or disappear.</li>"
    "<li><b>New entries are candidates, not verdicts.</b> A freshly added paper is in the "
    "corpus but not yet scored. Scoring waits on harvested evidence, so a 2025 model report "
    "sits unranked until that evidence accrues. Candidacy asserts nothing.</li>"
    "<li><b>The corpus is still partial.</b> Coverage is a pilot. The Chinese-language "
    "section in particular is openly under construction, and the paper set leans English. "
    "We would rather say so than pretend completeness.</li></ul>")

_METHOD_HOW_MADE = (
    '<h2 id="how-made">How this was made</h2>'
    "<p>The Canon is curated and computed, with AI used as a drafting aid, never as the "
    "authority. To be exact:</p><ul>"
    "<li><b>Ranks and scores</b> are computed deterministically from declared evidence and "
    "weights. They are not generated by a language model, and they rebuild bit-identically "
    "from the audit package.</li>"
    "<li><b>Sources</b> are real and human-checked. Every voice links to a source you can "
    "open, and the bibliographic record is reconciled against OpenLibrary and Crossref.</li>"
    "<li><b>Book and entry descriptions</b>: many are AI-drafted from public sources, "
    "written to be neutral and factual, with no claims beyond what the work is about; each "
    "carries a confidence flag in the data. If one is wrong, challenge it and we will fix it.</li>"
    "<li><b>Voice biographies</b>: AI-drafted from each voice's own cited source and the "
    "verified affiliation, written to be neutral and factual with no claims beyond the "
    "sources. If one is wrong, challenge it and we will correct it.</li>"
    "<li><b>Paper significance notes</b>: the one-line notes on the paper shelf are "
    "AI-drafted, anchored to each paper's own record, neutral and factual. The verbatim "
    "abstracts are NOT AI text: they are the authors' own words, quoted with a source.</li>"
    "<li><b>The frontier map</b>: the research-frontier review that surfaced the recent "
    "candidate papers was AI-run and human-checked, with every admitted paper verified "
    "against its arXiv record. It nominates candidates only; it scores nothing.</li>"
    "<li><b>The cover image</b> (the person holding a phone) is AI-modified and labelled as "
    "such on the social card, EU AI Act style.</li></ul>"
    "<p>Where AI helped draft text, a human checked it against the evidence. Where evidence "
    "is missing, we say so rather than let a model fill the gap.</p>")


def page_method() -> str:
    scn = _scenarios()
    body = ["<h2>Rules the ranking cannot break</h2><ol>"]
    body += [f"<li>{esc(r)}</li>" for r in _METHOD_RULES]
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
    body.append(_METHOD_SIGNALS)
    body.append(_METHOD_DEFERRED)
    body.append(_METHOD_NOT_HERE)
    body.append(_METHOD_HOW_MADE)
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


def _md_to_html(lines) -> str:
    """The markdown subset CHANGELOG.md actually uses: #/##/### headings, - lists,
    plain paragraphs. The top-level title is dropped (the page shell owns the h1)."""
    out, in_list = [], False
    for line in lines:
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
    return "".join(out)


def page_changelog() -> str:
    md = (_ROOT / "CHANGELOG.md").read_text("utf-8")
    return shell("changelog.html", "Append-only", "Changelog", _md_to_html(md.splitlines()))


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
        "<h2>Downloads</h2>"
        "<p>The audit bundle below contains everything (code, weights, pinned data, all rankings, and "
        "every per-work breakdown). The individual files are listed for convenience.</p>"
        "<h3>Audit package</h3><ul>"
        f'<li><a href="audit/{esc(VERSION)}/audit-bundle.zip"><b>audit-bundle.zip</b></a>, the self-contained '
        "offline package: pipeline code, weights, pinned data, release outputs, and a one-command "
        "reproduce script. Rebuild this release with no repo and no network.</li>"
        f'<li><a href="audit/{esc(VERSION)}/release.json">release.json</a>, the governance record</li>'
        f'<li><a href="audit/{esc(VERSION)}/coverage.json">coverage.json</a>, declared gaps</li>'
        "</ul>"
        "<h3>Rankings (Top-50 per scenario)</h3><ul>"
        f'<li><a href="audit/{esc(VERSION)}/rankings/paper__academic.json">paper__academic.json</a></li>'
        f'<li><a href="audit/{esc(VERSION)}/rankings/paper__broad_influence.json">paper__broad_influence.json</a></li>'
        f'<li><a href="audit/{esc(VERSION)}/rankings/paper__governance_practitioner.json">paper__governance_practitioner.json</a></li>'
        "</ul>"
        "<h3>The corpus, as open data</h3><ul>"
        f'<li><a href="audit/seeds/books.json">books.json</a> &middot; <a href="audit/seeds/books.csv">books.csv</a>, {counts()["books"]} books</li>'
        f'<li><a href="audit/seeds/papers.json">papers.json</a> &middot; <a href="audit/seeds/papers.csv">papers.csv</a>, {counts()["papers"]} papers</li>'
        '<li><a href="audit/seeds/persons.json">persons.json</a>, 184 voices</li>'
        '<li><a href="audit/seeds/orgs.json">orgs.json</a>, 133 organizations</li>'
        '<li><a href="audit/seeds/platforms.json">platforms.json</a>, 90 platforms</li>'
        "</ul>"
        '<p class="mono">Per-work breakdowns (one file per scored work) are inside the audit bundle.</p>',
        "<h2>Reproduce</h2>"
        '<p class="mono">make install &amp;&amp; make assemble &amp;&amp; make release &amp;&amp; make verify-release</p>'
        "<p>The last command rebuilds this release from the pinned inputs and asserts the corpus_hash "
        "and rankings are bit-identical. A mismatch means the release is defective, and we want the challenge.</p>",
        "<h2>License</h2>"
        "<p>The pipeline code is MIT. The corpus and data downloads above are CC BY 4.0 "
        "(attribution: The AI Canon, Apparens). One exception: the verbatim paper abstracts remain "
        "the copyright of their authors and publishers, are quoted with their source so each paper "
        "can speak for itself, and are not covered by the CC BY grant. Rights holders can have an "
        'abstract removed on request: <a href="mailto:office@apparens.nl">office@apparens.nl</a>.</p>',
    ]
    return shell("data.html", "Data & audit", "Data & audit", "".join(body))


def _p(text):
    return "<p>" + esc(text) + "</p>"


# The About statement, verbatim. A module-level constant (not a function body) so
# page_about stays a one-liner; the pieces and their order are unchanged.
_ABOUT_BODY = [
    '<p class="lead">Why this exists, what it is, and how to read it.</p>',

    "<h2>Why I built it</h2>",
    _p("The literature of artificial intelligence is now larger than any one person can hold, "
       "and the maps we have are mostly selling something. Affiliate lists, vendor reading "
       "guides, threads ranked by who shouted loudest. Each asks you to trust the curator. "
       "Almost none let you check the curator's work."),
    _p("I build governance for a living. My one rule is that governance is not what you claim, "
       "it is what you can prove. A field this consequential deserves a reference work held to "
       "the same standard: a library whose every judgment can be inspected, questioned, and "
       "overturned with evidence. So I built the thing I wanted to exist and could not find. "
       "Not to own it. To give it."),
    _p("This is a public good. It is free, it always will be, and nothing in it is for sale."),

    "<h2>What I built</h2>",
    _p("A reference library of the texts that define artificial intelligence: the books, the "
       "papers, and the standards that shaped how we think, build, and govern it. Alongside the "
       "texts, a curated record of the people, organizations, and platforms that form the "
       "field's context."),
    _p("The rankings get the attention, but they are not the product. The library is the "
       "product. A ranking is one view of it, produced by a published method at a fixed date. "
       "The method is the part that matters. Anyone can assert that a book is important. The "
       "Canon shows its reasoning, names its sources, and invites you to prove it wrong."),
    _p("So the Canon is a reference work first and a ranking second. It answers why a text "
       "matters, what underpins it, and how it relates to the rest, before it answers which one "
       "is first."),

    "<h2>How it is constructed</h2>",
    _p("Two kinds of thing live here, and they are treated differently on purpose."),
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
    _p("By a person, with help from machines that are not allowed to decide anything."),
    _p("I adjudicate every challenge myself, against the evidence, and publish the resolution. "
       "I write the descriptions. Automated tools harvest the data, watch for changes, and "
       "propose updates, but no ranking ever moves without a human reviewing and approving it. "
       "The tools observe, assess, and escalate. They do not act. That distinction is the whole "
       "point of a canon you can trust rather than an algorithm you must accept."),
    _p("Every change is logged and nothing is ever quietly altered. Corrections become new "
       "versions; the old ones remain visible. I do not promise a schedule, because a schedule I "
       "would resent is a promise I would break. I promise the discipline instead: every update "
       "logged, every correction traceable, every ranking open to challenge, and no commercial "
       "influence of any kind, ever. The changelog is the proof. It cannot lie about whether the "
       "work is being done."),

    "<h2>Sources and acknowledgments</h2>",
    _p("The candidate corpus was seeded, with gratitude, from curated reading lists: Jurgen "
       "Appelo's AI reading list, the Monett Critical-AI reading list (14th edition), and the "
       "project's own candidate hunt. Seeding from a list is candidacy for scoring, not an "
       "endorsement by those curators, and it carries no weight in any ranking. The full "
       "per-work source is kept in the downloadable corpus data for transparency."),

    "<h2>Who it is for</h2>",
    _p("One library, many doors. A student opens it to find what to learn and in what order. A "
       "professor opens it to find what to teach. A journalist opens it to find who and what to "
       "research, and the record of who got things wrong. An investor opens it to read the "
       "landscape. An author or editor opens it to find the works that endure. A practitioner "
       "opens it to find the standards that govern their work."),
    _p("It is not built to flatter any of them, and not built to convert anyone into a customer, "
       "because there is nothing to buy. It is built to be useful and honest to all of them at "
       "once, the way a good library is."),

    "<h2>How it should be interpreted</h2>",
    _p("A rank is not a verdict on intrinsic worth. It is a transparent output of declared "
       "evidence, weights, and missing-data rules, at a specific release date. Read it as "
       "exactly that, and no more."),
    _p("A high rank means a text scored well on the evidence the method measured, under one set "
       "of weights, on one day. Change the weights and the order changes, which is why three "
       "different weightings are published rather than one. A low rank, or an absence, is not a "
       "judgment that a work is bad. It may mean the evidence is thin, the work is recent, or "
       "the method does not yet see it well. Inclusion in the seed corpus means a work is a "
       "candidate, not that it is canonical."),
    _p("If you disagree, you are not a nuisance. You are the mechanism. The Canon improves by "
       "being contested, and a challenge you can file is worth more than a ranking you are asked "
       "to believe."),

    "<h2>What you can do with it</h2>",
    _p("If you are here to learn AI, start with the library, not the ranking. Pick the domain "
       "you care about, governance or deep learning or the economics of automation, and read "
       "the texts that have endured there, in the order their descriptions suggest. Use the "
       "rankings as a second opinion, not a syllabus. Follow the connections: a book leads to "
       "the papers under it, the papers to the people who wrote them, the people to the "
       "institutions they work in. The structure is a map of how the field thinks, and you can "
       "walk it. Download the whole corpus as open data and keep it. It is yours."),
    _p("If you find yourself here as a subject, an author whose book is listed or a voice in the "
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


def page_about() -> str:
    return shell("about.html", "The AI Canon", "Statement", "".join(_ABOUT_BODY))


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
        f'<p>{esc("Most maps of AI thought only see half the field. You cannot understand artificial intelligence in 2026 by reading only what was written in English. The AI Canon is built, as a published rule, to score Chinese-language works within their own publishing and citation ecosystem before any cross-language comparison, rather than against English metrics that would erase them. That rule is written into the method; the mechanism that enforces it, and the Chinese corpus it needs, are still being built. Today the scored pilot is English-language papers, and the Chinese section is a curated spine of dozens of works that is openly under construction and not yet scored, with the project actively recruiting Chinese-literate scholars and readers to help build and verify it. The story is not a finished global canon. It is a Western-built reference work that is structurally committed to including China and is openly asking Chinese experts to help, at a moment when most Western and Chinese AI discourse barely acknowledge each other.")}</p>',
        "<h2>Quotable, attributable to Jeroen Janssen</h2>",
    ]
    body += [f'<p class="pullquote">{esc(q)}</p>' for q in quotes]
    body += [
        "<h2>What you can verify before you publish</h2>",
        f'<p>{esc("The method, the ontology, the full corpus, and the audit files are open. The challenge log is public. There is no advertising, no affiliate income, and no paid placement anywhere in the project, by design and by rule. It is a non-commercial public good; there is nothing to buy and no upsell to find.")}</p>',
        f'<p>{esc("The builder\'s own book, The AI Accountability Trap, is in the corpus and carries a visible conflict flag, subject to the same rules as everything else, with no exemption and no boost. Books carry no metrics yet, so no book, this one included, is scored.")}</p>',
        "<h2>Contact</h2>",
        '<p>Jeroen Janssen, Apparens (Deventer, Netherlands). <a href="mailto:office@apparens.nl">office@apparens.nl</a>.</p>',
        '<p>If you want to share this rather than write about it, see the <a href="share.html">share page</a>.</p>',
    ]
    return shell("press.html", "For press and writers", "Press", "".join(body))


def page_share() -> str:
    body = [
        share_row("", "Share the Canon"),
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


def page_search() -> str:
    body = (
        '<p class="note">Search the whole corpus: 610 books, 269 papers, the models index, and the voices, '
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
