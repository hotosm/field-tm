export function setCookie(name: string, value: string) {
  document.cookie = `${name}=${value}; Path=/;`;
}

// export function removeCookie(name, domain = '') {
//   document.cookie = `${name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT; domain=${domain}`;
// }

export function removeCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:01 GMT"`;
}

export default function getCookie(name: string) {
  let cookieValue: string | null = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i += 1) {
      const cookie = cookies[i].toString().replace(/^([\s]*)|([\s]*)$/g, '');
      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
