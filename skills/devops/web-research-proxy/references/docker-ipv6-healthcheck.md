# Docker Healthcheck: IPv6 vs IPv4 localhost Issue

## Problem

Alpine-based containers use BusyBox `wget`, which resolves `localhost` to IPv6 (`::1`) by default. If the application inside the container only listens on IPv4 (`0.0.0.0`), healthcheck fails with:

```
wget: can't connect to remote host: Connection refused
```

Debugging shows: `Connecting to localhost:3000 ([::1]:3000)` — note the IPv6.

## Affected Combinations

| Container Base | Healthcheck Tool | App Listens On | Result |
|---|---|---|---|
| Alpine (BusyBox) | wget localhost | 0.0.0.0 (IPv4 only) | FAILS |
| Alpine (BusyBox) | wget 127.0.0.1 | 0.0.0.0 (IPv4 only) | OK |
| Alpine (BusyBox) | wget localhost | :: (IPv4+IPv6) | OK |

Common culprits: Next.js (default HOSTNAME=0.0.0.0), many Node.js servers.

## Fix

Change healthcheck URL from `localhost` to `127.0.0.1`:

```yaml
# ❌ Broken — BusyBox resolves localhost to ::1
healthcheck:
  test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]

# ✅ Fixed — explicit IPv4
healthcheck:
  test: ["CMD", "wget", "-qO-", "http://127.0.0.1:3000/api/health"]
```

## Verification

```bash
# Inside the container:
wget -qO- http://127.0.0.1:3000/   # should return HTML
wget -qO- http://localhost:3000/   # may fail with IPv6
```

## After Fixing

`docker restart` does NOT re-read docker-compose.yaml. Must recreate:
```bash
docker compose stop <service>
docker compose rm -f <service>
docker compose create <service>
docker compose start <service>
```
