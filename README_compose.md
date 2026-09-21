# Langfuse Observability Stack (OBS)

A complete Docker Compose setup for running **Langfuse** - an open-source LLM observability platform with integrated analytics, storage, and monitoring tools.

## 📋 Services

| Service | Port | Access URL / Connection | Purpose |
|---------|------|-------------------------|---------|
| **PostgreSQL** | 5432 | `localhost:5432` | Primary relational database |
| **pgAdmin** | 5050 | [http://localhost:5050](http://localhost:5050) | PostgreSQL management UI |
| **Langfuse Web** | 3000 | [http://localhost:3000](http://localhost:3000) | Main web UI for LLM observability |
| **Langfuse Worker** | N/A | N/A (Background process) | Background job processing |
| **Valkey** | 6379 | `localhost:6379` | Caching and real-time data |
| **Valkey Admin** | 8081 | [http://localhost:8081](http://localhost:8081) | Valkey management UI |
| **RedisInsight (optional)** | 5540 | [http://localhost:5540](http://localhost:5540) | Alternative Valkey management UI |
| **Jaeger** | 16686, 4317, 4318 | [http://localhost:16686](http://localhost:16686) | Distributed tracing UI and OTLP collector |
| **OpenSearch** | 9200, 9600 | `localhost:9200` | Search and analytics engine |
| **OpenSearch Dashboards** | 5601 | [http://localhost:5601](http://localhost:5601) | OpenSearch web UI |
| **ClickHouse** | 8123, 9000 | `localhost:8123` (HTTP) / `9000` (Native) | Analytics database |
| **Tabix** | 8080 | [http://localhost:8080](http://localhost:8080) | ClickHouse web UI |
| **MinIO** | 9002, 9001 | [http://localhost:9001](http://localhost:9001) (Console) / `:9002` (API) | S3-compatible object storage |

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB of available disk space for volumes

### Starting the Stack

```bash
docker-compose up -d
```

### Accessing Services

- **Langfuse UI**: http://localhost:3000
- **pgAdmin**: http://localhost:5050 (admin@example.com / admin)
- **Valkey Admin**: http://localhost:8081
- **RedisInsight (optional)**: http://localhost:5540
- **Jaeger UI**: http://localhost:16686
- **OpenSearch API**: http://localhost:9200
- **OpenSearch Dashboards**: http://localhost:5601
- **ClickHouse Tabix**: http://localhost:8080
- **MinIO Console**: http://localhost:9001

## ⚙️ Configuration

### Required Environment Variables

Before deploying, update the following secrets in `compose.yaml`:

```yaml
NEXTAUTH_SECRET: replace-with-random-secret
SALT: replace-with-random-salt
```

Generate secure secrets:
```bash
openssl rand -base64 32
```

### Database Setup

PostgreSQL runs as a containerized service with the following default credentials:
- **Host**: `postgres` (from within Docker) or `localhost:5432` (from host)
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `langfuse_practice`

The database connection is automatically configured in the compose file:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/langfuse_practice
DIRECT_URL=postgresql://postgres:postgres@postgres:5432/langfuse_practice
```

To modify credentials, update the environment variables in the `postgres` service section of `compose.yaml` before starting the stack.

**Managing PostgreSQL with pgAdmin**:
1. Open http://localhost:5050
2. Login with `admin@example.com` / `admin`
3. Add a new server connection to the PostgreSQL database
4. Use `postgres` as hostname, `postgres` as username and password

### MinIO Credentials

Default credentials (change in production):
- **Username**: `minioadmin`
- **Password**: `minioadmin`

## 📊 Architecture

```
┌─────────────────────────────────────┐
│  PostgreSQL (Port 5432)             │
│  └─ pgAdmin (Port 5050)             │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  Langfuse Web (Port 3000)           │
│  + Langfuse Worker (Background)     │
┌─────────────────────────────────────┐
│  Jaeger UI (Port 16686)             │
│  ├─ OTLP (Ports 4317, 4318)         │
│  OpenSearch (Ports 9200, 9600)      │
└─────────────────────────────────────┘
├─────────────────────────────────────┤
│  Valkey (Port 6379)                 │
│  ├─ Valkey Admin (Port 8081)         │
│  ├─ RedisInsight (Optional, Port 5540)│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  ClickHouse (Port 8123, 9000)       │
│  └─ Tabix UI (Port 8080)            │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  MinIO Storage (Port 9002, 9001)    │
└─────────────────────────────────────┘
```

## 🔧 Useful Commands

### Managing the Full Stack

**Start the entire stack**:
```bash
docker-compose up -d
```

**Stop the stack** (keeps data):
```bash
docker-compose down
```

**Remove data volumes** (complete reset):
```bash
docker-compose down -v
```

### Managing Individual Services

**Start a specific service**:
```bash
docker-compose up -d [service-name]
```

**Stop a specific service**:
```bash
docker-compose stop [service-name]
```

**Stop and remove a specific service**:
```bash
docker-compose down [service-name]
```

**Restart a specific service**:
```bash
docker-compose restart [service-name]
```

**View logs for a service**:
```bash
docker-compose logs -f [service-name]
```

**Example**: Start just Valkey and Valkey Admin:
```bash
docker-compose up -d valkey valkey-admin
```

**Optional**: Run RedisInsight instead of Valkey Admin:
```bash
docker run -d --name redisinsight -p 5540:5540 \
	-e REDIS_HOSTS=local:host.docker.internal:6379 \
	--add-host=host.docker.internal:host-gateway \
	redis/redisinsight:latest
```

**Example**: Start Jaeger and OpenSearch:
```bash
docker-compose up -d jaeger opensearch opensearch-dashboards
```

**Available service names**:
- `postgres`
- `pgadmin`
- `langfuse-web`
- `langfuse-worker`
- `valkey`
- `valkey-admin`
- `redisinsight` (optional, standalone container)
- `jaeger`
- `opensearch`
- `opensearch-dashboards`
- `clickhouse`
- `tabix`
- `minio`

### Container and Image Management

**How Docker Compose reuses resources:**
- `docker-compose up` reuses existing containers and images (no unnecessary copies)
- `docker-compose down` stops and removes containers but keeps images on disk for quick restart
- Only recreates containers if the compose file configuration has changed
- Stopped containers take minimal disk space (not RAM)

**Clean up and free disk space:**

**Remove containers, images, and volumes** (complete cleanup):
```bash
docker compose down -v --rmi all
```

**Remove only unused images**:
```bash
docker image prune -a
```

**Remove only unused volumes**:
```bash
docker volume prune
```

**View disk usage by Docker**:
```bash
docker system df
```

**Remove all unused Docker data** (containers, images, volumes, networks):
```bash
docker system prune -a --volumes
```

## 📝 Notes

- All services are configured with `restart: unless-stopped` for automatic recovery
- Data is persisted in Docker volumes: `postgres_data`, `pgadmin_data`, `valkey_data`, `opensearch_data`, `clickhouse_data`, `clickhouse_logs`, `minio_data`
- Telemetry is disabled (`TELEMETRY_ENABLED: "false"`)
- **Valkey** (a high-performance in-memory data store) replaces Redis for caching and real-time data
- **Jaeger** accepts OTLP traces over gRPC on port `4317` and HTTP on port `4318`
- **OpenSearch** runs as a single-node local development service with its security plugin disabled
- Local PostgreSQL service must be stopped/uninstalled to avoid port conflicts (port 5432)

## 🔐 Security Considerations

- **PostgreSQL**: Change default credentials (`postgres:postgres`) in production
- **pgAdmin**: Change default credentials (`admin@example.com:admin`) in production
- **MinIO**: Change default credentials (`minioadmin:minioadmin`) in production
- **OpenSearch**: Enable and configure security before exposing it outside local development
- Replace `NEXTAUTH_SECRET` and `SALT` with secure random values
- Restrict access to exposed ports (use firewall rules in production)
- Use strong, unique credentials for all services
- Consider using environment variables or secrets management for sensitive data
- Don't expose port 5432 to untrusted networks in production

## 📚 Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [ClickHouse Docs](https://clickhouse.com/docs)
- [MinIO Docs](https://docs.min.io/)
- [Valkey Docs](https://valkey.io/docs)
- [Valkey Admin](https://valkey-admin.valkey.io/)
- [RedisInsight Docs](https://docs.redis.com/latest/ri/)
- [Jaeger Docs](https://www.jaegertracing.io/docs/)
- [OpenSearch Docs](https://opensearch.org/docs/latest/)
