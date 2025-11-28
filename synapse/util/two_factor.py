#
# This file is licensed under the Affero General Public License (AGPL) version 3.
#
# Copyright 2014-2016 OpenMarket Ltd
# Copyright (C) 2023 New Vector, Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# See the GNU Affero General Public License for more details:
# <https://www.gnu.org/licenses/agpl-3.0.html>.
#
# Originally licensed under the Apache License, Version 2.0:
# <http://www.apache.org/licenses/LICENSE-2.0>.
#
# [This file includes modifications made by New Vector Limited]
#
"""
Two-Factor Authentication (2FA) utility service for Synapse.

This module provides TOTP (Time-based One-Time Password) functionality
for two-factor authentication.
"""

import base64
import hashlib
import hmac
import logging
import secrets
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import pyotp
    import qrcode
    from qrcode.image.pil import PilImage

    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
    logger.warning(
        "pyotp and qrcode libraries not available. 2FA functionality will be disabled."
    )


class TwoFactorAuthError(Exception):
    """Base exception for 2FA-related errors."""

    pass


class TwoFactorAuthService:
    """
    Service for managing Two-Factor Authentication using TOTP.

    This service provides functionality to:
    - Generate TOTP secrets
    - Generate QR codes for authenticator apps
    - Verify TOTP codes
    - Manage 2FA enrollment for users
    """

    # TOTP configuration
    TOTP_ISSUER = "Synapse Matrix Server"
    TOTP_DIGITS = 6  # Standard 6-digit codes
    TOTP_INTERVAL = 30  # 30-second time window
    TOTP_WINDOW = 1  # Allow 1 time step before/after current time

    def __init__(self, server_name: str):
        """
        Initialize the 2FA service.

        Args:
            server_name: The Matrix server name (e.g., "example.com")
        """
        if not TOTP_AVAILABLE:
            raise TwoFactorAuthError(
                "2FA service requires pyotp and qrcode libraries. "
                "Install them with: pip install pyotp qrcode[pil]"
            )

        self.server_name = server_name
        self.totp_issuer = f"{self.TOTP_ISSUER} ({server_name})"

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            A base32-encoded secret string suitable for TOTP generation.
        """
        # Generate 160 bits (20 bytes) of random data
        # This is the recommended secret length for TOTP (RFC 6238)
        random_bytes = secrets.token_bytes(20)
        secret = base64.b32encode(random_bytes).decode("utf-8")

        return secret

    def generate_totp_uri(
        self, user_id: str, secret: str, label: Optional[str] = None
    ) -> str:
        """
        Generate a TOTP URI for use with authenticator apps.

        Args:
            user_id: The Matrix user ID (e.g., "@user:example.com")
            secret: The TOTP secret (base32-encoded)
            label: Optional label for the account (defaults to user_id)

        Returns:
            A TOTP URI string (otpauth://totp/...)
        """
        if label is None:
            # Extract username from user_id (e.g., "@user:example.com" -> "user")
            if user_id.startswith("@"):
                label = user_id.split(":")[0][1:] if ":" in user_id else user_id[1:]
            else:
                label = user_id

        totp = pyotp.TOTP(secret, digits=self.TOTP_DIGITS, interval=self.TOTP_INTERVAL)

        # Format: otpauth://totp/Issuer:Label?secret=SECRET&issuer=Issuer&algorithm=SHA1&digits=6&period=30
        uri = totp.provisioning_uri(
            name=label,
            issuer_name=self.totp_issuer,
        )

        return uri

    def generate_qr_code(self, uri: str) -> bytes:
        """
        Generate a QR code image from a TOTP URI.

        Args:
            uri: The TOTP URI string

        Returns:
            PNG image bytes of the QR code
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        # Convert PIL image to PNG bytes
        import io

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        return img_bytes.getvalue()

    def verify_totp(self, secret: str, code: str) -> bool:
        """
        Verify a TOTP code against a secret.

        Args:
            secret: The TOTP secret (base32-encoded)
            code: The 6-digit code to verify

        Returns:
            True if the code is valid, False otherwise
        """
        if not code or len(code) != self.TOTP_DIGITS:
            return False

        if not code.isdigit():
            return False

        try:
            totp = pyotp.TOTP(secret, digits=self.TOTP_DIGITS, interval=self.TOTP_INTERVAL)
            # Verify with a window to account for clock skew
            return totp.verify(code, valid_window=self.TOTP_WINDOW)
        except Exception as e:
            logger.warning("Error verifying TOTP code: %s", e)
            return False

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """
        Generate backup codes for 2FA recovery.

        Args:
            count: Number of backup codes to generate (default: 10)

        Returns:
            List of backup codes (each is 8 characters, alphanumeric)
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = secrets.token_urlsafe(6).upper().replace("-", "").replace("_", "")[:8]
            codes.append(code)

        return codes

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage.

        Args:
            code: The plain backup code

        Returns:
            SHA-256 hash of the code (hex-encoded)
        """
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """
        Verify a backup code against its hash.

        Args:
            code: The plain backup code to verify
            hashed_code: The stored hash of the backup code

        Returns:
            True if the code matches, False otherwise
        """
        computed_hash = self.hash_backup_code(code)
        return hmac.compare_digest(computed_hash, hashed_code)

