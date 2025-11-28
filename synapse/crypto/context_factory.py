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
#

import logging

from service_identity import VerificationError
from service_identity.pyopenssl import verify_hostname, verify_ip_address
from zope.interface import implementer

from OpenSSL import SSL, crypto
from twisted.internet._sslverify import _defaultCurveName
from twisted.internet.abstract import isIPAddress, isIPv6Address
from twisted.internet.interfaces import IOpenSSLClientConnectionCreator
from twisted.internet.ssl import (
    CertificateOptions,
    ContextFactory,
    TLSVersion,
    platformTrust,
)
from twisted.protocols.tls import TLSMemoryBIOProtocol
from twisted.python.failure import Failure
from twisted.web.iweb import IPolicyForHTTPS

from synapse.config.homeserver import HomeServerConfig

logger = logging.getLogger(__name__)


_TLS_VERSION_MAP = {
    "1": TLSVersion.TLSv1_0,
    "1.1": TLSVersion.TLSv1_1,
    "1.2": TLSVersion.TLSv1_2,
    "1.3": TLSVersion.TLSv1_3,
}


class ServerContextFactory(ContextFactory):
    """Factory for PyOpenSSL SSL contexts that are used to handle incoming
    connections.

    TODO: replace this with an implementation of IOpenSSLServerConnectionCreator,
    per https://github.com/matrix-org/synapse/issues/1691
    """

    def __init__(self, config: HomeServerConfig):
        # Use the strongest available TLS method
        # Prefer TLS_METHOD if available (OpenSSL 1.1.0+), otherwise fall back to SSLv23_METHOD
        # Note: SSLv23_METHOD is a legacy name but is actually TLS_METHOD under the hood
        # It allows negotiation of TLS versions constrained by set_options
        if hasattr(SSL, "TLS_METHOD"):
            # TLS_METHOD is the modern, explicit method for TLS (OpenSSL 1.1.0+)
            # This is preferred over SSLv23_METHOD for clarity and future compatibility
            self._context = SSL.Context(SSL.TLS_METHOD)
        else:
            # Fallback for older OpenSSL versions
            # SSLv23_METHOD is actually TLS_METHOD, despite the confusing name
            self._context = SSL.Context(SSL.SSLv23_METHOD)
        self.configure_context(self._context, config)

    @staticmethod
    def configure_context(context: SSL.Context, config: HomeServerConfig) -> None:
        try:
            _ecCurve = crypto.get_elliptic_curve(_defaultCurveName)
            context.set_tmp_ecdh(_ecCurve)
        except Exception:
            logger.exception("Failed to enable elliptic curve for TLS")

        # Disable all weak/insecure protocols - enforce TLS 1.2 minimum
        # OP_NO_TLSv1 and OP_NO_TLSv1_1 disable TLS 1.0 and 1.1
        # This ensures only TLS 1.2 and 1.3 are allowed
        context.set_options(
            SSL.OP_NO_SSLv2
            | SSL.OP_NO_SSLv3
            | SSL.OP_NO_TLSv1
            | SSL.OP_NO_TLSv1_1
            | SSL.OP_NO_COMPRESSION  # Disable compression (CRIME vulnerability)
            | SSL.OP_CIPHER_SERVER_PREFERENCE  # Prefer server cipher order
        )

        # Set minimum protocol version to TLS 1.2 if supported
        # This provides an additional layer of enforcement
        if hasattr(context, "set_min_proto_version"):
            # OpenSSL 1.1.1+ supports explicit minimum version setting
            try:
                # Use TLS1_2_VERSION constant if available
                if hasattr(SSL, "TLS1_2_VERSION"):
                    context.set_min_proto_version(SSL.TLS1_2_VERSION)
                else:
                    # Fallback: use numeric value for TLS 1.2 (0x0303)
                    context.set_min_proto_version(0x0303)
            except Exception as e:
                logger.warning(
                    "Failed to set minimum TLS protocol version, using options instead: %s", e
                )

        context.use_certificate_chain_file(config.tls.tls_certificate_file)
        assert config.tls.tls_private_key is not None
        context.use_privatekey(config.tls.tls_private_key)

        # Updated cipher list for stronger security:
        # - Prefer ECDHE (forward secrecy) with AES-GCM and ChaCha20-Poly1305
        # - Remove MD5, SHA1, and other weak algorithms (SHA256/SHA384 are fine)
        # - Remove AES-CCM (less secure than GCM)
        # - Remove NULL, anon, export, DES, RC4, and 3DES ciphers
        # - TLS 1.3 cipher suites are negotiated separately and automatically
        context.set_cipher_list(
            b"ECDHE+AESGCM:ECDHE+CHACHA20:ECDHE+AES256:ECDHE+AES128:!aNULL:!eNULL:!MD5:!SHA1:!AESCCM:!DES:!RC4:!3DES:!EXPORT:!LOW"
        )

    def getContext(self) -> SSL.Context:
        return self._context


