const { hash } = require("./myhash.js");

/** @typedef {Object} LiteralRubric
 * @property {"text"|"decimal"|"hex"|"binary"|"table"} kind
 * @property {string} [solution]
 * @property {number} [points]
 * @property {boolean} [preserveCase]
 * @property {boolean} [preserveZeros]
 * @property {boolean} [preserveSpaces]
 * @property {string} [expectedHash]
 * @property {string} [result]
 * @property {string} [resultHash]
 * @property {boolean} [correct]
 * @property {string} [error]
 */

/** @typedef {Object} RubricTest
 * @property {Object} context
 * @property {string} [resultHash]
 * @property {string} [expectedHash]
 * @property {boolean} [correct]
 * @property {string} [result]
 */

/** @typedef {Object} ExpressionRubric
 * @property {"expression"|"function"} kind
 * @property {string} [solution]
 * @property {number} [points]
 * @property {RubricTest[]} tests
 * @property {boolean} [correct]
 * @property {string} [error]
 */

/** @typedef {Object} SQLTest
 * @property {string} db
 * @property {string} [resultHash]
 * @property {string} [expectedHash]
 * @property {boolean} [correct]
 * @property {import("./sqlWorker.js").dbResult} [result]
 */

/** @typedef {Object} SQLRubric
 * @property {"sql"} kind
 * @property {string} [solution]
 * @property {number} [points]
 * @property {SQLTest[]} tests
 * @property {boolean} [sort]
 * @property {number} [timeout]
 * @property {boolean} [correct]
 * @property {string} [error]
 */

/** @typedef {Object} SelectRubric
 * @property {"select"|"checkbox"} kind
 * @property {string} [solution]
 * @property {number} [points]
 * @property {string[]} [choices]
 * @property {boolean} [correct]
 */

/** @typedef {LiteralRubric | ExpressionRubric | SQLRubric | SelectRubric } Rubric
 */

/** @typedef {Object} CheckResult
 * @property {string} [expectedHash]
 * @property {string} [resultHash]
 * @property {boolean} [correct]
 */

/* example callback, you can provide your own in the context */
/* you'd have some function to reset these */
let iterations = 0;
let start = Date.now();
let limit = 2 * 1000; // 2 seconds

/* this gets called on each iteration */
function _loop() {
  iterations += 1;
  let t = Date.now();
  if (t - start > limit) {
    console.log("Throw timeout iterations=", iterations, "start=", start, "now=", t, "limit=", limit);
    throw "Execution Timeout";
  }
}

/* Get control at each function call */
let functionDict = {};
function _func(name, callsResult) {
  functionDict[name] = (functionDict[name] || 0) + 1;
  return callsResult;
}

/** format results for checking or constructing answers
 * @param {string} expectedHash
 * @param {string} resultHash
 * @returns {CheckResult}
 */
function check(expectedHash, resultHash) {
  let correct = expectedHash == resultHash;
  if (typeof expectedHash == "string") {
    return { correct, expectedHash, resultHash };
  } else {
    return { expectedHash: resultHash };
  }
}

/** include correct if all tests include it
 * @typedef {Object} testResult
 * @property {boolean} [correct]
 * @property {any} [result] - why do I need this?

 * checkTests - see if all the tests passed
 * @param {testResult[]} tests
 * @returns {Object}
 * @property {boolean} [correct]
 */
function checkTests(tests) {
  if (tests.every(t => "correct" in t)) {
    return { correct: tests.every(t => t.correct) };
  }
  return {};
}

/** validate user inputs for mypoll
 * @param {string} input
 * @param {Rubric} rubric
 * @param {string} nodeName
 * @returns {Promise<Rubric>}
 */
async function validate(input, rubric, nodeName) {
  let normalized = input.trim();
  if (!normalized.length) {
    return { ...rubric, correct: false };
  }
  switch (rubric.kind) {
    case "text":
      if (!rubric.preserveCase) {
        normalized = normalized.toUpperCase();
      }
      if (!rubric.preserveSpaces) {
        normalized = normalized.replace(/\s+/g, "");
      }
      return {
        ...rubric,
        result: normalized,
        ...check(rubric.expectedHash, hash(normalized))
      };
    case "decimal":
    case "hex":
    case "binary":
      let pattern = {
        decimal: /^[\d.]+$/,
        hex: /^[0-9A-F.]+$/,
        binary: /^[01.]+$/
      }[rubric.kind];
      normalized = input.toUpperCase();
      if (!pattern.test(normalized)) {
        return { ...rubric, error: "invalid character" };
      }
      if (!rubric.preserveZeros) {
        // replace 0's before first nonzero digit
        normalized = normalized.replace(/^0+(?=.)/, "");
        // drop .0* from the right end
        normalized = normalized.replace(/\.0*$/, "");
        // drop trailing 0's after a point
        normalized = normalized.replace(/(\..*)0+/, "$1");
      }
      return {
        ...rubric,
        result: normalized,
        ...check(rubric.expectedHash, hash(normalized))
      };

    case "select":
      if ("solution" in rubric) {
        return { ...rubric, correct: input == rubric.solution };
      }
      return { ...rubric, correct: false };
    case "table":
      return { ...rubric, ...check(rubric.expectedHash, hash(input)) };

    case "checkbox":
      if ("solution" in rubric) {
        return { ...rubric, correct: input == rubric.solution };
      }
      return { ...rubric, correct: false };

    case "expression":
      return validateExpression(input, rubric, nodeName);

    case "function":
      return validateFunction(input, rubric, nodeName);

    case "sql":
      return validateSQL(input, rubric);
  }
}

