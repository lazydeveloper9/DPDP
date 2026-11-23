# CS-01 Accuracy Benchmark Suite

Paired True Positive / True Negative fixtures for measuring detection precision, recall, F1 and false positive rate across all DPDP rules.

## Structure

```
fixtures/<RULE_ID>/
  tp_<scenario>/     # Mini-project that SHOULD trigger the rule
  tn_<scenario>/     # Mini-project that should NOT trigger the rule
```

## Running

```bash
python tests/accuracy_bench/evaluate.py
```

Outputs per-rule and aggregate metrics table, saves `baseline_metrics.json`.
