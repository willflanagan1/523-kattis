"""edit Rubrics before embedding in the page"""

import json

def exclude(d, *keys):
    """copy a dictionary excluding the given keys"""
    return {k: d[k] for k in d if k not in keys}


def editRubrics(Rubrics):
    """Remove solutions and such before putting rubrics in student's browser"""
    result = {}
    for tag, rubric in Rubrics.items():
        rubric = exclude(rubric, "solution", "result", "correct")
        if "tests" in rubric:
            rubric["tests"] = [
                exclude(test, "result", "correct") for test in rubric["tests"]
            ]
        result[tag] = rubric
    return json.dumps(result, indent=2)