const Babel = require("babel-core");
/** validate user expression in context
 * @param {string} expr
 * @param {ExpressionRubric} rubric
 * @returns {Rubric}
 */

function myPush(x,y) {
   return x.push(y);
}
function myLen(x) {
   return x.length;
}
function myT(x) {
   return x ** (2/3);
}
function myEmptyDict() {
   return {};
}
function myS(x) {
   return x ** (2/6);
}
function BigOh(x) { return Math.cbrt(x); }
function LittleOh(x) { return x ** (1/5);}
function Theta(x) { return x ** (1/4);   }
function Omega(x) { return x**2;         }
function LittleOmega(x) { return x**3;   }
function lg(x) { return log(x) / log(Math.E); }
function factorial(num) {
  if (num < 0)
        return -1;
  else if (num == 0)
      return 1;
  else {
      return (num * factorial(num - 1));
  }
}
function assert(condition, message) {
  if (!condition) {
     message = message || "Assertion failed";
     if (typeof Error !== "undefined") {
        throw new Error(message);
     }
     throw message;
  }
}

function validateExpression(expr, rubric, nodeName) {

  // some functions that are always available
  const functions = {
    BigOh: BigOh,
    LittleOh: LittleOh,
    Theta: Theta,
    Omega: Omega,
    LittleOmega: LittleOmega,
    lg:  Math.log,
    factorial: factorial,
    assert: assert,
    len: myLen,
    push: myPush,
    T: myT,
    S: myS,
    INFINITY: 99999999999999999999999999999999,

    log: Math.log,
    log10: Math.log10,
    log2: Math.log2,
    sqrt: Math.sqrt,
    ceiling: Math.ceil,
    floor: Math.floor,
    abs: Math.abs,
    max: Math.max,
    _loop: _loop
  };

  // Remove the ZWSP from func
  expr = expr.replace(/[\u200B-\u200F]/g, '');

  const tests = []; // outgoing test results
  for (const test of rubric.tests) {
    let context = Object.assign({}, functions, test.context);
    iterations = 0;
    start = Date.now();

    // hacked from https://medium.com/@bvjebin/js-infinite-loops-killing-em-e1c2f5f2db7f
    let transformer = () => {
      function notAllowed(path) {
        throw path.buildCodeFrameError("Not allowed " + path.type);
      }
      return {
        visitor: {
          WhileStatement: notAllowed,
          DoWhileStatement: notAllowed,
          ForStatement: notAllowed,
          MemberExpression: notAllowed,
          ObjectExpression: notAllowed,
          NewExpression: notAllowed,
          AssignmentExpression: notAllowed,
          ArrowFunctionExpression: notAllowed,
          BlockStatement: notAllowed,
          ConditionalExpression: notAllowed,
          // prevent global variables
          Identifier(path) {
            let name = path.node.name;
            if (name in context || path.scope.hasBinding(name)) {
              return;
            }
            throw path.buildCodeFrameError("No globals " + name);
          },
          // prevent XOR operator as confuses students with **
          BinaryExpression(path) {
             if (path.node.operator == "^") {
                throw path.buildCodeFrameError("Bitwise XOR (^) not allowed in pseudocode.");
             }
          }
        }
      };
    };

    // transform the user's code
    try {
      var tfunc = Babel.transform(`(${expr})`, { plugins: [transformer] }).code;
    } catch (e) {
      return { ...rubric, error: !e.message ? e : e.message };
    }
    tfunc = `return ${tfunc}`;
    try {
      var result = new Function(...Object.keys(context), tfunc)(
        ...Object.values(context)
      );
    } catch (e) {
      return { ...rubric, error: e.message };
    }

    // round if requested
    let toHash = result;
    if (typeof result == "number") {
      if (result == Math.floor(result)) {
        toHash = result.toString();
      } else {
        result = Number.parseFloat(result).toFixed(context._digits || 3);
        if (result == Math.floor(result)) {
           toHash = Math.floor(result).toString();
        } else {
           toHash = result;
        }
      }
    }
    tests.push({
      ...test,
      result: toHash,
      ...check(test.expectedHash, hash(toHash))
    });
  }
  return { ...rubric, tests, ...checkTests(tests) };
}

