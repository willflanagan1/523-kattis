"use strict";
(() => {
    // attempt to detect errors during loading the page to warn
    // students they need to refresh to try again.
    //
    // I need to do this part early in the page load to make sure
    // everything gets caught
    //
    // accumulate the errors
    const errors = [];
    window.addEventListener('error', (e) => {
        errors.push(e);
    }, true);
    window.addEventListener('load', () => {
        const loading = document.getElementById('loading');
        if (!loading) {
            // how can this happen?
            return;
        }
        if (errors.length > 0) {
            loading.innerHTML = 'Loading failed, refresh the page';
            for (const e of errors) {
                const p = document.createElement('p');
                if (e.message) {
                    p.innerHTML = e.message;
                }
                else {
                    const t = e.target;
                    let url;
                    if (t instanceof HTMLLinkElement) {
                        url = t.href; // css
                    }
                    else if (t instanceof HTMLScriptElement) {
                        url = t.src; // scripts
                    }
                    else {
                        url = 'something'; // not sure this can happen
                    }
                    const msg = `${t.tagName}: ${url} failed to load`;
                    p.innerHTML = msg;
                }
                loading.appendChild(p);
            }
        }
        else {
            loading.style.display = 'none';
            const pagebody = document.getElementById('pagebody');
            if (pagebody) {
                pagebody.style.display = 'block';
            }
        }
    });
})();
//# sourceMappingURL=monitorloading.js.map