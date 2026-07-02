"""The external JS bundles (the strict CSP forbids inline script) and the
search-index builder that feeds the in-browser search."""

from __future__ import annotations

import json

from .pages_corpus import _model_slug

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


def _search_index_js(books, papers, scored, persons, orgs, platforms, models_index) -> str:
    """The embedded search index, one entry per corpus item: type, label, sub, url."""
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
    for m in models_index["models"]:
        meta = " · ".join(x for x in [m.get("lab", ""), m.get("country", "")] if x)
        si.append({"t": "model", "l": m["name"], "s": meta, "u": "models.html#" + _model_slug(m["name"])})
    return ("window.CANON_INDEX=" + json.dumps(si, ensure_ascii=False, separators=(",", ":"))
            .replace("</", "<\\/") + ";\n")
