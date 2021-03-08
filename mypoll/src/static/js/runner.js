const { validate, validateQuit } = require("./validate.js");

var input = "";

process.stdin.resume();
process.stdin.setEncoding("utf8");

process.stdin.on("data", function (chunk) {
  input += chunk;
});

process.stdin.on("end", async function () {
  var { answers, rubrics } = JSON.parse(input);
  let outputs = {};
  for (const tag of Object.keys(rubrics)) {
    try {
      outputs[tag] = await validate(answers[tag], rubrics[tag]);
    } catch (e) {
      console.error("error", tag, answers[tag], e.message);
    }
  }
  var outputJSON = JSON.stringify(outputs, null, "    ");
  process.stdout.write(outputJSON);
  validateQuit();
});
