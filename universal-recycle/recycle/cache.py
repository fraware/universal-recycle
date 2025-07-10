"""
Remote caching system for Universal Recycle.

This module provides caching for build artifacts, dependencies, and binding
generation results using Redis and cloud storage backends.
"""

import os
import json
import hashlib
import pickle
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import tempfile
import shutil

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from google.cloud import storage

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""

    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime]
    size_bytes: int
    metadata: Dict[str, Any]

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            data=data["data"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data["expires_at"]
                else None
            ),
            size_bytes=data["size_bytes"],
            metadata=data["metadata"],
        )


class CacheBackend:
    """Base class for cache backends."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__

    def log(self, message: str, level: str = "info"):
        """Log a message with the backend name prefix."""
        log_func = getattr(logger, level)
        log_func(f"[{self.name}] {message}")

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry by key."""
        raise NotImplementedError

    def set(self, entry: CacheEntry) -> bool:
        """Set a cache entry."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        raise NotImplementedError

    def clear(self) -> bool:
        """Clear all cache entries."""
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        raise NotImplementedError


class RedisCacheBackend(CacheBackend):
    """Redis-based cache backend."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for Redis cache backend")

        self.redis_client = redis.Redis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379),
            db=config.get("db", 0),
            password=config.get("password"),
            decode_responses=False,  # We need bytes for pickle
        )
        self.prefix = config.get("prefix", "universal_recycle:")
        self.default_ttl = config.get("default_ttl", 3600)  # 1 hour

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry from Redis."""
        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)
            if data is None:
                return None

            entry_dict = pickle.loads(data)
            entry = CacheEntry.from_dict(entry_dict)

            if entry.is_expired():
                self.delete(key)
                return None

            self.log(f"Cache hit for key: {key}")
            return entry

        except Exception as e:
            self.log(f"Error getting cache entry {key}: {e}", "error")
            return None

    def set(self, entry: CacheEntry) -> bool:
        """Set a cache entry in Redis."""
        try:
            redis_key = self._make_key(entry.key)
            data = pickle.dumps(entry.to_dict())

            # Calculate TTL
            ttl = self.default_ttl
            if entry.expires_at:
                ttl = int((entry.expires_at - datetime.now()).total_seconds())
                if ttl <= 0:
                    return False

            self.redis_client.setex(redis_key, ttl, data)
            self.log(f"Cache set for key: {entry.key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            self.log(f"Error setting cache entry {entry.key}: {e}", "error")
            return False

    def delete(self, key: str) -> bool:
        """Delete a cache entry from Redis."""
        try:
            redis_key = self._make_key(key)
            result = self.redis_client.delete(redis_key)
            self.log(f"Cache delete for key: {key}")
            return result > 0
        except Exception as e:
            self.log(f"Error deleting cache entry {key}: {e}", "error")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            redis_key = self._make_key(key)
            return self.redis_client.exists(redis_key) > 0
        except Exception as e:
            self.log(f"Error checking cache entry {key}: {e}", "error")
            return False

    def clear(self) -> bool:
        """Clear all cache entries with the prefix."""
        try:
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            self.log(f"Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            self.log(f"Error clearing cache: {e}", "error")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            info = self.redis_client.info()
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)

            return {
                "backend": "redis",
                "total_keys": len(keys),
                "memory_usage": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            self.log(f"Error getting cache stats: {e}", "error")
            return {"backend": "redis", "error": str(e)}


class S3CacheBackend(CacheBackend):
    """AWS S3-based cache backend."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 package is required for S3 cache backend")

        self.bucket_name = config["bucket_name"]
        self.prefix = config.get("prefix", "universal_recycle/")
        self.default_ttl = config.get("default_ttl", 3600)

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key"),
            region_name=config.get("region_name", "us-east-1"),
        )

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry from S3."""
        try:
            s3_key = self._make_key(key)

            # Check if object exists and get metadata
            try:
                response = self.s3_client.head_object(
                    Bucket=self.bucket_name, Key=s3_key
                )
                expires_at = response.get("Metadata", {}).get("expires_at")

                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        self.delete(key)
                        return None

            except self.s3_client.exceptions.NoSuchKey:
                return None

            # Download the object
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            data = response["Body"].read()
            entry_dict = pickle.loads(data)
            entry = CacheEntry.from_dict(entry_dict)

            self.log(f"Cache hit for key: {key}")
            return entry

        except Exception as e:
            self.log(f"Error getting cache entry {key}: {e}", "error")
            return None

    def set(self, entry: CacheEntry) -> bool:
        """Set a cache entry in S3."""
        try:
            s3_key = self._make_key(entry.key)
            data = pickle.dumps(entry.to_dict())

            # Prepare metadata
            metadata = {
                "created_at": entry.created_at.isoformat(),
                "size_bytes": str(entry.size_bytes),
            }
            if entry.expires_at:
                metadata["expires_at"] = entry.expires_at.isoformat()

            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=s3_key, Body=data, Metadata=metadata
            )

            self.log(f"Cache set for key: {entry.key}")
            return True

        except Exception as e:
            self.log(f"Error setting cache entry {entry.key}: {e}", "error")
            return False

    def delete(self, key: str) -> bool:
        """Delete a cache entry from S3."""
        try:
            s3_key = self._make_key(key)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            self.log(f"Cache delete for key: {key}")
            return True
        except Exception as e:
            self.log(f"Error deleting cache entry {key}: {e}", "error")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in S3."""
        try:
            s3_key = self._make_key(key)
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            self.log(f"Error checking cache entry {key}: {e}", "error")
            return False

    def clear(self) -> bool:
        """Clear all cache entries with the prefix."""
        try:
            # List all objects with the prefix
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            objects_to_delete = []
            for page in pages:
                if "Contents" in page:
                    objects_to_delete.extend(
                        [{"Key": obj["Key"]} for obj in page["Contents"]]
                    )

            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name, Delete={"Objects": objects_to_delete}
                )

            self.log(f"Cleared {len(objects_to_delete)} cache entries")
            return True

        except Exception as e:
            self.log(f"Error clearing cache: {e}", "error")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get S3 cache statistics."""
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            total_size = 0
            total_objects = 0

            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        total_size += obj["Size"]
                        total_objects += 1

            return {
                "backend": "s3",
                "bucket": self.bucket_name,
                "total_objects": total_objects,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }
        except Exception as e:
            self.log(f"Error getting cache stats: {e}", "error")
            return {"backend": "s3", "error": str(e)}


class LocalCacheBackend(CacheBackend):
    """Local file-based cache backend."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cache_dir = Path(config.get("cache_dir", ".cache/universal_recycle"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = config.get("default_ttl", 3600)

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Create a hash of the key to avoid filesystem issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry from local storage."""
        try:
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                return None

            with open(cache_path, "rb") as f:
                entry_dict = pickle.load(f)

            entry = CacheEntry.from_dict(entry_dict)

            if entry.is_expired():
                self.delete(key)
                return None

            self.log(f"Cache hit for key: {key}")
            return entry

        except Exception as e:
            self.log(f"Error getting cache entry {key}: {e}", "error")
            return None

    def set(self, entry: CacheEntry) -> bool:
        """Set a cache entry in local storage."""
        try:
            cache_path = self._get_cache_path(entry.key)

            with open(cache_path, "wb") as f:
                pickle.dump(entry.to_dict(), f)

            self.log(f"Cache set for key: {entry.key}")
            return True

        except Exception as e:
            self.log(f"Error setting cache entry {entry.key}: {e}", "error")
            return False

    def delete(self, key: str) -> bool:
        """Delete a cache entry from local storage."""
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
                self.log(f"Cache delete for key: {key}")
                return True
            return False
        except Exception as e:
            self.log(f"Error deleting cache entry {key}: {e}", "error")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in local storage."""
        try:
            cache_path = self._get_cache_path(key)
            return cache_path.exists()
        except Exception as e:
            self.log(f"Error checking cache entry {key}: {e}", "error")
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            self.log("Cleared all cache entries")
            return True
        except Exception as e:
            self.log(f"Error clearing cache: {e}", "error")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get local cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                "backend": "local",
                "cache_dir": str(self.cache_dir),
                "total_files": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }
        except Exception as e:
            self.log(f"Error getting cache stats: {e}", "error")
            return {"backend": "local", "error": str(e)}


