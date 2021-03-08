function sqlFormatRow(row) {
  return '(' + row.map(sqlFormatItem).join(',') + ')';
}

function sqlFormatItem(item) {
  if (Number.isInteger(item)) {
    return '' + item;
  } else if (typeof(item) === 'number') {
    return item.toFixed(2);
  } else {
    return '"' + item.replace('"', '\\"') + '"';
  }
}

function hash_sql(data, sortRows) {
  let ncolumns = data[0].columns.length,
      nrows = data[0].values.length,
      formatedRows = data[0].values.map(sqlFormatRow);
  if (sortRows) {
    formatedRows.sort();
  }
  let stringRows = formatedRows.join(',');
  let theHash = fnv32a(stringRows);
  return {ncolumns:ncolumns, nrows:nrows, hash:theHash};
}

// run function in a timer to allow UI to update
function updateUI(func) {
  return new Promise(resolve => {func(); setTimeout(resolve, 1)});
}

async function validate_sql(node) {
  let $fieldset = $(node);
  let $textarea = $fieldset.find('textarea');
  let sortRows = $fieldset.attr('data-sort') == '1';
  let expected = JSON.parse($fieldset.attr('data-expected'));
  let value = $textarea.val();
  let $output = $fieldset.find('.sqloutput');
  // give the UI a chance to update
  if (!value.trim()) {
    return;
  }
  await updateUI(() => $output.html('Working'))
  sqldbs.some((db, i) => {
    try {
      res = db.exec(value);
      // clear the working message
      i == 0 && $output.empty();
    } catch(error) {
      let msg = document.createElement('div');
      msg.className = 'sqlerror';
      msg.appendChild(document.createTextNode(error.message));
      // clear the working message
      i == 0 && $output.empty();
      $output.append(msg);
      return true;
    }
    let yourResult = hash_sql(res,sortRows);
    let expectedResult = expected[i];
    let table = datatable(res, yourResult.hash == expectedResult.hash);
    $output.append(table);
  });
}

function sqlconnect(names) {
  window.extraPromises.push(
    Promise.all(names.map(async name => {
      let fresp = await fetch(name);
      let uInt8Array = await fresp.arrayBuffer();
      uInt8Array = new Uint8Array(uInt8Array);
      db = new SQL.Database(uInt8Array);
      return db;
    })).then(dbs => window.sqldbs = dbs)
  );
}

  // after they are all loaded validate the inputs
  /*
  $(function() {
    $('fieldset.sql').each(function(i, node) { validate_sql(node); });
  });
  */
function esc(s) {
  s = '' + s;
  return s.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function datatable (data, correct) {
  var tbl = document.createElement("table");
  tbl.className = 'datatable'
  if (correct) {
    tbl.style = "background:palegreen";
  }

  var header_labels = data[0].columns;
  for (var idx in header_labels) {
    var col = document.createElement('col');
    col.className = esc(header_labels[idx]);
    tbl.appendChild(col);
  }

  // create header row
  var thead = tbl.createTHead();
  var row = thead.insertRow(0);
  for (var idx in header_labels) {
    var cell = row.insertCell(idx);
    cell.innerHTML = esc(header_labels[idx]);
  }

  // fill table body
  var tbody = document.createElement("tbody");
  for (var row_idx in data[0]['values']) {
    var body_row = tbody.insertRow();
    for (var header_idx in header_labels) {
      var body_cell = body_row.insertCell();
      body_cell.appendChild(document.createTextNode(data[0]['values'][row_idx][header_idx]));
    }
  }
  tbl.appendChild(tbody);
  return tbl;
}
