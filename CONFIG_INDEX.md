# Configuration Files Index

This document provides an overview of all configuration files in the deployment.

## Directory Structure

```
refactored-chainsaw/
├── config/                      # All configuration files
│   ├── redis.conf              # Redis configuration
│   ├── radius/                 # RADIUS authentication
│   │   ├── clients.conf        # RADIUS clients
│   │   └── users               # RADIUS users
│   ├── postgres/               # PostgreSQL configuration
│   │   └── init-db.sh          # Database initialization script
│   └── ssl/                    # SSL certificates (create this)
│       ├── cert.crt            # SSL certificate
│       └── cert.key            # SSL private key
├── data/                        # Synapse data directory
│   ├── homeserver.yaml         # Main Synapse configuration
│   ├── log.config              # Logging configuration
│   ├── signing.key             # Generated signing key
│   ├── media_store/            # Media uploads
│   └── homeserver.log          # Application logs
├── scripts/                     # Utility scripts
│   ├── backup.sh               # Backup script
│   └── restore.sh              # Restore script
├── logs/                        # Log files
│   └── radius/                 # RADIUS logs
├── backups/                     # Backup storage
├── nginx/                       # Nginx configuration
│   └── stg-adm-nginx.conf      # Nginx reverse proxy config
├── docker-compose.yaml          # Docker Compose configuration
├── .env.example                 # Environment variables template
└── DEPLOYMENT_GUIDE.md          # Deployment instructions
```

## Configuration Files

### 1. Docker Compose (`docker-compose.yaml`)

Main orchestration file for all services:
- **Synapse**: Matrix homeserver
- **PostgreSQL**: Database backend
- **Redis**: Caching and pub/sub
- **RADIUS**: Authentication (optional)
- **Nginx**: Reverse proxy (optional)

**Key Settings**:
- Ports: 8008 (client), 8448 (federation)
- Networks: synapse-network (bridge)
- Volumes: Persistent data storage

### 2. Environment Variables (`.env`)

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
nano .env
```

**Required Variables**:
- `POSTGRES_PASSWORD`: Database password
- `SYNAPSE_SERVER_NAME`: Your domain name
- `SYNAPSE_REPORT_STATS`: Statistics reporting (yes/no)

### 3. Synapse Configuration (`data/homeserver.yaml`)

Main Synapse configuration file.

**Critical Settings**:
```yaml
server_name: "your-domain.com"          # Your Matrix server domain
public_baseurl: "https://your-domain.com/"
enable_registration: false               # User registration
```

**Database Configuration**:
```yaml
database:
  name: psycopg2
  args:
    password: your_postgres_password    # Match .env
