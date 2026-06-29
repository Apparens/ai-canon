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
