--
-- This file is licensed under the Affero General Public License (AGPL) version 3.
--
-- Copyright (C) 2024 New Vector, Ltd
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as
-- published by the Free Software Foundation, either version 3 of the
-- License, or (at your option) any later version.
--
-- See the GNU Affero General Public License for more details:
-- <https://www.gnu.org/licenses/agpl-3.0.html>.
--
-- Schema delta for Two-Factor Authentication (2FA) support
--

-- Table to store TOTP secrets for users
CREATE TABLE IF NOT EXISTS user_totp_secrets (
    user_id TEXT NOT NULL PRIMARY KEY,
    secret TEXT NOT NULL,  -- Base32-encoded TOTP secret
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_ts BIGINT NOT NULL,
    UNIQUE(user_id)
);

-- Table to store backup codes for 2FA recovery
CREATE TABLE IF NOT EXISTS user_backup_codes (
    user_id TEXT NOT NULL,
    code_hash TEXT NOT NULL,  -- SHA-256 hash of the backup code
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_ts BIGINT NOT NULL,
    used_ts BIGINT,
    PRIMARY KEY (user_id, code_hash)
);

CREATE INDEX IF NOT EXISTS user_backup_codes_user_id ON user_backup_codes(user_id);
CREATE INDEX IF NOT EXISTS user_backup_codes_unused ON user_backup_codes(user_id, used) WHERE used = FALSE;