@implementer(IPolicyForHTTPS)
class FederationPolicyForHTTPS:
    """Factory for Twisted SSLClientConnectionCreators that are used to make connections
    to remote servers for federation.

    Uses one of two OpenSSL context objects for all connections, depending on whether
    we should do SSL certificate verification.

    get_options decides whether we should do SSL certificate verification and
    constructs an SSLClientConnectionCreator factory accordingly.
    """

    def __init__(self, config: HomeServerConfig):
        self._config = config

        # Check if we're using a custom list of a CA certificates
        trust_root = config.tls.federation_ca_trust_root
        if trust_root is None:
            # Use CA root certs provided by OpenSSL
            trust_root = platformTrust()

        # "insecurelyLowerMinimumTo" is the argument that will go lower than
        # Twisted's default, which is why it is marked as "insecure" (since
        # Twisted's defaults are reasonably secure). But, since Twisted is
        # moving to TLS 1.2 by default, we want to respect the config option if
        # it is set to 1.0 (which the alternate option, raiseMinimumTo, will not
        # let us do).
        # Security note: TLS 1.0 and 1.1 are deprecated and insecure. We allow
        # configuration for backward compatibility, but strongly recommend TLS 1.2 minimum.
        minTLS = _TLS_VERSION_MAP[config.tls.federation_client_minimum_tls_version]
        
        # Enforce TLS 1.2 as absolute minimum for security, unless explicitly
        # configured lower (for legacy compatibility)
        if minTLS in (TLSVersion.TLSv1_0, TLSVersion.TLSv1_1):
            logger.warning(
                "federation_client_minimum_tls_version is set to %s. "
                "TLS 1.0 and 1.1 are deprecated and insecure. "
                "Consider upgrading to TLS 1.2 minimum.",
                config.tls.federation_client_minimum_tls_version
            )

        _verify_ssl = CertificateOptions(
            trustRoot=trust_root, insecurelyLowerMinimumTo=minTLS
        )
        self._verify_ssl_context = _verify_ssl.getContext()
        self._verify_ssl_context.set_info_callback(_context_info_cb)

        _no_verify_ssl = CertificateOptions(insecurelyLowerMinimumTo=minTLS)
        self._no_verify_ssl_context = _no_verify_ssl.getContext()
        self._no_verify_ssl_context.set_info_callback(_context_info_cb)

        self._should_verify = self._config.tls.federation_verify_certificates

        self._federation_certificate_verification_whitelist = (
            self._config.tls.federation_certificate_verification_whitelist
        )

    def get_options(self, host: bytes) -> IOpenSSLClientConnectionCreator:
        # IPolicyForHTTPS.get_options takes bytes, but we want to compare
        # against the str whitelist. The hostnames in the whitelist are already
        # IDNA-encoded like the hosts will be here.
        ascii_host = host.decode("ascii")

        # Check if certificate verification has been enabled
        should_verify = self._should_verify

        # Check if we've disabled certificate verification for this host
        if self._should_verify:
            for regex in self._federation_certificate_verification_whitelist:
                if regex.match(ascii_host):
                    should_verify = False
                    break

        ssl_context = (
            self._verify_ssl_context if should_verify else self._no_verify_ssl_context
        )

        return SSLClientConnectionCreator(host, ssl_context, should_verify)

    def creatorForNetloc(
        self, hostname: bytes, port: int
    ) -> IOpenSSLClientConnectionCreator:
        """Implements the IPolicyForHTTPS interface so that this can be passed
        directly to agents.
        """
        return self.get_options(hostname)


