# Two-Factor Authentication (2FA) Implementation

This document describes the 2FA service implementation for Synapse Matrix server.

## Overview

The 2FA service provides TOTP (Time-based One-Time Password) two-factor authentication for enhanced security. Users can enable 2FA on their accounts and must provide both their password and a TOTP code from an authenticator app to log in.

## Components

### 1. Utility Module (`synapse/util/two_factor.py`)
- **TwoFactorAuthService**: Core service for TOTP operations
  - `generate_secret()`: Generate new TOTP secrets
  - `generate_totp_uri()`: Create TOTP URI for QR codes
  - `generate_qr_code()`: Generate QR code images
  - `verify_totp()`: Verify TOTP codes
  - `generate_backup_codes()`: Generate recovery codes
  - `hash_backup_code()` / `verify_backup_code()`: Secure backup code handling

### 2. Database Schema (`synapse/storage/schema/main/delta/89/01_two_factor_auth.sql`)
- **user_totp_secrets**: Stores TOTP secrets for users
  - `user_id`: Primary key
  - `secret`: Base32-encoded TOTP secret
  - `enabled`: Whether 2FA is enabled
  - `created_ts`: Timestamp when secret was created

- **user_backup_codes**: Stores hashed backup codes
  - `user_id`: User identifier
  - `code_hash`: SHA-256 hash of backup code
  - `used`: Whether code has been used
  - `created_ts` / `used_ts`: Timestamps

### 3. Dependencies Added
- `pyotp >= 2.9.0`: TOTP implementation
- `qrcode[pil] >= 7.4.2`: QR code generation

## API Endpoints (To Be Implemented)

### Enable 2FA
```
POST /_matrix/client/v1/account/2fa/enable
```
Generates a new TOTP secret and returns QR code for setup.

### Verify and Enable 2FA
```
POST /_matrix/client/v1/account/2fa/verify
Body: { "code": "123456" }
```
Verifies the TOTP code and enables 2FA if valid.

### Disable 2FA
```
POST /_matrix/client/v1/account/2fa/disable
Body: { "password": "user_password" }
```
Disables 2FA for the user (requires password verification).

### Get Backup Codes
```
GET /_matrix/client/v1/account/2fa/backup_codes
```
Returns unused backup codes for the user.

### Verify TOTP During Login
```
POST /_matrix/client/v1/login
Body: {
  "type": "m.login.password",
  "user": "@user:example.com",
  "password": "password",
  "two_factor_code": "123456"  // Required if 2FA enabled
}
```

## Integration Points

1. **Login Flow** (`synapse/handlers/auth.py`):
   - After password verification, check if user has 2FA enabled
   - If enabled, require TOTP code verification
   - Return error if code is missing or invalid

2. **Store Methods** (To be created in `synapse/storage/databases/main/two_factor.py`):
   - `get_user_totp_secret(user_id)`: Get TOTP secret
   - `set_user_totp_secret(user_id, secret, enabled)`: Store/update secret
   - `is_2fa_enabled(user_id)`: Check if 2FA is enabled
   - `add_backup_codes(user_id, codes)`: Store backup codes
   - `verify_backup_code(user_id, code)`: Verify and mark backup code as used

## Security Considerations

1. **Secret Storage**: TOTP secrets are stored in plaintext (required for TOTP generation)
2. **Backup Codes**: Hashed using SHA-256 before storage
3. **Rate Limiting**: Should be applied to 2FA verification endpoints
4. **Session Management**: 2FA verification should be required for sensitive operations
5. **Recovery**: Backup codes provide recovery mechanism if device is lost

## Usage Example

```python
from synapse.util.two_factor import TwoFactorAuthService

# Initialize service
service = TwoFactorAuthService(server_name="example.com")

# Generate secret
secret = service.generate_secret()

# Generate QR code URI
uri = service.generate_totp_uri("@user:example.com", secret)

# Generate QR code image
qr_image = service.generate_qr_code(uri)

# Verify code
is_valid = service.verify_totp(secret, "123456")
```

## Next Steps

1. ✅ Create utility module
2. ✅ Create database schema
3. ✅ Add dependencies
4. ⏳ Create store methods
5. ⏳ Create REST API endpoints
6. ⏳ Integrate into login flow
7. ⏳ Add tests

## Notes

- Schema version updated to 89
- The implementation follows Synapse's existing patterns
- TOTP uses standard 6-digit codes with 30-second intervals
- Backup codes are 8-character alphanumeric strings

