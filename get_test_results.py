from csv import reader, writer

from google.cloud import storage

from parse_test_output import get_failed_tests, BUCKET_NAME

example_blob_name = "pr-logs/pull/tektoncd_pipeline/4695/pull-tekton-pipeline-integration-tests/1506021310742925313/artifacts/junit_B3KQbNdl.xml"
test_names = [
    "pull-tekton-pipeline-integration-tests",
    "pull-tekton-pipeline-alpha-integration-tests",
    "pull-tekton-pipeline-unit-tests",
]

reruns = []
with open("rerun_counts.csv", "r", newline="") as f:
    r = reader(f, dialect="excel")
    next(r)  # skip header
    for line in r:
        reruns.append(line)

storage_client = storage.Client()
failures_to_logs = {}  # Map of test name to list of blobs where the test failed
for rerun in reruns:
    test_name = rerun[0]
    if test_name not in test_names:
        continue
    pull_request_id = rerun[1]
    obj = f"pr-logs/pull/tektoncd_pipeline/{pull_request_id}/{test_name}/"
    try:
        invocations = storage_client.list_blobs(BUCKET_NAME, prefix=obj)
        for blob in invocations:
            filename = blob.name.split("/")[-1]
            if not (filename.startswith("junit") and filename.endswith("xml")):
                continue
            failures = get_failed_tests(storage_client, blob.name)
            url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}"
            for testname in failures:
                if testname in failures_to_logs:
                    failures_to_logs[testname].append(url)
                else:
                    failures_to_logs[testname] = [url]
    except Exception as e:
        print("exception: %s", e)  # Probably rate limited
        break

with open("test_failures.csv", "w", newline="") as f:
    w = writer(f, dialect="excel")
    w.writerow(["Test Name", "Number of Failures", "Log Links"])
    for testname, urls in failures_to_logs.items():
        row = [testname]
        row.append(len(urls))
        row.extend(urls)
        w.writerow(row)
