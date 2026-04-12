# Running E2E Tests

## In-Cluster (K8s Job)

```bash
cd cd/
kubectl apply -f jobs/e2e-test-job.yaml
kubectl logs -n graph-olap-platform -l job-name=e2e-tests -f
```

## From Dataproc

```bash
pip install graph-olap-sdk
python -m pytest tests/ -v --tb=short
```

## Notebooks

Run notebooks 02-19 in order. Notebook 00_run_all.ipynb executes all sequentially.
