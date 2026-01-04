# Troubleshooting

This guide covers common issues, their symptoms, and solutions for Gryag 2.0.

## Common Issues

### Bot Won't Start

**Symptoms:**
- Bot container exits immediately
- Error messages in logs
- "Failed to start" errors

**Solutions:**

1. **Check Bot Token:**
   ```bash
   # Verify token is set
   echo $TELEGRAM_BOT_TOKEN
   
   # Test token validity
   curl https://api.telegram.org/bot<TOKEN>/getMe
   ```

2. **Check LLM API Key:**
   ```bash
   # Verify key is set
   echo $LLM_API_KEY
   ```

3. **Check Database Connection:**
   ```bash
   # Verify PostgreSQL is running
   docker compose ps postgres
   
   # Test connection
   docker compose exec postgres psql -U bot -d gryag -c "SELECT 1;"
   ```

4. **Check Logs:**
   ```bash
   docker compose logs bot
   # Or
   tail -f data/logs/bot_$(date +%Y-%m-%d).log
   ```

5. **Verify Environment Variables:**
   ```bash
   # Check .env file exists
   ls -la .env
   
   # Verify required variables
   grep -E "TELEGRAM_BOT_TOKEN|LLM_API_KEY" .env
   ```

### Database Connection Errors

**Symptoms:**
- `Failed to initialize database`
- `Connection refused` errors
- `Authentication failed` errors

**Solutions:**

1. **Check PostgreSQL is Running:**
   ```bash
   docker compose ps postgres
   # Should show "Up"
   ```

2. **Verify Connection String:**
   ```env
   DATABASE_URL=postgresql+asyncpg://bot:bot@postgres:5432/gryag
   ```
   - Format: `postgresql+asyncpg://user:password@host:port/database`
   - Must use `asyncpg` driver

3. **Check Database Exists:**
   ```bash
   docker compose exec postgres psql -U bot -l | grep gryag
   ```

4. **Test Connection:**
   ```bash
   docker compose exec postgres psql -U bot -d gryag -c "SELECT version();"
   ```

5. **Check Network:**
   ```bash
   # Verify bot can reach postgres
   docker compose exec bot ping postgres
   ```

6. **Reset Database (if needed):**
   ```bash
   # WARNING: This deletes all data
   docker compose down -v
   docker compose up -d postgres
   # Wait for postgres to be ready
   docker compose up -d bot
   ```

### LLM API Errors

**Symptoms:**
- `LLM error` messages
- `model_unavailable` errors
- `llm_rate_limit` errors
- `llm_timeout` errors

**Solutions:**

1. **Verify API Key:**
   ```bash
   # Check key is set
   echo $LLM_API_KEY
   
   # Test API key (OpenAI example)
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $LLM_API_KEY"
   ```

2. **Check Base URL:**
   ```env
   LLM_BASE_URL=https://api.openai.com/v1
   # Or your custom endpoint
   ```

3. **Verify Model Name:**
   ```env
   LLM_MODEL=gpt-4o
   # Ensure model exists and is accessible
   ```

4. **Check Rate Limits:**
   - Review API provider's rate limits
   - Increase `LLM_MAX_RETRIES` if needed
   - Add delays between requests

5. **Enable Fallback Model:**
   ```env
   LLM_FALLBACK_MODEL=gpt-4o-mini
   ```

6. **Increase Timeout:**
   ```env
   LLM_TIMEOUT_SECONDS=120  # Default: 60
   ```

7. **Check Network:**
   ```bash
   # Test connectivity
   curl https://api.openai.com/v1/models
   ```

### Bot Not Responding

**Symptoms:**
- Bot receives messages but doesn't reply
- No errors in logs
- Bot appears to be running

**Solutions:**

1. **Check Access Control:**
   ```env
   # Verify access mode
   ACCESS_MODE=global  # or private, whitelist
   
   # Check if chat/user is blocked
   # Review blacklist and restrictions
   ```

2. **Check Rate Limiting:**
   ```env
   # Temporarily disable for testing
   RATE_LIMIT_ENABLED=False
   ```

3. **Check Trigger Keywords (Groups):**
   ```env
   # Verify keywords are set
   BOT_TRIGGER_KEYWORDS=gryag,грягі,griag
   
   # Ensure message contains keyword
   ```

4. **Check Logs:**
   ```bash
   # Look for errors
   docker compose logs bot | grep -i error
   
   # Check if messages are received
   docker compose logs bot | grep "message"
   ```

5. **Verify Bot is Added to Group:**
   - Bot must be member of group
   - Bot must have permission to read messages

6. **Check LLM Response:**
   - Verify LLM is returning responses
   - Check for moderation blocks
   - Review LLM error messages

### Context Too Large Errors

**Symptoms:**
- `context_max_tokens` exceeded
- Bot responses are slow
- High token usage

**Solutions:**

1. **Reduce Immediate Context:**
   ```env
   IMMEDIATE_CONTEXT_MESSAGES=50  # Default: 100
   ```

2. **Reduce Context Limit:**
   ```env
   CONTEXT_MAX_TOKENS=4000  # Default: 8000
   ```

3. **Reduce Summary Tokens:**
   ```env
   RECENT_SUMMARY_TOKENS=512   # Default: 1024
   LONG_SUMMARY_TOKENS=2048    # Default: 4096
   ```

4. **Enable More Frequent Summarization:**
   ```env
   RECENT_SUMMARY_INTERVAL_DAYS=1  # Default: 3
   ```

5. **Reduce Memory Facts:**
   ```env
   USER_MEMORY_MAX_FACTS=25  # Default: 50
   ```

### Rate Limiting Too Strict

**Symptoms:**
- Users getting rate limit errors frequently
- Legitimate users blocked

**Solutions:**

