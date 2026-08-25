---
id: bqutil-review-performance
title: Performance Review Rubric
description: >
  Review lens for slices that affect latency, throughput, or resource usage.
index:
  - id: performance
    keywords: [performance, latency, throughput, memory, benchmarks]
  - id: evidence
    keywords: [benchmarks, profiling, regressions, proof]
---

# Performance

## Performance

Review whether a change introduces hot-path regressions or disproportionate
resource costs.

## Evidence

Require benchmark or profiling evidence only when the changed behavior makes
performance material.
