# Payment Service Runbook

## Overview
The payment service handles credit/debit transactions, refunds, and invoicing. It depends on
- Auth service for customer tokens
- Ledger service for double-entry posting

## Alerts
- `payment-high-latency`: Check database connections and Redis queue depth.
- `payment-charge-failures`: Inspect integration logs with PSP vendors.

## Restart procedure
1. Drain traffic via service mesh (`traffic shift payment 0`).
2. Scale deployment to zero replicas.
3. Apply new config, scale back to desired replica count (4 in prod).
4. Re-enable traffic and run synthetic charge.

## Common incidents
- **PSP timeouts**: switch PSP routing to backup vendor by toggling feature flag `psp.failover=backup`.
- **Ledger mismatch**: pause ingestion, notify finance bridge, and run `./scripts/replay-ledger.sh --from <ts>`.