class CacheManager:
    """Manages multiple cache backends with fallback support."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backends: List[CacheBackend] = []
        self._setup_backends()

    def _setup_backends(self):
        """Set up cache backends based on configuration."""
        backends_config = self.config.get("backends", [])

        for backend_config in backends_config:
            backend_type = backend_config["type"]

            try:
                if backend_type == "redis":
                    backend = RedisCacheBackend(backend_config)
                elif backend_type == "s3":
                    backend = S3CacheBackend(backend_config)
                elif backend_type == "local":
                    backend = LocalCacheBackend(backend_config)
                else:
                    logger.warning(f"Unknown cache backend type: {backend_type}")
                    continue

                self.backends.append(backend)
                logger.info(f"Initialized {backend_type} cache backend")

            except Exception as e:
                logger.error(f"Failed to initialize {backend_type} cache backend: {e}")

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a cache entry from any available backend."""
        for backend in self.backends:
            try:
                entry = backend.get(key)
                if entry is not None:
                    return entry
            except Exception as e:
                logger.warning(f"Error getting from {backend.name}: {e}")

        return None

    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set a cache entry in all backends."""
        if metadata is None:
            metadata = {}

        # Calculate expiration
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        # Create cache entry
        entry = CacheEntry(
            key=key,
            data=data,
            created_at=datetime.now(),
            expires_at=expires_at,
            size_bytes=len(pickle.dumps(data)),
            metadata=metadata,
        )

        # Set in all backends
        success = False
        for backend in self.backends:
            try:
                if backend.set(entry):
                    success = True
            except Exception as e:
                logger.warning(f"Error setting in {backend.name}: {e}")

        return success

    def delete(self, key: str) -> bool:
        """Delete a cache entry from all backends."""
        success = False
        for backend in self.backends:
            try:
                if backend.delete(key):
                    success = True
            except Exception as e:
                logger.warning(f"Error deleting from {backend.name}: {e}")

        return success

    def exists(self, key: str) -> bool:
        """Check if a key exists in any backend."""
        for backend in self.backends:
            try:
                if backend.exists(key):
                    return True
            except Exception as e:
                logger.warning(f"Error checking in {backend.name}: {e}")

        return False

    def clear(self) -> bool:
        """Clear all cache entries from all backends."""
        success = True
        for backend in self.backends:
            try:
                if not backend.clear():
                    success = False
            except Exception as e:
                logger.warning(f"Error clearing {backend.name}: {e}")
                success = False

        return success

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all backends."""
        stats = {"backends": [], "total_backends": len(self.backends)}

        for backend in self.backends:
            try:
                backend_stats = backend.get_stats()
                stats["backends"].append(backend_stats)
            except Exception as e:
                logger.warning(f"Error getting stats from {backend.name}: {e}")

        return stats