/*
 * run student code in a context
 * prevent infinite loops
 * count iterations
 */

/** validate user expression in context
 * @param {string} func
 * @param {ExpressionRubric} rubric
 * @returns {Rubric}
 */
function validateFunction(func, rubric, nodeName) {
  // hack from https://stackoverflow.com/questions/20256760/javascript-console-log-to-html/20256785
  if ((typeof document != 'undefined') && nodeName && document.getElementById("javascript" + nodeName)) {
     (function () {
         var old = console.log;
         var logger;
         try {
            logger = document.getElementById("javascript" + nodeName);
         } catch(e) {
            logger = console.error
         }
         myPrint = function (...args) {
             for (var i=0; i<args.length; i++) {
                if (typeof args[i] == 'object') {
                    logger.innerHTML += " " + (JSON && JSON.stringify ? JSON.stringify(args[i]) : args[i]);
                } else {
                    logger.innerHTML += " " + args[i];
                }
             }
             logger.innerHTML += '<br />';
         }
         // myPrint = function (...args) {
         //     for (const i=0; i<args.length; i++) {
         //         if (typeof args[i] == 'object') {
         //             logger.innerHTML += (JSON && JSON.stringify ? JSON.stringify(args[i]) : args[i]);
         //         } else {
         //             logger.innerHTML += " " + args[i];
         //         }
         //     }
         //     logger.innerHTML += '<br />';
         // }
     })();
  } else {
     myPrint = console.error
  }

  // some functions that are always available
  const functions = {
    BigOh: BigOh,
    LittleOh: LittleOh,
    Theta: Theta,
    Omega: Omega,
    LittleOmega: LittleOmega,
    lg:  Math.log,
    factorial: factorial,
    assert: assert,
    len: myLen,
    push: myPush,
    print: myPrint,
    T: myT,
    S: myS,
    INFINITY: 99999999999999999999999999999999,

    log: Math.log,
    log10: Math.log10,
    log2: Math.log2,
    sqrt: Math.sqrt,
    ceiling: Math.ceil,
    floor: Math.floor,
    abs: Math.abs,
    max: Math.max,
    emptyDictionary: myEmptyDict,
    _func: _func,
    _loop: _loop,
  };

  // Remove the ZWSP from func
  func = func.replace(/[\u200B-\u200F]/g, '');

  const tests = [];
  for (const test of rubric.tests) {
    let context = Object.assign({}, functions, test.context);
    iterations = 0;
    functionDict = {};
    start = Date.now();
    const args = context._args;
    delete context._args;
    if ('_m' in context) {
       m = {};
       delete context._m;
       context['m'] = {};
    }

    // hacked from https://medium.com/@bvjebin/js-infinite-loops-killing-em-e1c2f5f2db7f
    let transformer = babel => {
      var t = babel.types;
      // transform a loop by adding our callback
      function loopTransform(path) {
        if ("_loop" in context) {
          path
            .get("body")
            .pushContainer(
              "body",
              t.expressionStatement(t.callExpression(t.identifier("_loop"), []))
            );
        }
      }
      // add a call to our function call counter
      function callTransform(path) {
        // Converts:
        // var right_half = lost_array(n- middle, l, r);
        // into:
        // var right_half = _func("lost_array", lost_array(n - middle, l, r));
        let name = path.get("body").container.callee.name;
        if ((name != "_loop") && (name != "_func")) {
           path.replaceWith(
               t.callExpression(t.identifier("_func"),
                                [t.stringLiteral(name),
                                 path.node])
           );
           // Do not recursively call the new stack
           // Avoid "Maximum call stack exceeded"
           path.skip();
           path.stop();  
        }
      }

      return {
        visitor: {
          // keep track of number of function call
          CallExpression: callTransform,
          // prevent endless loops
          WhileStatement: loopTransform,
          DoWhileStatement: loopTransform,
          ForStatement: loopTransform,
          // prevent member access
          MemberExpression(path) {
            // example of disallowing member access
            var name = path.node.object.name;
            var member = path.node.property.name;
            var message = 'Object membership not allowed: ' + name + '.' + member;

            // throw path.buildCodeFrameError("Not allowed");
          },
          // prevent object creation
          ObjectExpression(path) {
            // no objects allowed
            console.error("JJM path", path);
            console.error("JJM path.node", path.node);
            throw path.buildCodeFrameError("Object expression not allowed");
          },
          // prevent calling new
          NewExpression(path) {
            throw path.buildCodeFrameError("New() not allowed");
          },
          // prevent global variables
          Identifier(path) {
            let name = path.node.name;
            if (name in context || path.scope.hasBinding(name)) {
              return;
            }
            throw path.buildCodeFrameError("No globals " + name);
          }
        }
      };
    };

    // transform the user's code
    try {
      var tfunc = Babel.transform(func, { plugins: [transformer] }).code;
    } catch (e) {
      return { ...rubric, error: !e.message ? e : e.message };
    }
    // we should handle the insertion of the return better
    // could the transformer somehow do it?
    // jamming it on at the front is making lots of assumptions about the
    // shape of their code. We could put one at the end returning a specific
    // name, perhaps specified as an argument? Or maybe we use the transformer
    // code to fetch the name of the function defined in the code? Suppose they
    // define more than one? Which one to call?
    if ("_return" in context) {
      tfunc = tfunc + `\nreturn ${context._return}`;
    } else {
      tfunc = "return " + tfunc;
    }
    if ("_aux" in context) {
      tfunc = tfunc + `\n ${context._aux}`;
    }
    try {
      var result = new Function(...Object.keys(context), tfunc)(
        ...Object.values(context)
      );
    } catch (e) {
      return { ...rubric, error: e.message };
    }

    // if the result is a function and we got _args in the context, then
    // call the function
    if (Array.isArray(args) && result instanceof Function) {
      try {
         result = result(...args);

         // Do we need to add the number of function calls to the result?
         if ("_function" in context) {
           // Note, number of times called can be 1-number of times
           // run if the function is the main returned function
           if (!(context["_function"] in functionDict)) {
             functionDict[context["_function"]] = 0;
           } 
           // result is now an array with the value followed by the number of function calls
           // or the value (which was an array) appended with the number of function calls
           if (Array.isArray(result)) {
             result.push(functionDict[context["_function"]]);
           } else {
             result = [ result, functionDict[context["_function"]] ];
           }
         }
      } catch (e) {
         return { ...rubric, error: !e.message ? e:  e.message };
      }
    }

    // For debug, spit out the result in the grader
    if (typeof document == 'undefined') {
        console.error("For seq_no: ", rubric['seq_no'], 
                      typeof test['result'] === 'undefined' ? 'test result:' : "test['result']:", 
                      typeof test['result'] === 'undefined' ? result : test['result']);
    }
    // round if requested
    let toHash = result;
    if (typeof result == "number") {
      if ((context._digits == undefined) && !Number.isInteger(result)) {
         // 64 ** (1/4) is different in lowest digits in Node vs JS
         context._digits = 6
      }
      toHash = Number.parseFloat(result).toFixed(context._digits);
    }
    tests.push({ ...test, result, ...check(test.expectedHash, hash(toHash)) });
  }
  return { ...rubric, tests, ...checkTests(tests) };
}

