from defusedxml.ElementTree import fromstring  # secure XML parser

BUCKET_NAME = "tekton-prow"

def download(client, blob_name):
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    return blob.download_as_string()

def get_failed_tests_from_tree(xml_tree):
    failed_tests = []
    for testsuite in xml_tree:
        for testcase in testsuite:
            failures = [child for child in testcase if child.tag == "failure" and bool(child.text)]
            if len(failures) > 0:
                failed_tests.append(testcase.attrib.get("name"))
    return failed_tests

def get_failed_tests(client, blob_name):
    xmlfilecontents = download(client, blob_name)
    tree = fromstring(xmlfilecontents)
    return get_failed_tests_from_tree(tree)

def get_test_runtimes(xml_tree):
    testcase_runtimes = {testcase.attrib.get("name"): testcase.attrib.get("time") for testcase in xml_tree.iter("testcase")}
    testsuite_runtimes = {testsuite.attrib.get("name"): testsuite.attrib.get("time") for testsuite in xml_tree}
    return testcase_runtimes, testsuite_runtimes
