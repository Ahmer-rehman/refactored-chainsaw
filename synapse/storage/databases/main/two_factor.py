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
"""Database store for Two-Factor Authentication (2FA) data."""

import logging
from typing import List, Optional, Tuple

from synapse.storage.database import LoggingDatabaseConnection
from synapse.storage.databases.main.registration import RegistrationStore
from synapse.storage.types import Cursor

logger = logging.getLogger(__name__)


class TwoFactorStore(RegistrationStore):
    """Database store for 2FA operations."""

    async def is_2fa_enabled(self, user_id: str) -> bool:
        """
        Check if 2FA is enabled for a user.

        Args:
            user_id: The user ID to check

        Returns:
            True if 2FA is enabled, False otherwise
        """
        return await self.db_pool.simple_select_one_onecol(
            table="user_totp_secrets",
            keyvalues={"user_id": user_id},
            retcol="enabled",
            allow_none=True,
            desc="is_2fa_enabled",
        ) or False

    async def get_user_totp_secret(self, user_id: str) -> Optional[str]:
        """
        Get the TOTP secret for a user.

        Args:
            user_id: The user ID

        Returns:
            The TOTP secret (base32-encoded) or None if not set
        """
        return await self.db_pool.simple_select_one_onecol(
            table="user_totp_secrets",
            keyvalues={"user_id": user_id},
            retcol="secret",
            allow_none=True,
            desc="get_user_totp_secret",
        )

    async def set_user_totp_secret(
        self, user_id: str, secret: str, enabled: bool = False
    ) -> None:
        """
        Set or update the TOTP secret for a user.

        Args:
            user_id: The user ID
            secret: The TOTP secret (base32-encoded)
            enabled: Whether 2FA is enabled
        """
        await self.db_pool.simple_upsert(
            table="user_totp_secrets",
            keyvalues={"user_id": user_id},
            values={
                "secret": secret,
                "enabled": enabled,
                "created_ts": self._clock.time_msec(),
            },
            desc="set_user_totp_secret",
        )

    async def enable_2fa(self, user_id: str) -> None:
        """
        Enable 2FA for a user.

        Args:
            user_id: The user ID
        """
        await self.db_pool.simple_update(
            table="user_totp_secrets",
            keyvalues={"user_id": user_id},
            updatevalues={"enabled": True},
            desc="enable_2fa",
        )

    async def disable_2fa(self, user_id: str) -> None:
        """
        Disable 2FA for a user.

        Args:
            user_id: The user ID
        """
        await self.db_pool.simple_update(
            table="user_totp_secrets",
            keyvalues={"user_id": user_id},
            updatevalues={"enabled": False},
            desc="disable_2fa",
        )

    async def add_backup_codes(self, user_id: str, code_hashes: List[str]) -> None:
        """
        Add backup codes for a user.

        Args:
            user_id: The user ID
            code_hashes: List of SHA-256 hashes of backup codes
        """
        def add_backup_codes_txn(txn: Cursor) -> None:
            now = self._clock.time_msec()
            self.db_pool.simple_insert_many_txn(
                txn,
                table="user_backup_codes",
                values=[
                    {
                        "user_id": user_id,
                        "code_hash": code_hash,
                        "used": False,
                        "created_ts": now,
                    }
                    for code_hash in code_hashes
                ],
            )

        await self.db_pool.runInteraction("add_backup_codes", add_backup_codes_txn)

    async def verify_backup_code(self, user_id: str, code_hash: str) -> bool:
        """
        Verify and mark a backup code as used.

        Args:
            user_id: The user ID
            code_hash: SHA-256 hash of the backup code

        Returns:
            True if the code was valid and unused, False otherwise
        """
        def verify_backup_code_txn(txn: Cursor) -> bool:
            # Check if code exists and is unused
            row = self.db_pool.simple_select_one_txn(
                txn,
                table="user_backup_codes",
                keyvalues={"user_id": user_id, "code_hash": code_hash, "used": False},
                retcols=("code_hash",),
                allow_none=True,
            )

            if not row:
                return False

            # Mark as used
            self.db_pool.simple_update_one_txn(
                txn,
                table="user_backup_codes",
                keyvalues={"user_id": user_id, "code_hash": code_hash},
                updatevalues={"used": True, "used_ts": self._clock.time_msec()},
            )

            return True

        return await self.db_pool.runInteraction(
            "verify_backup_code", verify_backup_code_txn
        )

    async def get_unused_backup_codes_count(self, user_id: str) -> int:
        """
        Get the count of unused backup codes for a user.

        Args:
            user_id: The user ID

        Returns:
            Number of unused backup codes
        """
        def get_count_txn(txn: Cursor) -> int:
            txn.execute(
                "SELECT COUNT(*) FROM user_backup_codes WHERE user_id = ? AND used = ?",
                (user_id, False),
            )
            row = txn.fetchone()
            return row[0] if row else 0

        return await self.db_pool.runInteraction(
            "get_unused_backup_codes_count", get_count_txn
        )

