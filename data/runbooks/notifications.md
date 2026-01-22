# Notifications Runbook

## Overview
Manages omni-channel delivery (email, SMS, push). Depends on the template service and vendor gateways (SendGrid, Twilio).

## Health checks
- `/healthz` returns build info and queue stats.
- Grafana dashboard `notif-overview` tracks throughput and delivery errors.

## Deployment
1. Verify feature flags for campaigns scheduled in the next hour.
2. Deploy canary (10%) and watch `notif-error-rate` for 5 minutes.
3. Roll out to 100% if error delta < 0.5%.

## Troubleshooting tips
- For Twilio 429 errors, throttle SMS workers via `SMS_WORKER_CONCURRENCY` env var.
- Email rendering bugs often stem from stale templates; run `template-sync --pull`.