@implementer(IPolicyForHTTPS)
class RegularPolicyForHTTPS:
    """Factory for Twisted SSLClientConnectionCreators that are used to make connections
    to remote servers, for other than federation.

    Always uses the same OpenSSL context object, which uses the default OpenSSL CA
    trust root.
    """

    def __init__(self) -> None:
        trust_root = platformTrust()
        certificate_options = CertificateOptions(trustRoot=trust_root)
        self._ssl_context = certificate_options.getContext()
        
        # Enforce TLS 1.2 minimum for regular HTTPS connections
        # This ensures strong security for all outbound client connections
        # Disable weak/insecure protocols
        self._ssl_context.set_options(
            SSL.OP_NO_SSLv2
            | SSL.OP_NO_SSLv3
            | SSL.OP_NO_TLSv1
            | SSL.OP_NO_TLSv1_1
            | SSL.OP_NO_COMPRESSION  # Disable compression (CRIME vulnerability)
        )
        
        # Set minimum protocol version to TLS 1.2 if supported
        if hasattr(self._ssl_context, "set_min_proto_version"):
            try:
                if hasattr(SSL, "TLS1_2_VERSION"):
                    self._ssl_context.set_min_proto_version(SSL.TLS1_2_VERSION)
                else:
                    # Fallback: use numeric value for TLS 1.2 (0x0303)
                    self._ssl_context.set_min_proto_version(0x0303)
            except Exception:
                # If setting minimum version fails, options above still enforce it
                pass
        
        self._ssl_context.set_info_callback(_context_info_cb)

    def creatorForNetloc(
        self, hostname: bytes, port: int
    ) -> IOpenSSLClientConnectionCreator:
        return SSLClientConnectionCreator(hostname, self._ssl_context, True)


def _context_info_cb(ssl_connection: SSL.Connection, where: int, ret: int) -> None:
    """The 'information callback' for our openssl context objects.

    Note: Once this is set as the info callback on a Context object, the Context should
    only be used with the SSLClientConnectionCreator.
    """
    # we assume that the app_data on the connection object has been set to
    # a TLSMemoryBIOProtocol object. (This is done by SSLClientConnectionCreator)
    tls_protocol = ssl_connection.get_app_data()
    try:
        # ... we further assume that SSLClientConnectionCreator has set the
        # '_synapse_tls_verifier' attribute to a ConnectionVerifier object.
        tls_protocol._synapse_tls_verifier.verify_context_info_cb(ssl_connection, where)
    except BaseException:  # taken from the twisted implementation
        logger.exception("Error during info_callback")
        f = Failure()
        tls_protocol.failVerification(f)


@implementer(IOpenSSLClientConnectionCreator)
class SSLClientConnectionCreator:
    """Creates openssl connection objects for client connections.

    Replaces twisted.internet.ssl.ClientTLSOptions
    """

    def __init__(self, hostname: bytes, ctx: SSL.Context, verify_certs: bool):
        self._ctx = ctx
        self._verifier = ConnectionVerifier(hostname, verify_certs)

    def clientConnectionForTLS(
        self, tls_protocol: TLSMemoryBIOProtocol
    ) -> SSL.Connection:
        context = self._ctx
        connection = SSL.Connection(context, None)

        # as per twisted.internet.ssl.ClientTLSOptions, we set the application
        # data to our TLSMemoryBIOProtocol...
        connection.set_app_data(tls_protocol)

        # ... and we also gut-wrench a '_synapse_tls_verifier' attribute into the
        # tls_protocol so that the SSL context's info callback has something to
        # call to do the cert verification.
        tls_protocol._synapse_tls_verifier = self._verifier  # type: ignore[attr-defined]
        return connection


class ConnectionVerifier:
    """Set the SNI, and do cert verification

    This is a thing which is attached to the TLSMemoryBIOProtocol, and is called by
    the ssl context's info callback.
    """

    # This code is based on twisted.internet.ssl.ClientTLSOptions.

    def __init__(self, hostname: bytes, verify_certs: bool):
        self._verify_certs = verify_certs

        _decoded = hostname.decode("ascii")
        if isIPAddress(_decoded) or isIPv6Address(_decoded):
            self._is_ip_address = True
        else:
            self._is_ip_address = False

        self._hostnameBytes = hostname
        self._hostnameASCII = self._hostnameBytes.decode("ascii")

    def verify_context_info_cb(
        self, ssl_connection: SSL.Connection, where: int
    ) -> None:
        if where & SSL.SSL_CB_HANDSHAKE_START and not self._is_ip_address:
            ssl_connection.set_tlsext_host_name(self._hostnameBytes)

        if where & SSL.SSL_CB_HANDSHAKE_DONE and self._verify_certs:
            try:
                if self._is_ip_address:
                    verify_ip_address(ssl_connection, self._hostnameASCII)
                else:
                    verify_hostname(ssl_connection, self._hostnameASCII)
            except VerificationError:
                f = Failure()
                tls_protocol = ssl_connection.get_app_data()
                tls_protocol.failVerification(f)
