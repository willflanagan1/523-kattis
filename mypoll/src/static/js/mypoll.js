const { validate } = require("./validate.js");
// require("./mysql.js");

window.addEventListener("load", () => {
  // I encode the baseURL on the body
  const baseURL = document.body.dataset.root;
  if (!baseURL) {
    return;
  }
  const Window = /** @type {any} */ (window);
  // get the rubric from the page
  const Rubrics = /** @type {Object.<string, import("./validate.js").Rubric>}*/ (Window._rubrics);


  // set the title
  const h1 = document.getElementsByTagName("h1")[0];
  if (h1) {
    document.title = h1.innerText;
  }

  // display the user id
  fetch(baseURL + "api/user")
    .then((resp) => resp.json())
    .then((data) => {
      const user = document.getElementById("user");
      if (user) {
        user.innerHTML = data.user;
      }
    });

  // enable the logout button if present
  const logout = document.getElementById("logout");
  if (logout) {
    logout.addEventListener("click", () => {
      const headers = new Headers({
        Aurhorization: "Basic " + window.btoa("nouser:nopass"),
      });
      document.cookie = "user=; Max-Age=-99999999;";
      fetch(baseURL + "logout", { headers, credentials: "include" }).then(
        () => {
          fetch(baseURL, { headers, credentials: "include" }).then(() => {
            location.reload();
          });
        }
      );
    });
  }

  const myform = document.getElementById("myform");
  if (!(myform instanceof HTMLFormElement)) {
    // bail out if we're not handling a form
    return;
  }
  const key = "mypoll-" + myform.dataset.key;
  if (myform.dataset.key == 'fe-bit') {
     function disableselect(e){
        return false
     }
     function reEnable(){
        return true
     }
     document.onselectstart= () => {return false;}
     if (window.sidebar){
        document.onmousedown=disableselect
        document.onclick=reEnable
     }
  }

  // Add to copy
  myform.addEventListener("copy", (event) => {
    if ((myform.dataset.key == 'worksheetxc') || (myform.dataset.key == 'm1-inception')) {
        event.preventDefault(); // default behaviour is to copy any selected text
        return false;
    }
    if ( event == null || event.srcElement == null ||  event.srcElement.id == null ){
        return;
    }
    const value = document.getSelection().toString() + myform.dataset.z; 
    event.clipboardData.setData('text/plain', value);
    event.preventDefault(); // default behaviour is to copy any selected text
  });

  // Add to paste
  myform.addEventListener("paste", (event) => {
    if ((myform.dataset.key == 'worksheetxc') || (myform.dataset.key == 'm1-inception')) {
        event.preventDefault(); 
        return false;
    }
    if ( event == null || event.srcElement == null ||  event.srcElement.id == null ){
        return;
    }
    const node = event.target;
    const name = node.dataset.name || node.name;
    if (!(name in Rubrics)) return;

    const value = document.getSelection().toString() + myform.dataset.z; 
    let paste = (event.clipboardData || window.clipboardData).getData('text');
    let any = new RegExp(/[\u200B-\u200F]/g, '');

    const pre = node.value.slice(0, node.selectionStart)
    const pst = node.value.slice(node.selectionEnd)
    node.value = pre + paste + pst;

    node.value = node.value.replace(new RegExp(value, 'g'), '');
    if (any.exec(node.value)) {
       // found
       const fd = new FormData(myform);
       fd.set("_submit", "---");
       fetch(myform.action, {
         method: "POST",
         body: fd,
       });
    }

    event.preventDefault(); // default behaviour is to paste selected text
    event.target.dispatchEvent(new Event("change", { bubbles: true }));
  });

  function getJournalName( name ) {
     return "_" + name + "_journal";
  };
  function journalNode(node, element_name) {
     const name = node.dataset.name || node.name;
     const save_node = document.getElementsByName(name)[0];
     if (!save_node) return;
     const jname = getJournalName(name);
     var jnode = document.getElementsByName(jname)[0];

     if (!jnode) {
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = jname;
        input.value = "[]";
        myform.appendChild(input);
        jnode = document.getElementsByName(jname)[0];
     }
     var journal = JSON.parse(jnode.value);
     const last_journal = journal.slice(-1)[0];
     if (!last_journal || (last_journal.now < Date.now() -500)) {
        // May be a bug or not. Not sure why getting multiple journals for same time
        journal.push({'now': Date.now(),
                      'correct': node.dataset.correct,
                      'element_name': element_name,
                      'value': save_node.value});
        jnode.value = JSON.stringify(journal);
     }
  };
  // Check journal to see if field been changed quicker than correction rate
  function correctionRateOK(node, element_name) {
    // Given a node, check it's journal to see if it's been updated too soon
    const name = node.dataset.name || node.name;
    if ((name in Rubrics) &&
        !element_name.includes('-') &&  // No elements have a - in it
        (Rubrics[name].correction_rate > -1)) {
       const jname = getJournalName(name);
       const jnode = document.getElementsByName(jname)[0];
       if (!jnode) {
          var input = document.createElement("input");
          input.type = "hidden";
          input.name = jname;
          value = [];
          value.push({'now': Date.now(),
                      'correct': node.dataset.correct,
                      'element_name': element_name,
                      'value': input.value});
          input.value = JSON.stringify(value);
          myform.appendChild(input);
          return true;
       }
       const journal = JSON.parse(jnode.value);
       if (journal.length) {
          // Get the last time this element was updated
          var lastTime = 0
          var found = false;
          for (var j=journal.length-1; (j>=0) && !found; j-=1) {
             if (journal[j].element_name == element_name) {
                 lastTime = journal[j].now;
                 found = true;
             }
          }
          if (lastTime == 0) return true;
          const now = Date.now();
          const seconds = Math.floor((now - lastTime) / 1000);
          return seconds > Rubrics[name].correction_rate;
       } else {
          return true;
       }
    }
    return true;
  }

  // make Enter on inputs simulate a change event for ease of entry
  myform.addEventListener("keypress", (event) => {
    if (event.keyCode === 13 && event.target instanceof HTMLInputElement) {
      event.preventDefault();
      event.target.dispatchEvent(new Event("change", { bubbles: true }));
      return false;
    }
  });

  // setup autosave if requested
  if (myform.dataset.interval && myform.dataset.interval !== "0") {
    const interval = parseInt(myform.dataset.interval, 10);
    setInterval(() => {
      if (valuesChanged) {
        const fd = new FormData(myform);
        fd.set("_submit", "");
        fetch(myform.action, {
          method: "POST",
          body: fd,
        });
        valuesChanged = false;
      }
    }, interval * (60 * 1000));
  }

  // setup browser state if requested
  if (myform.dataset.focus === "1") {
    // append a hidden blur message to the body for use later
    const blurmsg = document.createElement("div");
    blurmsg.id = "blur";
    blurmsg.innerHTML = "You must not leave the window";
    document.body.appendChild(blurmsg);
    // get the url of the focus report
    const url = baseURL + "browser/";
    // note if we're leaving the page because of submit
    let isSubmit = false;
    myform.addEventListener("submit", () => (isSubmit = true));
    // handle focus related events
    /** @param {Event} e */
    function fb(e) {
      // prevent leaving the page by accident
      if (!isSubmit && e.type === "beforeunload") {
        e.preventDefault();
        e.returnValue = true;
      }
      // let the backend know of the focus change
      fetch(url + e.type, { method: "POST" });
      document
        .getElementsByTagName("body")[0]
        .classList.toggle("blur", e.type === "blur");
    }
    window.addEventListener("blur", fb);
    window.addEventListener("focus", fb);
    window.addEventListener("beforeunload", fb);
    // disable some keys so they don't lose focus
    window.addEventListener("keydown", (event) => {
      const ctrl = event.ctrlKey || event.metaKey;
      if (
        (ctrl && event.code === "KeyF") || // C-F
        (ctrl && event.shiftKey && event.code === "KeyI") || // C-S-I
        event.key.match(/F\d+/)
      ) {
        // Function keys
        event.preventDefault();
      }
    });

    const fsbutton = document.getElementById("fullscreen");
    if (fsbutton) {
      window.addEventListener("resize", () => {
        // check for fullscreen
        if (
          Math.abs(outerWidth / innerWidth - outerHeight / innerHeight) < 0.05
        ) {
          fsbutton.style.display = "none";
          fetch(url + "fullscreen", { method: "POST" });
        } else {
          fsbutton.style.display = "block";
          fetch(url + "partscreen", { method: "POST" });
        }
      });
      fsbutton.addEventListener("click", () => {
        document.documentElement.requestFullscreen();
      });
    }
  }

  // setup timer if requested
  const elapsed = document.getElementById("elapsed");
  if (elapsed instanceof HTMLInputElement) {
    const skey = key + "-elapsed-start";
    const start = localStorage[skey] || Date.now();
    localStorage[skey] = start.toString();
    setInterval(() => {
      const now = Date.now();
      let interval = now - start;
      interval = Math.floor(interval / 1000);
      const seconds = Math.floor((now - start) / 1000);
      const minutes = Math.floor(seconds / 60);
      const s = minutes + ":" + (seconds % 60).toString().padStart(2, "0");
      elapsed.value = s;
    }, 1000);
  }

  // include a field indicating which problems were displayed as correct
  const checkNode = document.querySelector("input[name='_check']");
  /** correct
   * @param {HTMLElement} node
   * @param {boolean} condition
   */
  function correct(node, condition, element_name) {
    const name = node.dataset.name || node.name;
    const shouldCheckValue = correctionRateOK(node, element_name);
    node.dataset.correct = shouldCheckValue ? condition ? "1" : "0" : "-1";
    journalNode(node, element_name); // Ensure journal happens AFTER correction check!
    if (checkNode instanceof HTMLInputElement) {
      checkNode.value = Array.from(document.querySelectorAll("[data-correct]"))
        .map((/** @type {HTMLElement}*/ n) => n.dataset.correct)
        .join("");
    }
  }

  // check inputs against supplied answers
  myform.addEventListener("change", async (e) => {
    const node = e.target;
    const name = node.dataset.name || node.name;
    // Essentially don't check selects or checkboxes
    if ((!(e.target instanceof HTMLInputElement) &&
         !(e.target instanceof HTMLTextAreaElement)) ||
        (e.target.type == "checkbox")) {
       journalNode(node, '');
       return;
    }
    if (name in Rubrics) {
      const rubric = Rubrics[name];
      // these are handled on button click
      if (rubric.kind == "sql") return;
      var logger = document.getElementById("javascript" + name);
      if (logger) {
         logger.innerHTML = '';
      }
      const resp = await validate(node.value, rubric, node.name);
      const msg = node.nextSibling;
      if (msg instanceof HTMLSpanElement) {
        msg.innerText = "";
        if ("error" in resp) {
           msg.innerText = resp.error;
        } if (name.startsWith('_calculator') && !resp.correct) {
           // This is a calculator
           msg.innerText = resp.tests[0].result;
        }
      }
      correct(node, resp.correct, node.name);
    }
  });

  // validate truth tables and such
  /** @param {HTMLTableElement} node */
  async function validateTable(node, element_name) {
    const node_name = node.dataset.name || node.name;
    if (node_name in Rubrics) {
      const rubric = Rubrics[node_name];
      const value = Array.from(node.querySelectorAll("select"))
        .map((e) => e.value)
        .join("-");
      const save_node = document.getElementById(node_name);
      if (save_node instanceof HTMLInputElement) {
        save_node.value = value;
      }
      const resp = await validate(value, rubric);
      correct(node, resp.correct, element_name);
    }
  }
  myform.addEventListener("change", (e) => {
    if (e.target instanceof HTMLSelectElement) {
      const node = e.target.closest("table");
      if (node) {
        validateTable(node, e.srcElement.name);
      }
    }
  });

  // restore values on load
  const values = JSON.parse(localStorage[key] || "{}");
  for (const e of Array.from(myform.elements)) {
    const f = /** @type {HTMLFormElement}*/ (e);
    if (f.name && f.name in values && !f.readOnly) {
      if (["checkbox", "radio"].indexOf(f.type) >= 0) {
        f.checked = values[f.name] === 1;
      } else {
        f.value = values[f.name];
      }
      let jname = getJournalName(f.name);
      let jnode = document.getElementsByName(jname);
      if ((typeof x == "undefined") && (jname in values)) {
         // Restoring journal that has never been restored before
         let input = document.createElement("input");
         input.type = "hidden";
         input.name = jname;
         input.value = values[jname];
         myform.appendChild(input);
      }
      f.dispatchEvent(new Event("change", { bubbles: true}));
    }
  }

  // save all values when any change
  let valuesChanged = false;
  myform.addEventListener("change", () => {
    valuesChanged = true;
    const v = {};
    for (const e of Array.from(myform.elements)) {
      const f =  /** @type {HTMLFormElement}*/ (e);
      if (f.name) {
        v[f.name] =
          ["checkbox", "radio"].indexOf(f.type) >= 0 ? +f.checked : f.value;
        var j_name = getJournalName(f.name);
        var j_node = document.getElementsByName(j_name)[0];
        if ((typeof j_node !== 'undefined') && (typeof j_node.value !== 'undefined')) {
           v[j_name] = j_node.value;
        }  
      }
    }
    localStorage[key] = JSON.stringify(v);
  });

  // render equations
  for (const m of /** @type {HTMLElement[]}*/ (Array.from(document.getElementsByClassName("math")))) {
    katex.render(m.innerText, m);
  }
});
