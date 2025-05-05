// utils.js
function debounce(fn, delay) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  }
  
  function fetchCheck(url) {
    return fetch(`http://localhost:5050/check?url=${encodeURIComponent(url)}`)
      .then(res => res.json());
  }