# WSL2 Docker Networking Patterns

## Cross-Platform Access Guide

### Problem Statement
WSL2 containers are isolated from Windows host by NAT. Direct `localhost` access from Windows does not work unless explicitly configured.

---

## Solution Paths

### Path 1: Use WSL2 Gateway IP (Recommended)

#### Step 1: Find Gateway IP
```bash
$ ip route show default | awk '{print $3}'
# Output: 172.20.103.1 (varies per WSL instance)
```

#### Step 2: Access from Windows
Open browser or curl:
```
http://<gateway-ip>:<port>/<endpoint>
```

Example:
```bash
# From Windows CMD:
curl http://172.20.103.1:59000/monitor

# From Windows PowerShell:
Invoke-RestMethod -Uri "http://172.20.103.1:59000/health"
```

#### Why This Works
WSL2 implements a virtualized network where:
- WSL guest has IP like `172.20.103.2`
- Host (Windows) uses gateway at `172.20.103.1`
- All container ports exposed on `0.0.0.0` are forwarded through NAT to this gateway

---

### Path 2: --network host Mode (Simpler, Less Isolated)

```bash
docker run -d \
  --name <service-name> \
  --network host \  # Uses host's network namespace directly
  -p <port>:<container-port> \  # Still needed for port binding
  <image-ref>
```

**Pros**: 
- No NAT routing layer
- localhost works directly in both Windows and WSL
- Fewer troubleshooting variables

**Cons**:
- Port conflicts more likely
- Less isolation between services

---

### Path 3: Explicit Interface Binding

```bash
docker run -d \
  --name <service-name> \
  -p 0.0.0.0:<host-port>:<container-port> \  # Force all interfaces
  <image-ref>
```

Then verify:
```bash
$ netstat -tuln | grep <host-port>
tcp   LISTEN 0 128 0.0.0.0:<port> 0.0.0.0:*
```

If shows `127.0.0.1` instead of `0.0.0.0`, container is only listening locally → fails from Windows host.

---

## Troubleshooting Decision Tree

```
User can't access service from Windows host
├─ Can you access via localhost in WSL terminal?
│  ├─ YES → Container running fine, fix Windows access path
│  │          Check firewall + use gateway IP method
│  └─ NO → Container itself has issue
│           Run: docker logs <name>, docker ps
│
├─ Is port mapped correctly?
│  ├─ `docker port <name>` shows HostIp: 0.0.0.0
│  │    ✓ Good
│  │ ❌ `docker port <name>` shows HostIp: 127.0.0.1
│  │    → Redeploy with explicit `-p 0.0.0.0`
│
├─ Is Windows Firewall blocking?
│  ├─ Open Windows Defender Firewall → Advanced Settings
│  │  → Inbound Rules → New Rule → Port → TCP 59000 → Allow
│  └─ Temporarily disable firewall to test (not for production)
│
└─ Did user change WSL instance IP?
   ├─ Gateway IP changes across reboot sometimes
   │  → Re-run: ip route show default | grep default
   └─ Document new IP in configuration
```

---

## Reference Commands

### Get current WSL2 IP (from Windows)
```powershell
# PowerShell
netsh interface ipv4 show addresses wsl

# Or ask WSL:
wsl ip route show default | grep src
```

### Get gateway IP (from WSL)
```bash
ip route show default | awk '{print $3}'
```

### Check port is actually listening
```bash
ss -tuln | grep <port>
# Expected output:
# tcp  LISTEN 0 128 0.0.0.0:<port> 0.0.0.0:*
```

### Test accessibility from within WSL
```bash
curl -v http://localhost:<port>/health
curl -v http://$(ip route show default | awk '{print $3}'):<port>/health
```

### Test from Windows CMD (after fixing issues)
```cmd
curl http://<gateway-ip>:<port>/health
```

---

## Common Error Messages

| Error | Root Cause | Fix |
|-------|------------|-----|
| "localhost refused to connect" | Wrong URL, wrong port, or blocked | Verify `docker port`, try gateway IP |
| "Connection timeout" | Firewall blocking or no listener | Add inbound rule, check `ss -tuln` |
| "Address already in use" | Another service on same port | `fuser -k <port>/tcp` or use different port |
| "Can't connect to localhost" | Container crashed on launch | `docker logs <name> --tail 100` |

---

## Best Practices Summary

1. **Always verify before reporting** — run internal curl/test first
2. **Use high-numbered ports** (>50000) to avoid system conflicts  
3. **Prefer `--network host`** for dashboard services when possible
4. **Document gateway IP** after major system changes
5. **Never say "please test it yourself"** — agent must self-verify