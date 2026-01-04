# Deployment

Gryag bot is fully containerized using Docker, making the deployment process simple and reliable. This guide covers deployment from development to production.

## Requirements

### Minimum Requirements

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM (4GB recommended)
- 10GB disk space
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- LLM API key (OpenAI or compatible provider)

### Production Requirements

- Docker 24.0+
- Docker Compose 2.20+
- 4GB+ RAM
- 20GB+ disk space (for database and logs)
- PostgreSQL 15+ (if using external database)
- Redis 7+ (if using external Redis)
- SSL/TLS for secure connections (recommended)

## Quick Deployment

### Development Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourserver/gryag-2.0.git
    cd gryag-2.0
    ```

2. **Create environment file:**

    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

3. **Start services:**

    ```bash
    docker compose up -d
    ```

4. **Check logs:**

    ```bash
    docker compose logs -f bot
    ```

5. **Verify bot is running:**

    ```bash
    docker compose ps
    ```

## Service Structure

The Docker Compose setup includes three main services:

### Bot Service

- **Image**: Built from `Dockerfile`
- **Ports**: None (communicates via Telegram API)
- **Volumes**:
  - `./data:/app/data` - Logs and persistent data
  - `./prompts:/app/prompts:ro` - System prompts (read-only)
- **Dependencies**: `postgres`, `redis`
- **Health Check**: Python process check

### PostgreSQL Service

- **Image**: `postgres:18-alpine`
- **Ports**: `5432` (internal only)
- **Volumes**: `./data/postgres:/var/lib/postgresql/data`
- **Environment**: Pre-configured user/password
- **Health Check**: `pg_isready` check

### Redis Service

- **Image**: `redis:alpine`
- **Ports**: `6379` (internal only)
- **Volumes**: Named volume `redis_data`
- **Persistence**: AOF (Append Only File) enabled
- **Health Check**: `redis-cli ping`

## Production Deployment

### Pre-Deployment Checklist

- [ ] Secure `.env` file with strong credentials
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS (if using external services)
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting
- [ ] Review security settings
- [ ] Test in staging environment

### Production Configuration

1. **Secure Environment Variables:**

    ```bash
    # Use strong passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    
    # Store secrets securely (use secrets management)
    # Never commit .env to version control
    ```

2. **Update docker-compose.yml for production:**

    ```yaml
    services:
      bot:
        restart: always
        deploy:
          resources:
            limits:
              cpus: '2'
              memory: 2G
            reservations:
              cpus: '1'
              memory: 1G
    ```

3. **Configure Logging:**

    ```env
    LOG_LEVEL=WARNING
    LOG_FORMAT=json
    LOG_FILE_ENABLED=True
    LOG_FILE_RETENTION_DAYS=30
    ```

4. **Set Access Control:**

    ```env
    ACCESS_MODE=whitelist
    WHITELIST_CHATS=-1001234567890
    RATE_LIMIT_ENABLED=True
    RATE_LIMIT_PROMPTS=20
    ```

### Docker Networking

Services communicate via Docker's internal network:

- **Network**: Default bridge network (or custom network)
- **Service Discovery**: Services accessible by name (`postgres`, `redis`)
- **Port Exposure**: Only expose ports if needed externally

**Example Custom Network:**

```yaml
networks:
  gryag_network:
    driver: bridge

services:
  bot:
    networks:
      - gryag_network
  postgres:
    networks:
      - gryag_network
  redis:
    networks:
      - gryag_network
```

### External Database Setup

To use an external PostgreSQL database:

1. **Update DATABASE_URL:**

    ```env
    DATABASE_URL=postgresql+asyncpg://user:password@host:5432/gryag?ssl=require
    ```

2. **Remove postgres service from docker-compose.yml**

3. **Ensure network connectivity**

### External Redis Setup

To use an external Redis instance:

1. **Update REDIS_URL:**

    ```env
    REDIS_URL=redis://:password@host:6379/0
    ```

2. **Remove redis service from docker-compose.yml**

3. **Ensure network connectivity**

## Database Migrations

The project uses Alembic for database migrations.

### Automatic Migrations

Migrations run automatically on bot startup if the database is empty or missing tables.

### Manual Migration Management

1. **Create a new migration:**

    ```bash
    docker compose exec bot alembic revision --autogenerate -m "description"
    ```

2. **Apply migrations:**

    ```bash
    docker compose exec bot alembic upgrade head
    ```

3. **Rollback migration:**

    ```bash
    docker compose exec bot alembic downgrade -1
    ```

4. **Check current version:**

    ```bash
    docker compose exec bot alembic current
    ```

### Migration Best Practices

- Always test migrations in development first
- Backup database before applying migrations
- Review generated migration files
- Use descriptive migration messages
- Never edit existing migration files

## Backup and Restore

### Database Backup

1. **Full database backup:**

    ```bash
    docker compose exec postgres pg_dump -U bot gryag > backup_$(date +%Y%m%d).sql
    ```

2. **Automated backup script:**

    ```bash
    #!/bin/bash
    BACKUP_DIR="./backups"
    mkdir -p $BACKUP_DIR
    docker compose exec -T postgres pg_dump -U bot gryag | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz
    ```

3. **Schedule backups (cron):**

    ```bash
    # Daily backup at 2 AM
    0 2 * * * /path/to/backup_script.sh
    ```

### Database Restore

1. **Restore from backup:**

    ```bash
    gunzip < backup_20240101.sql.gz | docker compose exec -T postgres psql -U bot gryag
    ```

2. **Restore to new database:**

    ```bash
    docker compose exec postgres createdb -U bot gryag_new
    gunzip < backup.sql.gz | docker compose exec -T postgres psql -U bot gryag_new
    ```

### Redis Backup

Redis data is stored in a Docker volume. To backup:

```bash
docker compose exec redis redis-cli SAVE
docker cp gryag-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

