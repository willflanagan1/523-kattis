/* evaluate and hash sqlite queries
 *
 * I want this to work both in the browser and in node.
 */

// I'll cache downloaded and opened dbs here
const dbs = {};

if (typeof importScripts === "function") {
  // web worker
  importScripts("./workerpool.js", "./sql-wasm.js", "./myhash.js");

  var getDb = async function (/** @type {string} */ name) {
    // initialize sqlite, I'm hoping it only happens once
    const SQL = await initSqlJs();
    // if it isn't in the cache load it
    if (!(name in dbs)) {
      // in the browser I'm using fetch to get the database
      let resp = await fetch(name);
      let buffer = await resp.arrayBuffer();
      let uIntArray = new Uint8Array(buffer);
      let db = new SQL.Database(uIntArray);
      dbs[name] = db;
    }
    // return the opened db from the cache
    return dbs[name];
  };
} else {
  // node.js
  var workerpool = require("workerpool");
  var initSqlJs = require("./sql-wasm.js");
  var { hash } = require("./myhash.js");
  var fs = require("fs");
  var SQL = null;
  var getDb = async function (/** @type {string} */ name) {
    if (!SQL) {
      SQL = await initSqlJs();
    }
    if (!(name in dbs)) {
      // in node.js I'm reading from the file system
      // hack the name to make it work on the filesystem
      let buffer = fs.readFileSync("." + name.replace(/\?.*$/, ""));
      let db = new SQL.Database(buffer);
      dbs[name] = db;
    }
    return dbs[name];
  };
}

/** @typedef {string|number} dbItem */

/** @typedef {dbItem[]} dbRow */

/** @typedef {Object} dbResult
 * @property {string[]} columns
 * @property {dbRow[]} values
 */

/** @typedef {Object} evalSQLresult
 * @property {dbResult} result
 * @property {string} hash
 */

/** sqlFormatItem - format a single value for hashing
 * @param {dbItem} item
 * @returns {string}
 */
function sqlFormatItem(item) {
  if (typeof item === "number") {
    if (Number.isInteger(item)) {
      return "" + item;
    }
    return item.toFixed(2);
  } else {
    return '"' + item.replace('"', '\\"') + '"';
  }
}

/** sqlFormatRow - format a row from the database
 * @param {dbRow} row
 * @returns {string}
 */
function sqlFormatRow(row) {
  return "(" + row.map(sqlFormatItem).join(",") + ")";
}

/** hashDbResult - take database result and hash it
 * @param {dbResult} data - value returned by sql.exec
 * @param {boolean} sortRows - true to sort rows before hashing
 * @returns {string}
 */
function hashDbResult(data, sortRows) {
  let formatedRows = data[0].values.map(sqlFormatRow);
  if (sortRows) {
    formatedRows.sort();
  }
  let stringRows = formatedRows.join(",");
  let theHash = hash(stringRows);
  return theHash;
}

/** evalSQL - evaluate an sql query with the given db
 * @param {string} code
 * @param {string} dbName
 * @param {boolean} sortRows - true to sort before hashing
 * @returns {Promise<evalSQLresult>}
 */
async function evalSQL(code, dbName, sortRows) {
  const db = await getDb(dbName);
  const result = db.exec(code);
  const hash = hashDbResult(result, sortRows);
  return { result, hash };
}

/** prefetch - prefetch a database to avoid timeouts in evalSQL
 * @param {string} dbName
 */
async function prefetch(dbName) {
  await getDb(dbName);
  return "ok";
}

workerpool.worker({
  evalSQL: evalSQL,
  prefetch: prefetch,
});
