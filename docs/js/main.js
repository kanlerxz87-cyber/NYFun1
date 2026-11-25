// Minimal JS: highlight active nav link
(function(){
  var path = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav a[data-page]').forEach(function(a){
    if(a.getAttribute('data-page')===path) a.classList.add('active');
  });
})();
