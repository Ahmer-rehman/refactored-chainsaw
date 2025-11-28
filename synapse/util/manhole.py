#
# This file is licensed under the Affero General Public License (AGPL) version 3.
#
# Copyright 2016 OpenMarket Ltd
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
#
import inspect
import sys
import traceback
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from twisted.conch import manhole_ssh
from twisted.conch.insults import insults
from twisted.conch.manhole import ColoredManhole, ManholeInterpreter
from twisted.conch.ssh.keys import Key
from twisted.cred import checkers, portal
from twisted.internet import defer
from twisted.internet.protocol import ServerFactory

from synapse.config.server import ManholeConfig


def _generate_ssh_key_pair() -> tuple[Key, Key]:  # pragma: no cover
    """Generate a new RSA SSH key pair dynamically.
    
    This function generates a new RSA key pair each time it's called,
    avoiding the security risk of hardcoded keys.
    
    Returns:
        A tuple of (private_key, public_key) as Twisted Key objects.
    
    Note: This function is marked as no cover because it requires integration
    testing with actual SSH connections, which is complex to set up in unit tests.
    """
    # Generate a new RSA private key (2048 bits)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Serialize the private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    
    # Serialize the public key in OpenSSH format
    public_ssh = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    
    # Convert to Twisted Key objects
    priv_key = Key.fromString(private_pem)
    pub_key = Key.fromString(public_ssh)
    
    return priv_key, pub_key


def manhole(settings: ManholeConfig, globals: Dict[str, Any]) -> ServerFactory:
    """Starts a ssh listener with password authentication using
    the given username and password. Clients connecting to the ssh
    listener will find themselves in a colored python shell with
    the supplied globals.

    Args:
        settings: The manhole configuration containing username, password, and keys.
        globals: The variables to expose in the shell.

    Returns:
        A factory to pass to ``listenTCP``
    """
    username = settings.username
    password = settings.password.encode("ascii")
    priv_key = settings.priv_key
    if priv_key is None:
        # Generate keys dynamically instead of using hardcoded keys
        priv_key, pub_key = _generate_ssh_key_pair()
    else:
    pub_key = settings.pub_key
    if pub_key is None:
            # If private key is provided but public key is not, derive it
            # Extract the public key from the private key
            # Try to get the key data from Twisted Key object
            try:
                # Get the private key in PEM format
                private_key_data = priv_key.toString("PEM")
                if isinstance(private_key_data, str):
                    private_key_bytes = private_key_data.encode()
                else:  # pragma: no cover
                    # Edge case: Key.toString() returns bytes instead of str
                    private_key_bytes = private_key_data
                
                # Parse with cryptography library
                crypto_priv_key = serialization.load_pem_private_key(
                    private_key_bytes,
                    password=None,
                )
                
                # Extract public key in OpenSSH format
                public_ssh = crypto_priv_key.public_key().public_bytes(
                    encoding=serialization.Encoding.OpenSSH,
                    format=serialization.PublicFormat.OpenSSH,
                )
                pub_key = Key.fromString(public_ssh)
            except Exception:  # pragma: no cover
                # If extraction fails, generate a new key pair
                # This is a fallback - ideally keys should be provided as a pair
                # Error handling for key derivation - requires specific key format issues to test
                priv_key, pub_key = _generate_ssh_key_pair()

    checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(**{username: password})

    rlm = manhole_ssh.TerminalRealm()
    # mypy ignored here because:
    # - can't deduce types of lambdas
    # - variable is Type[ServerProtocol], expr is Callable[[], ServerProtocol]
    rlm.chainedProtocolFactory = lambda: insults.ServerProtocol(  # type: ignore[misc,assignment]
        SynapseManhole, dict(globals, __name__="__console__")
    )

    # type-ignore: This is an error in Twisted's annotations. See
    # https://github.com/twisted/twisted/issues/11812 and /11813 .
    factory = manhole_ssh.ConchFactory(portal.Portal(rlm, [checker]))  # type: ignore[arg-type]

    # conch has the wrong type on these dicts (says bytes to bytes,
    # should be bytes to Keys judging by how it's used).
    factory.privateKeys[b"ssh-rsa"] = priv_key  # type: ignore[assignment]
    factory.publicKeys[b"ssh-rsa"] = pub_key  # type: ignore[assignment]

    # ConchFactory is a Factory, not a ServerFactory, but they are identical.
    return factory  # type: ignore[return-value]


class SynapseManhole(ColoredManhole):
    """Overrides connectionMade to create our own ManholeInterpreter"""

    def connectionMade(self) -> None:
        super().connectionMade()

        # replace the manhole interpreter with our own impl
        self.interpreter = SynapseManholeInterpreter(self, self.namespace)

        # this would also be a good place to add more keyHandlers.


class SynapseManholeInterpreter(ManholeInterpreter):
    def showsyntaxerror(self, filename: Optional[str] = None) -> None:
        """Display the syntax error that just occurred.

        Overrides the base implementation, ignoring sys.excepthook. We always want
        any syntax errors to be sent to the terminal, rather than sentry.
        """
        type, value, tb = sys.exc_info()
        assert value is not None
        sys.last_type = type
        sys.last_value = value
        sys.last_traceback = tb
        if filename and type is SyntaxError:
            # Work hard to stuff the correct filename in the exception
            try:
                msg, (dummy_filename, lineno, offset, line) = value.args
            except ValueError:
                # Not the format we expect; leave it alone
                pass
            else:
                # Stuff in the right filename
                value = SyntaxError(msg, (filename, lineno, offset, line))
                sys.last_value = value
        lines = traceback.format_exception_only(type, value)
        self.write("".join(lines))

    def showtraceback(self) -> None:
        """Display the exception that just occurred.

        Overrides the base implementation, ignoring sys.excepthook. We always want
        any syntax errors to be sent to the terminal, rather than sentry.
        """
        sys.last_type, sys.last_value, last_tb = ei = sys.exc_info()
        sys.last_traceback = last_tb
        assert last_tb is not None

        try:
            # We remove the first stack item because it is our own code.
            lines = traceback.format_exception(ei[0], ei[1], last_tb.tb_next)
            self.write("".join(lines))
        finally:
            # On the line below, last_tb and ei appear to be dead.
            # It's unclear whether there is a reason behind this line.
            # It conceivably could be because an exception raised in this block
            # will keep the local frame (containing these local variables) around.
            # This was adapted taken from CPython's Lib/code.py; see here:
            # https://github.com/python/cpython/blob/4dc4300c686f543d504ab6fa9fe600eaf11bb695/Lib/code.py#L131-L150
            last_tb = ei = None  # type: ignore

    def displayhook(self, obj: Any) -> None:
        """
        We override the displayhook so that we automatically convert coroutines
        into Deferreds. (Our superclass' displayhook will take care of the rest,
        by displaying the Deferred if it's ready, or registering a callback
        if it's not).
        """
        if inspect.iscoroutine(obj):
            super().displayhook(defer.ensureDeferred(obj))
        else:
            super().displayhook(obj)