```

**Security Settings**:
- Password policy (8+ chars, symbols, etc.)
- Rate limiting
- IP blacklists (prevent SSRF)
- Federation controls

**See Also**: [Synapse Config Docs](https://matrix-org.github.io/synapse/latest/usage/configuration/config_documentation.html)

### 4. Logging Configuration (`data/log.config`)

Python logging configuration for Synapse.

**Features**:
- Daily log rotation
- Console and file output
- Configurable log levels
- 7-day retention

**Log Levels**:
- `DEBUG`: Detailed debugging
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages

### 5. Redis Configuration (`config/redis.conf`)

Redis server configuration optimized for Synapse.

**Key Settings**:
- **Memory**: 256MB limit with LRU eviction
- **Persistence**: RDB snapshots every 60 seconds
- **Security**: Protected mode enabled
- **Performance**: Optimized for pub/sub workload

**To enable password protection**:
```conf
requirepass your_redis_password_here
```

### 6. RADIUS Configuration (`config/radius/`)

FreeRADIUS server configuration for authentication.

#### `clients.conf`
Defines which clients can connect to RADIUS:
```conf
client synapse {
    ipaddr = synapse
    secret = testing123    # Change in production!
}
```

#### `users`
Defines user accounts:
```conf
admin Cleartext-Password := "admin123"
```

**Security Note**: Use strong secrets and passwords in production!

### 7. PostgreSQL Configuration (`config/postgres/`)

#### `init-db.sh`
Database initialization script that runs on first start:
- Creates required extensions (pg_trgm)
- Sets locale to C (required by Synapse)
- Grants permissions

**Mounted as**: `/docker-entrypoint-initdb.d/init-db.sh`

### 8. Nginx Configuration (`nginx/stg-adm-nginx.conf`)

Reverse proxy configuration with security hardening.

**Security Features**:
- Strong TLS ciphers only (TLS 1.2+)
- Security headers (CSP, X-Content-Type-Options, etc.)
- Rate limiting
- OCSP stapling

**SSL Certificate Paths**:
```nginx
ssl_certificate /etc/ssl/certs/your-domain.crt;
ssl_certificate_key /etc/ssl/private/your-domain.key;
```

**See Also**: `SECURITY_FIXES_ACUNETIX.md` for security details

## Scripts

### Backup Script (`scripts/backup.sh`)

Automated backup of all data:

```bash
./scripts/backup.sh
```

**Backs up**:
- PostgreSQL database (compressed)
- Synapse data directory
- Configuration files
- Media store (optional)

**Retention**: Keeps last 7 days of backups

### Restore Script (`scripts/restore.sh`)

Restore from backup:

```bash
./scripts/restore.sh 20260114_120000
```

**Restores**:
- Database
- Data directory
- Configuration
- Media files

## Quick Configuration Guide

### Initial Setup

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit environment variables**:
   ```bash
   nano .env
   # Set POSTGRES_PASSWORD and SYNAPSE_SERVER_NAME
   ```

3. **Edit homeserver.yaml**:
   ```bash
   nano data/homeserver.yaml
   # Update server_name and database password
   ```

4. **Generate signing key**:
   ```bash
   docker compose run --rm synapse generate
   ```

### Enable Features

#### Enable Registration
```yaml
# data/homeserver.yaml
enable_registration: true
```

#### Enable Email
```yaml
# data/homeserver.yaml
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your-email@gmail.com"
  smtp_pass: "your-app-password"
```

#### Enable RADIUS
```yaml
# docker-compose.yaml
# Uncomment radius service

# data/homeserver.yaml
password_providers:
  - module: "radius_auth_provider.RadiusAuthProvider"
    config:
      host: "radius"
      secret: "testing123"
```

#### Enable Nginx
```yaml
# docker-compose.yaml
# Uncomment nginx service

# Place SSL certificates in config/ssl/
```

## Security Checklist

Before production deployment:

- [ ] Change `POSTGRES_PASSWORD` in `.env`
- [ ] Update `server_name` in `homeserver.yaml`
- [ ] Change RADIUS `secret` in `config/radius/clients.conf`
- [ ] Update RADIUS user passwords in `config/radius/users`
- [ ] Obtain SSL certificate for your domain
- [ ] Enable Redis password in `config/redis.conf`
- [ ] Review rate limiting settings
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Enable monitoring

## Troubleshooting

### Configuration Validation

```bash
# Test Synapse configuration
docker compose exec synapse python -m synapse.config -c /data/homeserver.yaml

# Test Nginx configuration
docker compose exec nginx nginx -t

# Test Redis configuration
docker compose exec redis redis-cli CONFIG GET '*'
```

### View Current Configuration

```bash
# View Synapse config
docker compose exec synapse cat /data/homeserver.yaml

# View Redis config
docker compose exec redis cat /usr/local/etc/redis/redis.conf
```

## References

- [Synapse Configuration Docs](https://matrix-org.github.io/synapse/latest/usage/configuration/config_documentation.html)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [FreeRADIUS Documentation](https://freeradius.org/documentation/)
- [Nginx SSL Configuration](https://ssl-config.mozilla.org/)

---

**Last Updated**: 2026-01-14  
**Configuration Version**: 1.0
