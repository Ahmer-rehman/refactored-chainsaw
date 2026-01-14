# Matrix Synapse - Security-Hardened Deployment

[![Security](https://img.shields.io/badge/Security-Hardened-green.svg)](SECURITY_FIXES_ACUNETIX.md)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](docker-compose.yaml)
[![Matrix](https://img.shields.io/badge/Matrix-Synapse-black.svg)](https://matrix.org)

A production-ready Matrix Synapse deployment with all Acunetix security audit fixes applied.

## 🔒 Security Features

✅ **All Acunetix Code-Level Vulnerabilities Fixed**
- jQuery upgraded to 3.7.1 (fixes CVE-2020-11022, CVE-2020-11023, CVE-2020-23064)
- Content Security Policy (CSP) implemented
- X-Content-Type-Options header added
- Permissions-Policy header implemented
- Strong TLS cipher configuration
- IP blacklists to prevent SSRF attacks
- Comprehensive security headers

See [SECURITY_FIXES_ACUNETIX.md](SECURITY_FIXES_ACUNETIX.md) for complete security audit details.

## 📋 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./quick-start.sh
```

This interactive script will:
- Create environment configuration
- Generate signing keys
- Set up directories
- Build and start services
- Create admin user

### Option 2: Manual Setup

```bash
# 1. Copy environment template
cp .env.example .env
nano .env  # Edit with your settings

# 2. Create directories
mkdir -p data/media_store logs/radius backups config/ssl
chmod 700 data

# 3. Generate signing key
docker compose run --rm synapse generate

# 4. Build and start
docker compose build
docker compose up -d

# 5. Create admin user
docker compose exec synapse register_new_matrix_user \
  -c /data/homeserver.yaml -u admin -a http://localhost:8008
```

## 📁 Project Structure

```
refactored-chainsaw/
├── 📄 docker-compose.yaml       # Main orchestration file
├── 📄 .env.example              # Environment variables template
├── 🚀 quick-start.sh            # Automated setup script
│
├── 📁 config/                   # All configuration files
│   ├── redis.conf              # Redis configuration
│   ├── radius/                 # RADIUS authentication
│   │   ├── clients.conf        # RADIUS clients
│   │   └── users               # RADIUS users
│   ├── postgres/               # PostgreSQL configuration
│   │   └── init-db.sh          # Database initialization
│   └── ssl/                    # SSL certificates (create this)
│
├── 📁 data/                     # Synapse data (persistent)
│   ├── homeserver.yaml         # Main Synapse config
│   ├── log.config              # Logging config
│   ├── signing.key             # Generated signing key
│   ├── media_store/            # Media uploads
│   └── homeserver.log          # Application logs
│
├── 📁 scripts/                  # Utility scripts
│   ├── backup.sh               # Backup script
│   └── restore.sh              # Restore script
│
├── 📁 nginx/                    # Nginx reverse proxy
│   └── stg-adm-nginx.conf      # Security-hardened config
│
├── 📁 logs/                     # Log files
├── 📁 backups/                  # Backup storage
│
└── 📚 Documentation
    ├── README.md                # This file
    ├── DEPLOYMENT_GUIDE.md      # Detailed deployment guide
    ├── CONFIG_INDEX.md          # Configuration reference
    ├── SECURITY_FIXES_ACUNETIX.md  # Security audit fixes
    └── ACUNETIX_VERIFICATION_REPORT.md  # Verification report
```

## 🛠️ Services

| Service | Description | Port | Status |
|---------|-------------|------|--------|
| **Synapse** | Matrix homeserver | 8008, 8448 | Required |
| **PostgreSQL** | Database backend | 5432 | Required |
| **Redis** | Caching & pub/sub | 6379 | Required |
| **RADIUS** | Authentication | 1812/udp | Optional |
| **Nginx** | Reverse proxy | 80, 443 | Optional |

## ⚙️ Configuration

### Essential Configuration

1. **Environment Variables** (`.env`):
   ```bash
   POSTGRES_PASSWORD=your_secure_password
   SYNAPSE_SERVER_NAME=matrix.example.com
   ```

2. **Homeserver Config** (`data/homeserver.yaml`):
   ```yaml
   server_name: "matrix.example.com"
   public_baseurl: "https://matrix.example.com/"
   enable_registration: false
   ```

3. **Database Password**:
   Must match in both `.env` and `data/homeserver.yaml`

### Optional Features

#### Enable User Registration
```yaml
# data/homeserver.yaml
enable_registration: true
```

#### Enable Email Notifications
```yaml
# data/homeserver.yaml
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your-email@gmail.com"
  smtp_pass: "your-app-password"
```

#### Enable RADIUS Authentication
```bash
# 1. Uncomment radius service in docker-compose.yaml
# 2. Configure in homeserver.yaml:
password_providers:
  - module: "radius_auth_provider.RadiusAuthProvider"
    config:
      host: "radius"
      secret: "testing123"
```

#### Enable Nginx Reverse Proxy
```bash
# 1. Obtain SSL certificate
# 2. Place in config/ssl/
# 3. Uncomment nginx service in docker-compose.yaml
# 4. Start: docker compose up -d nginx
```

See [CONFIG_INDEX.md](CONFIG_INDEX.md) for complete configuration reference.

## 🚀 Common Operations

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f synapse
docker compose logs -f postgres
```

### Manage Users
```bash
# Create user
docker compose exec synapse register_new_matrix_user \
  -c /data/homeserver.yaml http://localhost:8008

# Create admin user
docker compose exec synapse register_new_matrix_user \
  -c /data/homeserver.yaml -u admin -a http://localhost:8008

# Deactivate user
docker compose exec synapse synapse_admin_user \
  -c /data/homeserver.yaml deactivate @user:domain.com
```

### Backup & Restore
```bash
# Create backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh 20260114_120000

# List available backups
ls -lh backups/
```

### Service Management
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart specific service
docker compose restart synapse

# View service status
docker compose ps

# Update and restart
docker compose pull
docker compose up -d
```

### Health Checks
```bash
# Check Synapse health
curl http://localhost:8008/health

# Check federation
curl https://federationtester.matrix.org/api/report?server_name=your-domain.com

# Check database connection
docker compose exec postgres psql -U synapse -d synapse -c "SELECT 1;"

# Check Redis
docker compose exec redis redis-cli PING
```

## 🔧 Troubleshooting

### Synapse Won't Start
```bash
# Check logs
docker compose logs synapse

# Validate configuration
docker compose exec synapse python -m synapse.config -c /data/homeserver.yaml

# Check file permissions
ls -la data/
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U synapse -d synapse -c "SELECT 1;"

# Verify password matches in .env and homeserver.yaml
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8008

# Change port in docker-compose.yaml
ports:
  - "8009:8008"  # Use different external port
```

### Out of Memory
```bash
# Check memory usage
docker stats

# Increase Redis memory limit in config/redis.conf:
maxmemory 512mb

# Restart Redis
docker compose restart redis
```

## 📊 Monitoring

### Resource Usage
```bash
# View resource usage
docker stats

# Check disk usage
du -sh data/
du -sh data/media_store/
```

### Database Maintenance
```bash
# Vacuum database
docker compose exec postgres vacuumdb -U synapse -d synapse -z -v

# Check database size
docker compose exec postgres psql -U synapse -d synapse -c \
  "SELECT pg_size_pretty(pg_database_size('synapse'));"
```

### Clean Old Media
```bash
# Remove media older than 90 days
docker compose exec synapse \
  synapse_media_cleanup \
  --before="90 days ago" \
  /data/homeserver.yaml
```

## 🔐 Security Checklist

Before production deployment:

- [ ] Change `POSTGRES_PASSWORD` in `.env`
- [ ] Update `server_name` in `homeserver.yaml`
- [ ] Obtain SSL certificate for your domain
- [ ] Deploy nginx reverse proxy
- [ ] Enable HSTS in nginx (after SSL works)
- [ ] Change RADIUS secrets (if using)
- [ ] Enable Redis password (if exposed)
- [ ] Configure firewall (allow only 80, 443, 8448)
- [ ] Set up automated backups
- [ ] Review rate limiting settings
- [ ] Configure email for password resets
- [ ] Set up monitoring and alerting
- [ ] Review and test disaster recovery

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[CONFIG_INDEX.md](CONFIG_INDEX.md)** - Configuration file reference
- **[SECURITY_FIXES_ACUNETIX.md](SECURITY_FIXES_ACUNETIX.md)** - Security audit fixes
- **[Synapse Docs](https://matrix-org.github.io/synapse/latest/)** - Official documentation
- **[Matrix Spec](https://spec.matrix.org/)** - Matrix protocol specification

## 🆘 Support

- **Security Issues**: See [SECURITY_FIXES_ACUNETIX.md](SECURITY_FIXES_ACUNETIX.md)
- **Deployment Help**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Synapse Issues**: https://github.com/matrix-org/synapse/issues
- **Matrix Community**: https://matrix.to/#/#synapse:matrix.org

## 📝 License

This deployment configuration is provided as-is. Matrix Synapse is licensed under Apache 2.0.

## 🙏 Acknowledgments

- Security hardening based on Acunetix security audit
- Matrix Synapse by Matrix.org Foundation
- Community contributions and best practices

---

**Version**: 1.0  
**Last Updated**: 2026-01-14  
**Security Audit**: Acunetix fixes applied ✅
