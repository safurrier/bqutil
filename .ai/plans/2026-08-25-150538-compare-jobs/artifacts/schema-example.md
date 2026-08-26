# Compare JSON example

```json
{
  "semantics": "candidate_minus_baseline",
  "baseline": {"job_id": "before", "cache_hit": false, "query_plan": []},
  "candidate": {"job_id": "after", "cache_hit": true, "query_plan": []},
  "metrics": {
    "bytes_processed": {
      "baseline": 100,
      "candidate": 80,
      "absolute_delta": -20,
      "percent_change": -20.0
    }
  }
}
```
