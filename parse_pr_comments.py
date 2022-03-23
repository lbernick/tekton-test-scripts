from collections import defaultdict

"""
Returns a possibly-empty list of test targets rerun by the comment.
If "/retest" was used without a target specified, list includes "All tests rerun".
"""
def rerun_targets(comment):
    targets = []
    lines = comment.body.split("\n")
    for line in lines:
        if line.startswith("/test") or line.startswith("/retest"):
            words = line.split(" ")
            if len(words) > 1:
                targets.append(words[1].rstrip("\r\n"))
            else:
                targets.append("All tests rerun")
    return targets

"""
Returns a possibly-empty map of test name -> invocation,
based on failure comments from the Tekton robot.
"""
def failed_tests(comment):
    failed = defaultdict(str)
    if comment.user.login != "tekton-robot":
        return failed
    if not "The following test **failed**" in comment.body:
        return failed
    lines = comment.body.split("\n")
    failures = lines[4:-8]
    for failure in failures:
        words = failure.split(" ")
        target = words[0]
        invocation = words[4].split("/")[-2]
        failed[target] = (invocation)
    return failed

"""
Returns a mapping of test name -> (flake count, failed invocations).
Flake count = min(number of reruns, number of failures).

Flake count for a test might not be the same as the number of failed invocations.
Use flake count for metrics, but link a failed test to all of its failed invocations for debugging.

TODO: This actually doesn't work at all since the robot cleans up past test failure comments
"""
def get_flaky_invocations(pull):
    reruns = defaultdict(int)
    failed_invocations = defaultdict(list)
    for comment in pull.get_issue_comments():
        targets = rerun_targets(comment)
        for target in targets:
            reruns[target] += 1
        failures = failed_tests(comment)
        for testname, invocation in failures.items():
            failed_invocations[testname].append(invocation)
    out = {}
    for testname in reruns:
        flake_count = min(reruns[testname], len(failed_invocations[testname]))
        if flake_count == 0:
            continue
        out[testname] = (flake_count, failed_invocations[testname])
    return out

"""
Returns a map of test names to a list of failed invocations
"""
def get_all_failures(pull):
    failed_invocations = defaultdict(list)
    for comment in pull.get_issue_comments():
        failures = failed_tests(comment)
        for testname, invocation in failures.items():
            failed_invocations[testname].append(invocation)
    return failed_invocations

"""
Returns a map of test names to number of reruns
"""
def get_all_reruns(pull):
    reruns = defaultdict(int)
    for comment in pull.get_issue_comments():
        targets = rerun_targets(comment)
        for target in targets:
            reruns[target] += 1
    return reruns