## Monitoring and Health Checks

### Health Checks

All services include health checks:

- **Bot**: Python process check
- **Postgres**: `pg_isready` check
- **Redis**: `redis-cli ping` check

### Monitoring Logs

1. **View all logs:**

    ```bash
    docker compose logs -f
    ```

2. **View specific service:**

    ```bash
    docker compose logs -f bot
    docker compose logs -f postgres
    docker compose logs -f redis
    ```

3. **View last N lines:**

    ```bash
    docker compose logs --tail=100 bot
    ```

4. **Filter logs:**

    ```bash
    docker compose logs bot | grep ERROR
    ```

### Resource Monitoring

1. **Container stats:**

    ```bash
    docker stats
    ```

2. **Disk usage:**

    ```bash
    docker system df
    ```

3. **Volume usage:**

    ```bash
    docker volume ls
    docker volume inspect gryag-2.0_redis_data
    ```

### Application Monitoring

The bot logs important events:

- **Startup/Shutdown**: Logged at INFO level
- **Errors**: Logged at ERROR level
- **LLM API calls**: Logged at DEBUG level
- **Tool executions**: Logged at INFO level

**Log File Location**: `./data/logs/bot_YYYY-MM-DD.log`

## Updating the Bot

### Update Process

1. **Pull latest changes:**

    ```bash
    git pull origin main
    ```

2. **Backup database:**

    ```bash
    # Follow backup procedure above
    ```

3. **Rebuild and restart:**

    ```bash
    docker compose build bot
    docker compose up -d
    ```

4. **Verify:**

    ```bash
    docker compose logs -f bot
    docker compose ps
    ```

### Rolling Updates

For zero-downtime updates:

1. **Deploy new version alongside old:**

    ```bash
    docker compose -f docker-compose.yml -f docker-compose.new.yml up -d
    ```

2. **Gradually migrate traffic**

3. **Remove old version**

### Version Pinning

For production stability, pin versions:

```yaml
services:
  postgres:
    image: postgres:18-alpine
  redis:
    image: redis:7-alpine
```

## Scaling Considerations

### Horizontal Scaling

The bot is designed for single-instance deployment. For scaling:

1. **Database**: Use external managed PostgreSQL
2. **Redis**: Use external managed Redis
3. **Bot Instances**: Run multiple instances with:
   - Shared database
   - Shared Redis
   - Load balancing (if using webhooks)

### Vertical Scaling

Increase resources:

```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

### Performance Tuning

1. **Database Connection Pooling**: Configured in SQLAlchemy
2. **Redis Caching**: Enable for frequently accessed data
3. **Context Limits**: Adjust based on usage
4. **Rate Limiting**: Tune based on user behavior

## Security Best Practices

1. **Secrets Management:**
   - Use Docker secrets or external secret management
   - Never commit `.env` files
   - Rotate credentials regularly

2. **Network Security:**
   - Use internal Docker networks
   - Restrict external access
   - Use firewall rules

3. **Container Security:**
   - Run as non-root user (already configured)
   - Keep images updated
   - Scan images for vulnerabilities

4. **Database Security:**
   - Use strong passwords
   - Enable SSL/TLS
   - Restrict network access
   - Regular backups

5. **Application Security:**
   - Enable access control
   - Configure rate limiting
   - Monitor for abuse
   - Regular security updates

## Troubleshooting Deployment

### Bot Won't Start

1. Check logs: `docker compose logs bot`
2. Verify environment variables
3. Check database connectivity
4. Verify bot token is valid

### Database Connection Issues

1. Verify PostgreSQL is running: `docker compose ps postgres`
2. Check connection string format
3. Verify network connectivity
4. Check firewall rules

### High Memory Usage

1. Monitor with `docker stats`
2. Reduce context limits
3. Enable more frequent summarization
4. Increase container memory limits

### Disk Space Issues

1. Clean old logs: `find ./data/logs -mtime +30 -delete`
2. Clean Docker system: `docker system prune`
3. Rotate log files
4. Archive old database backups

## Related Documentation

- [Configuration Guide](configuration.md) - All configuration options
- [Architecture](architecture.md) - System architecture
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
