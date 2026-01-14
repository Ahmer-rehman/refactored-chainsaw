# Synapse Deployment Guide

This directory contains a security-hardened Matrix Synapse deployment with all Acunetix audit fixes applied.

## 🔒 Security Features

✅ **All Acunetix Code-Level Vulnerabilities Fixed**:
- jQuery upgraded to 3.7.1 (fixes CVE-2020-11022, CVE-2020-11023, CVE-2020-23064)
- Content Security Policy (CSP) implemented
- X-Content-Type-Options header added
- Permissions-Policy header implemented
- Strong TLS cipher configuration
- IP blacklists to prevent SSRF attacks
- Rate limiting enabled
- Strong password policy

## 📁 Directory Structure

```
refactored-chainsaw/
├── docker-compose.yaml          # Docker Compose configuration
├── data/
│   ├── homeserver.yaml         # Main Synapse configuration
│   ├── log.config              # Logging configuration
│   ├── signing.key             # Generated on first run
│   ├── media_store/            # Media uploads (created on first run)
│   └── homeserver.log          # Application logs
├── nginx/
│   └── stg-adm-nginx.conf      # Nginx reverse proxy config (optional)
├── synapse/                     # Synapse source code with security fixes
├── docker/                      # Docker build files
└── SECURITY_FIXES_ACUNETIX.md  # Security audit documentation
```

## 🚀 Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- At least 2GB RAM available
- Ports 8008 and 8448 available

### 2. Initial Setup

```bash
# Navigate to the directory
cd "/root/code backups/refactored-chainsaw"

# Create required directories
mkdir -p data/media_store

# Set proper permissions
chmod 700 data

# Generate signing key (first time only)
docker compose run --rm synapse generate

# Or manually generate:
# docker run -it --rm \
#   -v $(pwd)/data:/data \
#   -e SYNAPSE_SERVER_NAME=stg-adm-im-ma.bservices-api.org.pk \
#   -e SYNAPSE_REPORT_STATS=no \
#   matrixdotorg/synapse:latest generate
```

### 3. Configure Environment Variables

Create a `.env` file:

```bash
cat > .env << 'EOF'
# PostgreSQL password (change this!)
POSTGRES_PASSWORD=your_secure_password_here

# Synapse configuration
SYNAPSE_SERVER_NAME=stg-adm-im-ma.bservices-api.org.pk
SYNAPSE_REPORT_STATS=no
EOF
```

### 4. Update Configuration

Edit `data/homeserver.yaml`:

```yaml
# Update these settings:
server_name: "your-domain.com"
public_baseurl: "https://your-domain.com/"

# Database password (match .env file)
database:
  args:
    password: your_secure_password_here

# Enable registration if needed
enable_registration: true
```

### 5. Build and Start

```bash
# Build the custom Synapse image
docker compose build

# Start all services
docker compose up -d

# Check logs
docker compose logs -f synapse

# Check health
curl http://localhost:8008/health
```

## 👤 Create Admin User

```bash
# Create an admin user
docker compose exec synapse register_new_matrix_user \
  -c /data/homeserver.yaml \
  -u admin \
  -p your_password \
  -a \
  http://localhost:8008
```

## 🔧 Configuration Options

### Enable Registration

Edit `data/homeserver.yaml`:

```yaml
enable_registration: true
enable_registration_without_verification: false
```

### Configure Email (Optional)

```yaml
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "your-email@gmail.com"
  smtp_pass: "your-app-password"
  require_transport_security: true
  notif_from: "Matrix <your-email@gmail.com>"
```

### Enable RADIUS Authentication (Optional)

1. Uncomment the `radius` service in `docker-compose.yaml`
2. Configure RADIUS in `data/homeserver.yaml`:

```yaml
password_providers:
  - module: "radius_auth_provider.RadiusAuthProvider"
    config:
      host: "radius"
      port: 1812
      secret: "testing123"
```

### Enable Nginx Reverse Proxy (Recommended)

1. Obtain SSL certificate for your domain
2. Place certificates in `./ssl/` directory
3. Uncomment `nginx` service in `docker-compose.yaml`
4. Update `nginx/stg-adm-nginx.conf` with your domain
5. Restart: `docker compose up -d nginx`

## 🔍 Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Synapse only
docker compose logs -f synapse

# PostgreSQL
docker compose logs -f postgres
```

### Check Service Status

```bash
# All services
docker compose ps

# Health check
curl http://localhost:8008/health

# Federation test
curl https://federationtester.matrix.org/api/report?server_name=your-domain.com
```

### Database Backup

```bash
# Backup PostgreSQL database
docker compose exec postgres pg_dump -U synapse synapse > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T postgres psql -U synapse synapse < backup_20260114.sql
```

## 🛡️ Security Checklist

Before going to production:

- [ ] Change default PostgreSQL password in `.env`
- [ ] Update `server_name` and `public_baseurl` in `homeserver.yaml`
- [ ] Obtain proper SSL certificate for your domain
- [ ] Deploy nginx reverse proxy with strong TLS ciphers
- [ ] Fix DNS configuration (remove localhost records)
- [ ] Enable firewall rules (allow only 80, 443, 8448)
- [ ] Set up automated backups
- [ ] Enable HSTS in nginx (after SSL is working)
- [ ] Review and adjust rate limiting settings
- [ ] Configure email for password resets
- [ ] Set up monitoring and alerting

## 🔄 Maintenance

### Update Synapse

```bash
# Pull latest changes
git pull

# Rebuild image
docker compose build synapse

# Restart with new image
docker compose up -d synapse
```

### Clean Up Old Data

```bash
# Remove old media (older than 90 days)
docker compose exec synapse \
  synapse_media_cleanup \
  --before="90 days ago" \
  /data/homeserver.yaml

# Vacuum database
docker compose exec postgres vacuumdb -U synapse -d synapse -z -v
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart synapse

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

## 🐛 Troubleshooting

### Synapse won't start

```bash
# Check logs
docker compose logs synapse

# Verify configuration
docker compose exec synapse python -m synapse.config -c /data/homeserver.yaml

# Check permissions
ls -la data/
```

### Database connection issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U synapse -d synapse -c "SELECT 1;"

# Check password in homeserver.yaml matches .env
```

### Port already in use

```bash
# Find process using port 8008
sudo lsof -i :8008

# Change port in docker-compose.yaml
ports:
  - "8009:8008"  # Use different external port
```

## 📚 Additional Resources

- [Synapse Documentation](https://matrix-org.github.io/synapse/latest/)
- [Matrix Specification](https://spec.matrix.org/)
- [Federation Tester](https://federationtester.matrix.org/)
- [Security Best Practices](https://matrix.org/docs/guides/moderation/)

## 🆘 Support

For issues related to:
- **Security fixes**: See `SECURITY_FIXES_ACUNETIX.md`
- **Deployment**: Check this README
- **Synapse bugs**: https://github.com/matrix-org/synapse/issues
- **Matrix protocol**: https://matrix.org/docs/

## 📝 License

This deployment configuration is provided as-is. Synapse is licensed under Apache 2.0.

---

**Last Updated**: 2026-01-14  
**Synapse Version**: Latest (with security patches)  
**Security Audit**: Acunetix fixes applied
