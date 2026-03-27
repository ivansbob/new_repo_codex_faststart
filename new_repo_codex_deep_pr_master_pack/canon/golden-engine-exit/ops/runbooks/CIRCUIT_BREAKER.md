# Per-arm circuit breaker

Rule (example):
- if fail_rate > threshold OR p90_latency > baseline*mult → cooldown_sec.

Log:
- record cooldown decisions in must-log fields (arm_state snapshot).
