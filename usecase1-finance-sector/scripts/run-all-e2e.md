# Run All E2E Tests

Paste into a single Jupyter cell. Runs all test notebooks sequentially via papermill, reports pass/fail for each.

## Configuration

Update the environment variables and notebook directory before running.

## Script

```python
import os, time, subprocess, json

# === CONFIGURATION — UPDATE THESE ===
os.environ['GRAPH_OLAP_API_URL'] = 'https://<your-control-plane-url>'
os.environ['GRAPH_OLAP_IN_CLUSTER_MODE'] = 'true'
os.environ['GRAPH_OLAP_USE_CASE_ID'] = '<your-use-case-id>'
os.environ['GRAPH_OLAP_VERIFY_SSL'] = 'false'
os.environ['GRAPH_OLAP_SKIP_HEALTH_CHECK'] = 'true'
os.environ['https_proxy'] = 'http://<proxy-host>:<port>'
os.environ['http_proxy'] = 'http://<proxy-host>:<port>'

# Install papermill (proxy off for pip)
clean_env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
subprocess.run(["pip", "install", "--no-cache-dir", "papermill", "-q"], capture_output=True, env=clean_env)

import papermill as pm

NOTEBOOK_DIR = "/home/jupyter/notebooks"  # Adjust to your notebook directory
RESULTS = []

NOTEBOOKS = [
    "02_health_checks.ipynb",
    "03_managing_resources.ipynb",
    "04_cypher_basics.ipynb",
    "05_exploring_schemas.ipynb",
    "06_graph_algorithms.ipynb",
    "07_end_to_end_workflows.ipynb",
    "08_quick_start.ipynb",
    "09_handling_errors.ipynb",
    "10_bookmarks.ipynb",
    "11_instance_lifecycle.ipynb",
    "13_advanced_mappings.ipynb",
    "14_version_diffing.ipynb",
    "15_background_jobs.ipynb",
    "16_falkordb.ipynb",
    "17_authorization.ipynb",
    "18_admin_operations.ipynb",
    "19_ops_configuration.ipynb",
]

print("=" * 60)
print("E2E TEST SUITE - Starting")
print("=" * 60)
print(f"Notebooks: {len(NOTEBOOKS)}")
print(f"API URL: {os.environ['GRAPH_OLAP_API_URL']}")
print(f"Use Case: {os.environ['GRAPH_OLAP_USE_CASE_ID']}")
print()

start_all = time.time()

for nb in NOTEBOOKS:
    nb_path = f"{NOTEBOOK_DIR}/{nb}"
    out_path = f"{NOTEBOOK_DIR}/output_{nb}"
    print(f"Running: {nb} ...", end=" ", flush=True)
    start = time.time()
    try:
        pm.execute_notebook(
            nb_path,
            out_path,
            kernel_name="python3",
            parameters={
                "WRAPPER_TYPE": "falkordb",
            },
            progress_bar=False,
        )
        elapsed = int(time.time() - start)
        RESULTS.append({"notebook": nb, "status": "PASS", "time": f"{elapsed}s", "error": ""})
        print(f"PASS ({elapsed}s)")
    except pm.PapermillExecutionError as e:
        elapsed = int(time.time() - start)
        error_msg = str(e)[:200]
        RESULTS.append({"notebook": nb, "status": "FAIL", "time": f"{elapsed}s", "error": error_msg})
        print(f"FAIL ({elapsed}s)")
        print(f"  Error: {error_msg}")
    except Exception as e:
        elapsed = int(time.time() - start)
        error_msg = str(e)[:200]
        RESULTS.append({"notebook": nb, "status": "ERROR", "time": f"{elapsed}s", "error": error_msg})
        print(f"ERROR ({elapsed}s)")
        print(f"  Error: {error_msg}")

total_time = int(time.time() - start_all)

# === SUMMARY ===
print()
print("=" * 60)
print("E2E TEST SUITE - Summary")
print("=" * 60)

passed = sum(1 for r in RESULTS if r["status"] == "PASS")
failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
errors = sum(1 for r in RESULTS if r["status"] == "ERROR")

for r in RESULTS:
    status_icon = "+" if r["status"] == "PASS" else "x" if r["status"] == "FAIL" else "!"
    print(f"  {status_icon} {r['notebook']:40s} {r['status']:5s} {r['time']:>6s}")
    if r["error"]:
        print(f"    -> {r['error'][:100]}")

print()
print(f"Total: {len(RESULTS)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
print(f"Time: {total_time}s")
print()

if failed + errors == 0:
    print("ALL TESTS PASSED")
else:
    print(f"FAILURES: {failed + errors} test(s) need attention")
    print("Check output_*.ipynb files for detailed error traces")
```