const workerpool = require("./workerpool");

let wpath =
  typeof window !== "undefined"
    ? "/static/js/sqlWorker.js"
    : "./static/js/sqlWorker.js";

let pool = null;

/** validateSQL validate user sql
 * @param {string} query
 * @param {SQLRubric} rubric
 * @returns {Promise<SQLRubric>}
 */
async function validateSQL(query, rubric) {
  if (!pool) {
    pool = workerpool.pool(wpath, { maxWorkers: 1 });
  }
  const tests = [];
  for (const test of rubric.tests) {
    // prefetch the db so that time isn't counted in the timeout below
    await pool.exec("prefetch", [test.db]);
    try {
      /** @type {import("./sqlWorker.js").evalSQLresult} r */
      const r = await pool
        .exec("evalSQL", [query, test.db, rubric.sort])
        .timeout(rubric.timeout);
      tests.push({
        ...test,
        result: r.result,
        ...check(test.expectedHash, r.hash)
      });
    } catch (e) {
      return { ...rubric, error: e };
    }
  }
  return { ...rubric, tests, ...checkTests(tests) };
}

function validateQuit() {
  if (pool) {
    pool.terminate();
  }
}

exports.validate = validate;
exports.validateQuit = validateQuit;
exports.validateSQL = validateSQL;

async function test() {
  console.log(
    await validate("A+B", {
      kind: "expression",
      tests: [{ context: { A: 3, B: 4 }, expectedHash: "320ca3f6" }]
    })
  );
  console.log(
    await validate("000deadbeef.0", {
      kind: "hex",
      expectedHash: "53fd34f5"
    })
  );
  /*
  console.log(validateExpression("A=A+B", { A: 3, B: 4 }));
  console.log(validateExpression("A=1;B=2;A+B", { A: 3, B: 4 }));
  console.log(validateExpression("A;A+B", { A: 3, B: 4 }));
  console.log(validateExpression("A ? B : A", { A: 3, B: 4 }));
  console.log(validateExpression("A.toString()", { A: 3, B: 4 }));
  console.log(validateExpression("log(1)", {}));
  */
}

/* test(); */
