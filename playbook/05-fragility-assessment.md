# Loka Antifragile TPM Playbook – Fragility Assessment

**Principle:** Don’t try to predict risks. Measure fragility vectors and eliminate ruin exposure.

## Practices
- Identify fragility vectors: areas where small shocks cause outsized damage.
- Classify each as **local** (bounded downside, recoverable) or **systemic** (ruin exposure).
- Eliminate ruin exposures first (e.g., unvalidated data, single-region cloud dependency).
- Use stress scenarios to map breakpoints (“what happens if API fails for 48h?”).
- Prefer designs that look inefficient in normal times but survive stress (redundancy, buffers).

## Loka Example
**Vector**: single-region cloud deployment for a healthcare AI platform.
**Systemic fragility**: ruin exposure if region outage coincides with trial deadlines.
**Antifragile action**: **multi-region deployment before optimization.**
