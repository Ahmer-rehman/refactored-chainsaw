# Nginx Configuration for stg-adm-im-ma.bservices-api.org.pk

This directory contains nginx configuration files for the staging admin Synapse server.

## Files

- `stg-adm-nginx.conf` - Main nginx configuration file

## Security Fixes Applied

This configuration addresses all security vulnerabilities identified in the Acunetix audit:

### 1. TLS/SSL Weak Cipher Suites ✅ FIXED
- **Issue**: Server was offering weak CBC cipher suites
- **Fix**: 
  - Disabled TLS 1.0 and 1.1 (only TLS 1.2 and 1.3 allowed)
  - Removed all weak CBC ciphers
  - Only strong GCM and ChaCha20-Poly1305 ciphers enabled
  - Based on Mozilla's "Modern" SSL configuration

### 2. Missing Security Headers ✅ FIXED
- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **Permissions-Policy**: Restricts browser features (geolocation, microphone, camera, etc.)
- **Content-Security-Policy**: Enhanced with `object-src 'none'` to prevent plugin injection
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **X-Frame-Options**: `DENY` - Prevents clickjacking

### 3. SSL Certificate Hostname Mismatch ⚠️ ACTION REQUIRED
- **Issue**: Certificate is for `5.staging.averox.com` but server is `stg-adm-im-ma.bservices-api.org.pk`
- **Action Required**: 
  1. Obtain a new SSL certificate for `stg-adm-im-ma.bservices-api.org.pk`
  2. Update certificate paths in the configuration:
     - `ssl_certificate /etc/ssl/certs/stg-adm-im-ma.bservices-api.org.pk.crt`
     - `ssl_certificate_key /etc/ssl/private/stg-adm-im-ma.bservices-api.org.pk.key`
  3. Consider using Let's Encrypt for free certificates:
     ```bash
     certbot certonly --nginx -d stg-adm-im-ma.bservices-api.org.pk
     ```

## Installation

1. **Copy configuration file**:
   ```bash
   sudo cp nginx/stg-adm-nginx.conf /etc/nginx/sites-available/stg-adm-im-ma.bservices-api.org.pk
   ```

2. **Create symbolic link**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/stg-adm-im-ma.bservices-api.org.pk /etc/nginx/sites-enabled/
   ```

3. **Remove default site** (if exists):
   ```bash
   sudo rm /etc/nginx/sites-enabled/default
   ```

4. **Test configuration**:
   ```bash
   sudo nginx -t
   ```

5. **Reload nginx**:
   ```bash
   sudo systemctl reload nginx
   ```

## Configuration Details

### Ports
- **443**: Client port (HTTPS) - for Matrix clients
- **8448**: Federation port (HTTPS) - for server-to-server communication
- **80**: HTTP redirect to HTTPS

### Upstream
- Synapse backend: `127.0.0.1:8008`
- Keepalive connections: 32

### Rate Limiting
- Matrix API: 10 requests/second with burst of 20
- Static files: 50 requests/second with burst of 50

### File Upload
- Maximum body size: 100M (adjust to match `max_upload_size` in `homeserver.yaml`)

## SSL Certificate Setup (Let's Encrypt)

If using Let's Encrypt:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d stg-adm-im-ma.bservices-api.org.pk

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

## Verification

After deployment, verify the configuration:

1. **Test SSL configuration**:
   ```bash
   openssl s_client -connect stg-adm-im-ma.bservices-api.org.pk:443 -servername stg-adm-im-ma.bservices-api.org.pk
   ```

2. **Check SSL Labs rating**:
   - Visit: https://www.ssllabs.com/ssltest/
   - Enter: `stg-adm-im-ma.bservices-api.org.pk`
   - Should achieve A or A+ rating

3. **Verify security headers**:
   ```bash
   curl -I https://stg-adm-im-ma.bservices-api.org.pk/_matrix/client/versions
   ```
   Should see:
   - `X-Content-Type-Options: nosniff`
   - `Permissions-Policy: ...`
   - `Content-Security-Policy: ...`
   - `X-Frame-Options: DENY`

4. **Test Matrix endpoints**:
   ```bash
   curl https://stg-adm-im-ma.bservices-api.org.pk/_matrix/client/versions
   ```

## Troubleshooting

### Certificate Issues
- Ensure certificate file paths are correct
- Check file permissions (certificate should be readable by nginx user)
- Verify certificate matches the server name

### Connection Issues
- Verify Synapse is running on port 8008: `sudo netstat -tlnp | grep 8008`
- Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Check Synapse logs for connection errors

### Rate Limiting
- If legitimate traffic is being rate limited, adjust limits in the configuration
- Check rate limit logs: `sudo tail -f /var/log/nginx/access.log`

## Additional Security Recommendations

1. **Enable HSTS** (after confirming SSL works correctly):
   - Uncomment the `Strict-Transport-Security` header in the configuration
   - This tells browsers to always use HTTPS for this domain

2. **Firewall Configuration**:
   - Only allow ports 80, 443, and 8448 from the internet
   - Restrict port 8008 to localhost only

3. **Regular Updates**:
   - Keep nginx updated: `sudo apt-get update && sudo apt-get upgrade nginx`
   - Monitor security advisories for nginx

4. **Logging**:
   - Monitor access logs for suspicious activity
   - Set up log rotation to prevent disk space issues

## Notes

- The configuration assumes Synapse is running on `localhost:8008`
- Adjust `client_max_body_size` to match your `homeserver.yaml` `max_upload_size` setting
- Admin endpoints (`/_synapse/admin`) are blocked from public access
- Health check endpoint (`/_matrix/client/versions`) has no rate limiting