1. **Increase Rate Limit:**
   ```env
   RATE_LIMIT_PROMPTS=50  # Default: 30
   ```

2. **Increase Time Window:**
   ```env
   RATE_LIMIT_WINDOW_HOURS=2  # Default: 1
   ```

3. **Disable Temporarily (Testing):**
   ```env
   RATE_LIMIT_ENABLED=False
   ```

4. **Add Users to Admin:**
   - Admins bypass rate limiting
   - Add trusted users to `ADMIN_IDS`

### Vision Not Working

**Symptoms:**
- Bot doesn't process images
- Vision errors in logs

**Solutions:**

1. **Enable Vision:**
   ```env
   LLM_VISION_ENABLED=True
   ```

2. **Check Vision Model:**
   ```env
   LLM_VISION_MODEL=gpt-4o  # Or vision-capable model
   ```

3. **Verify Model Supports Vision:**
   - Not all models support vision
   - Use GPT-4 Vision, Claude 3, or compatible model

4. **Check Image URL:**
   - Bot constructs Telegram file URLs
   - Verify bot can access Telegram API
   - Check network connectivity

### Database Performance Issues

**Symptoms:**
- Slow responses
- High database CPU usage
- Timeout errors

**Solutions:**

1. **Check Indexes:**
   ```sql
   -- Verify indexes exist
   \d messages
   \d summaries
   ```

2. **Optimize Queries:**
   - Use `.limit()` for queries
   - Avoid N+1 queries
   - Use select_related for relationships

3. **Clean Old Data:**
   ```python
   # Delete old messages
   await repo.delete_old(chat_id, older_than_days=60)
   ```

4. **Increase Connection Pool:**
   ```python
   # In bot/db/session.py
   pool_size=20  # Default: 10
   max_overflow=40  # Default: 20
   ```

5. **Monitor Database:**
   ```bash
   # Check database size
   docker compose exec postgres psql -U bot -d gryag -c "\l+"
   
   # Check active connections
   docker compose exec postgres psql -U bot -d gryag -c "SELECT count(*) FROM pg_stat_activity;"
   ```

### Memory Issues

**Symptoms:**
- High memory usage
- Container OOM (Out of Memory) errors
- Slow performance

**Solutions:**

1. **Reduce Context Limits:**
   ```env
   IMMEDIATE_CONTEXT_MESSAGES=50
   CONTEXT_MAX_TOKENS=4000
   ```

2. **Enable More Summarization:**
   - Reduces context size
   - More frequent summaries

3. **Clean Old Data:**
   - Delete old messages
   - Archive old summaries
   - Clean up old logs

4. **Increase Container Memory:**
   ```yaml
   # docker-compose.yml
   services:
     bot:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

### Log Analysis

**Viewing Logs:**

```bash
# All logs
docker compose logs bot

# Follow logs
docker compose logs -f bot

# Last 100 lines
docker compose logs --tail=100 bot

# Filter errors
docker compose logs bot | grep -i error

# Log file
tail -f data/logs/bot_$(date +%Y-%m-%d).log
```

**Log Levels:**

```env
LOG_LEVEL=DEBUG   # Most verbose
LOG_LEVEL=INFO   # Default
LOG_LEVEL=WARNING # Warnings and errors
LOG_LEVEL=ERROR  # Errors only
```

**Common Log Messages:**

- `Bot authenticated: @botname` - Bot started successfully
- `Database initialized` - Database connected
- `Redis connected` - Redis connected (or warning if failed)
- `Executing tool X` - Tool execution
- `LLM error: ...` - LLM API error
- `Failed to store message` - Database error

### Performance Optimization

**Slow Responses:**

1. **Reduce Context:**
   - Lower `IMMEDIATE_CONTEXT_MESSAGES`
   - Enable more frequent summarization

2. **Optimize Database:**
   - Add indexes
   - Clean old data
   - Optimize queries

3. **Use Caching:**
   - Enable Redis
   - Cache frequently accessed data

4. **Optimize LLM Calls:**
   - Use faster models for summarization
   - Reduce max tokens
   - Use structured output

**High Resource Usage:**

1. **Monitor Resources:**
   ```bash
   docker stats
   ```

2. **Limit Resources:**
   ```yaml
   services:
     bot:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

3. **Scale Services:**
   - Use external PostgreSQL
   - Use external Redis
   - Consider horizontal scaling

## Debug Mode

### Enabling Debug Mode

```env
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### Debugging Tools

1. **Python Debugger:**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **Logging:**
   ```python
   logger.debug("Debug message")
   logger.info("Info message")
   ```

3. **Database Queries:**
   ```env
   LOG_LEVEL=DEBUG  # Logs all SQL queries
   ```

## Getting Help

### Before Asking for Help

1. **Check Logs:**
   - Review error messages
   - Check for patterns
   - Note timestamps

2. **Verify Configuration:**
   - Check `.env` file
   - Verify all required variables
   - Review documentation

3. **Test Components:**
   - Test database connection
   - Test LLM API
   - Test bot token

4. **Gather Information:**
   - Bot version
   - Configuration (sanitized)
   - Error messages
   - Log excerpts

### Reporting Issues

When reporting issues, include:

1. **Environment:**
   - OS and version
   - Docker version
   - Python version

2. **Configuration:**
   - Access mode
   - LLM provider
   - Database setup

3. **Error Details:**
   - Full error message
   - Stack trace
   - Log excerpts

4. **Steps to Reproduce:**
   - What you did
   - What happened
   - What you expected

## Related Documentation

- [Configuration](configuration.md) - Configuration troubleshooting
- [Deployment](deployment.md) - Deployment issues
- [Admin Guide](admin.md) - Admin troubleshooting
- [Development Guide](development.md) - Development issues