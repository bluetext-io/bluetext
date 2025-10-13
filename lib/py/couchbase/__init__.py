"""
Couchbase client library for BlueText.

This package provides a clean interface for interacting with Couchbase.
"""

from .client import CouchbaseClient, CouchbaseConf, Keyspace

__all__ = [
    "CouchbaseClient",
    "CouchbaseConf",
    "Keyspace",
]
