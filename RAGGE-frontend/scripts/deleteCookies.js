const closeCookie = document.getElementById('delete-cookies');

closeCookie.addEventListener('click', () => {
    console.log('delete cookies');
    document.cookie = 'cookie=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';

    // redirect to home page;
    window.location.href = '/';
});

function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
      }
    }
    return "";
  }