# Cache key generators
def generate_build_cache_key(repo_name: str, commit_hash: str, build_type: str) -> str:
    """Generate a cache key for build artifacts."""
    return f"build:{repo_name}:{commit_hash}:{build_type}"


def generate_binding_cache_key(repo_name: str, generator: str, commit_hash: str) -> str:
    """Generate a cache key for binding generation results."""
    return f"binding:{repo_name}:{generator}:{commit_hash}"


def generate_dependency_cache_key(dependency_name: str, version: str) -> str:
    """Generate a cache key for dependencies."""
    return f"dep:{dependency_name}:{version}"


def generate_file_hash_cache_key(file_path: str) -> str:
    """Generate a cache key for file hashes."""
    return f"hash:{file_path}"


# Utility functions
def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def cache_directory_contents(
    cache_manager: CacheManager, directory: str, cache_key: str
) -> bool:
    """Cache the contents of a directory as a tar.gz archive."""
    try:
        import tarfile

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
            with tarfile.open(temp_file.name, "w:gz") as tar:
                tar.add(directory, arcname=os.path.basename(directory))

            # Read the archive and cache it
            with open(temp_file.name, "rb") as f:
                archive_data = f.read()

            # Clean up temp file
            os.unlink(temp_file.name)

            # Cache the archive
            return cache_manager.set(
                cache_key,
                archive_data,
                ttl=86400,  # 24 hours
                metadata={"type": "directory_archive", "original_path": directory},
            )

    except Exception as e:
        logger.error(f"Error caching directory {directory}: {e}")
        return False


def restore_directory_contents(
    cache_manager: CacheManager, cache_key: str, target_directory: str
) -> bool:
    """Restore directory contents from cache."""
    try:
        import tarfile

        entry = cache_manager.get(cache_key)
        if entry is None:
            return False

        # Create target directory
        os.makedirs(target_directory, exist_ok=True)

        # Write archive to temp file
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_file:
            temp_file.write(entry.data)
            temp_file.flush()

            # Extract archive
            with tarfile.open(temp_file.name, "r:gz") as tar:
                tar.extractall(path=os.path.dirname(target_directory))

            # Clean up temp file
            os.unlink(temp_file.name)

        return True

    except Exception as e:
        logger.error(f"Error restoring directory {target_directory}: {e}")
        return False
