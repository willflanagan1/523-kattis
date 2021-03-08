window.addEventListener("load", () => {

  // render equations
  for (const m of /** @type {HTMLElement[]}*/ (Array.from(document.getElementsByClassName("math")))) {
    katex.render(m.innerText, m);
  }
});
