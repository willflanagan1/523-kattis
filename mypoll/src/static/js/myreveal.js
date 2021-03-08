function insertActivePages(key, onyen, section, activepages) {
   const fd = new FormData();
   fd.append('key', key);
   fd.append('onyen', onyen);
   fd.append('section', section);
   fd.append('activepages', activepages);

   fetch("/mypoll/insertActivePages", {method: 'post', body: fd});
}
function deleteActivePages(key, onyen, section) {
   const fd = new FormData();
   fd.append('key', key);
   fd.append('onyen', onyen);
   fd.append('section', section);

   fetch("/mypoll/deleteActivePages", {method: 'post', body: fd});
}
