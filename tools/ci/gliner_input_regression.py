import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path.cwd()
out = root / "gliner-input-results"
out.mkdir(exist_ok=True)
adapter = root / "packages/sie_server/src/sie_server/adapters/gliner2/adapter.py"
fixed = adapter.read_bytes()
baseline = "d3fa3c16aa8150747da1fa3b2cd0624ba48a3ebd"
selectors = [
    "packages/sie_server/tests/adapters/test_gliner2_input_errors.py",
    "packages/sie_server/tests/test_queue_executor.py::TestProcessExtractBatch::test_gliner2_invalid_request_does_not_fail_valid_sibling",
]

def run(label):
    proc = subprocess.run([
        sys.executable, "-m", "pytest", "-q", *selectors,
        "--junitxml=" + str(out / (label + ".xml")),
    ], text=True, capture_output=True)
    (out / (label + ".log")).write_text(proc.stdout + proc.stderr)
    print(proc.stdout[-6000:] + proc.stderr[-1500:])
    suites = ET.parse(out / (label + ".xml")).getroot()
    counts = {key: sum(int(s.get(key, "0")) for s in suites.findall("testsuite")) for key in ["tests", "failures", "errors", "skipped"]}
    counts["exit_code"] = proc.returncode
    return counts

try:
    adapter.write_bytes(subprocess.check_output(["git", "show", baseline + ":" + str(adapter.relative_to(root))]))
    before = run("original")
finally:
    adapter.write_bytes(fixed)
after = run("fixed")
(out / "summary.json").write_text(json.dumps({"before": before, "after": after}, indent=2))
print("REGRESSION", json.dumps({"before": before, "after": after}))
assert before["errors"] == 0 and before["failures"] == 20, before
assert before["tests"] == 21 and before["skipped"] == 0, before
assert after["exit_code"] == 0 and after["tests"] == 21 and after["skipped"] == 0, after
