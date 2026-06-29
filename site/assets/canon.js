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
