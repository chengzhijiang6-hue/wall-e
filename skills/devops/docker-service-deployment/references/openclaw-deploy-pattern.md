# OpenClaw Deployment Pattern Reference

## Why It Works When Others Fail

OpenClaw succeeds where other services fail because it follows correct deployment conventions:

### 1. Port Binding Configuration
```bash
docker inspect openclaw --format='{{json .NetworkSettings.Ports}}'
# Output shows: map[80/tcp:[{HostIp:0.0.0.0 HostPort:"80"}]]
# ✓ Binds to ALL interfaces (0.0.0.0) not just localhost
```

### 2. Network Accessibility Path
| Layer | Setting | Result |
|-------|---------|--------|
| Container port | 80 | Standard HTTP |
| Host mapping | 0.0.0.0:80→8080 | All network interfaces exposed |
| Docker bridge | Default NAT | Windows host sees via gateway IP |
| Firewall | Allow-listed | System-level service exception |

### 3. Comparison Table

| Attribute | OpenClaw (Success) | Typical Failure Mode |
|-----------|-------------------|---------------------|
| Interface binding | `0.0.0.0` | `localhost` or omitted |
| Port choice | System standard (80) | Custom conflicts with existing |
| Network mode | Bridge with explicit mapping | `--network host` without verification |
| Verification | Self-test before report | Assumed success |

### 4. Replication Template
For any new dashboard/service:

```bash
docker run -d \
  --name <service-name> \
  -p 0.0.0.0:<high-port>:<container-port> \
  --network host \
  -v <data-dir>:/app/data \
  <image-ref>

# Immediate verification checklist:
$ docker ps --filter name=<service-name>
$ netstat -tuln | grep <high-port>
$ curl http://localhost:<high-port>/health
$ curl http://$(ip route show default | awk '{print $3}'):<high-port>/health
```

### Key Lesson
**Successful deployment = Correct configuration + Immediate self-verification**