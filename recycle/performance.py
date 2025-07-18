"""
Performance optimizations for Universal Recycle.

This module provides remote caching, distributed builds, parallelization,
and performance monitoring for enterprise-scale deployments.
"""

import os
import json
import time
import hashlib
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

logger = logging.getLogger(__name__)


class DistributedBuildManager:
    """Manages distributed builds across multiple nodes."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.nodes = config.get("nodes", [])
        self.max_workers = config.get("max_workers", 4)
        self.build_queue = []
        self.active_builds = {}

    def add_build_node(
        self, node_id: str, host: str, port: int, capabilities: List[str]
    ) -> bool:
        """Add a build node to the distributed system."""
        node = {
            "id": node_id,
            "host": host,
            "port": port,
            "capabilities": capabilities,
            "status": "available",
            "current_build": None,
            "load": 0.0,
        }

        # Check if node already exists
        for existing_node in self.nodes:
            if existing_node["id"] == node_id:
                logger.warning(f"Node {node_id} already exists")
                return False

        self.nodes.append(node)
        logger.info(f"Added build node {node_id} at {host}:{port}")
        return True

    def distribute_build(
        self, targets: List[str], profile_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Distribute build targets across available nodes."""
        if not self.nodes:
            return {"error": "No build nodes available"}

        # Calculate target distribution
        available_nodes = [n for n in self.nodes if n["status"] == "available"]
        if not available_nodes:
            return {"error": "No available build nodes"}

        # Simple round-robin distribution
        distribution = {}
        for i, target in enumerate(targets):
            node = available_nodes[i % len(available_nodes)]
            if node["id"] not in distribution:
                distribution[node["id"]] = []
            distribution[node["id"]].append(target)

        # Execute builds in parallel
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_node = {}

            for node_id, node_targets in distribution.items():
                future = executor.submit(
                    self._execute_node_build, node_id, node_targets, profile_settings
                )
                future_to_node[future] = node_id

            for future in as_completed(future_to_node):
                node_id = future_to_node[future]
                try:
                    result = future.result()
                    results[node_id] = result
                except Exception as e:
                    results[node_id] = {"error": str(e)}

        return {
            "distribution": distribution,
            "results": results,
            "total_targets": len(targets),
            "nodes_used": len(distribution),
        }

    def _execute_node_build(
        self, node_id: str, targets: List[str], profile_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute build on a specific node."""
        node = next((n for n in self.nodes if n["id"] == node_id), None)
        if not node:
            return {"error": f"Node {node_id} not found"}

        # Simulate distributed build execution
        start_time = time.time()
        node["status"] = "building"
        node["current_build"] = targets

        # Simulate build time
        time.sleep(2)  # Simulated build time

        build_results = {}
        for target in targets:
            build_results[target] = {
                "status": "success",
                "duration": "00:00:30",
                "node": node_id,
            }

        node["status"] = "available"
        node["current_build"] = None
        node["load"] = 0.0

        return {
            "node_id": node_id,
            "targets": targets,
            "results": build_results,
            "duration": time.time() - start_time,
        }

    def get_node_status(self) -> List[Dict[str, Any]]:
        """Get status of all build nodes."""
        return [
            {
                "id": node["id"],
                "host": node["host"],
                "status": node["status"],
                "load": node["load"],
                "current_build": node["current_build"],
            }
            for node in self.nodes
        ]


class EnhancedCacheManager:
    """Enhanced cache manager with remote caching and optimization."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.local_cache_dir = Path(
            config.get("local_cache_dir", ".cache/universal_recycle")
        )
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        self.remote_backends = config.get("remote_backends", [])
        self.cache_stats = {"hits": 0, "misses": 0, "uploads": 0, "downloads": 0}

    def get_cache_key(self, target: str, profile_settings: Dict[str, Any]) -> str:
        """Generate a cache key for a target and profile combination."""
        # Create a hash of the target and profile settings
        content = f"{target}:{json.dumps(profile_settings, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get build artifacts from cache."""
        # Try local cache first
        local_path = self.local_cache_dir / f"{cache_key}.json"
        if local_path.exists():
            try:
                with open(local_path, "r") as f:
                    result = json.load(f)
                self.cache_stats["hits"] += 1
                logger.info(f"Cache hit for key {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Failed to load from local cache: {e}")

        # Try remote caches
        for backend in self.remote_backends:
            try:
                result = self._get_from_remote_cache(backend, cache_key)
                if result:
                    # Store in local cache for future use
                    self._store_in_local_cache(cache_key, result)
                    self.cache_stats["hits"] += 1
                    self.cache_stats["downloads"] += 1
                    logger.info(
                        f"Remote cache hit for key {cache_key} from {backend['type']}"
                    )
                    return result
            except Exception as e:
                logger.warning(
                    f"Failed to get from remote cache {backend['type']}: {e}"
                )

        self.cache_stats["misses"] += 1
        logger.info(f"Cache miss for key {cache_key}")
        return None

    def store_in_cache(self, cache_key: str, build_result: Dict[str, Any]) -> bool:
        """Store build artifacts in cache."""
        # Store in local cache
        success = self._store_in_local_cache(cache_key, build_result)

        # Store in remote caches
        for backend in self.remote_backends:
            try:
                self._store_in_remote_cache(backend, cache_key, build_result)
                self.cache_stats["uploads"] += 1
                logger.info(f"Stored in remote cache {backend['type']}")
            except Exception as e:
                logger.warning(
                    f"Failed to store in remote cache {backend['type']}: {e}"
                )

        return success

    def _store_in_local_cache(
        self, cache_key: str, build_result: Dict[str, Any]
    ) -> bool:
        """Store build result in local cache."""
        try:
            cache_file = self.local_cache_dir / f"{cache_key}.json"
            with open(cache_file, "w") as f:
                json.dump(build_result, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to store in local cache: {e}")
            return False

    def _get_from_remote_cache(
        self, backend: Dict[str, Any], cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get build result from remote cache."""
        backend_type = backend["type"]

        if backend_type == "redis":
            return self._get_from_redis_cache(backend, cache_key)
        elif backend_type == "s3":
            return self._get_from_s3_cache(backend, cache_key)
        elif backend_type == "gcs":
            return self._get_from_gcs_cache(backend, cache_key)
        else:
            logger.warning(f"Unknown remote cache backend: {backend_type}")
            return None

    def _store_in_remote_cache(
        self, backend: Dict[str, Any], cache_key: str, build_result: Dict[str, Any]
    ):
        """Store build result in remote cache."""
        backend_type = backend["type"]

        if backend_type == "redis":
            self._store_in_redis_cache(backend, cache_key, build_result)
        elif backend_type == "s3":
            self._store_in_s3_cache(backend, cache_key, build_result)
        elif backend_type == "gcs":
            self._store_in_gcs_cache(backend, cache_key, build_result)
        else:
            logger.warning(f"Unknown remote cache backend: {backend_type}")

    def _get_from_redis_cache(
        self, backend: Dict[str, Any], cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get from Redis cache (simulated)."""
        # Simulate Redis cache access
        return None

    def _store_in_redis_cache(
        self, backend: Dict[str, Any], cache_key: str, build_result: Dict[str, Any]
    ):
        """Store in Redis cache (simulated)."""
        # Simulate Redis cache storage
        pass

    def _get_from_s3_cache(
        self, backend: Dict[str, Any], cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get from S3 cache (simulated)."""
        # Simulate S3 cache access
        return None

    def _store_in_s3_cache(
        self, backend: Dict[str, Any], cache_key: str, build_result: Dict[str, Any]
    ):
        """Store in S3 cache (simulated)."""
        # Simulate S3 cache storage
        pass

    def _get_from_gcs_cache(
        self, backend: Dict[str, Any], cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get from Google Cloud Storage cache (simulated)."""
        # Simulate GCS cache access
        return None

    def _store_in_gcs_cache(
        self, backend: Dict[str, Any], cache_key: str, build_result: Dict[str, Any]
    ):
        """Store in Google Cloud Storage cache (simulated)."""
        # Simulate GCS cache storage
        pass

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "stats": self.cache_stats,
            "hit_rate": self.cache_stats["hits"]
            / max(1, self.cache_stats["hits"] + self.cache_stats["misses"]),
            "local_cache_size": self._get_local_cache_size(),
            "remote_backends": len(self.remote_backends),
        }

    def _get_local_cache_size(self) -> int:
        """Get local cache size in bytes."""
        total_size = 0
        for file_path in self.local_cache_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        self.metrics = {
            "build_times": {},
            "cache_performance": {},
            "resource_usage": {},
            "errors": [],
        }
        self.start_time = time.time()

    def record_build_time(self, target: str, duration: float, profile: str):
        """Record build time for a target."""
        if target not in self.metrics["build_times"]:
            self.metrics["build_times"][target] = []

        self.metrics["build_times"][target].append(
            {"duration": duration, "profile": profile, "timestamp": time.time()}
        )

    def record_cache_performance(
        self, cache_type: str, operation: str, duration: float
    ):
        """Record cache performance metrics."""
        if cache_type not in self.metrics["cache_performance"]:
            self.metrics["cache_performance"][cache_type] = {}

        if operation not in self.metrics["cache_performance"][cache_type]:
            self.metrics["cache_performance"][cache_type][operation] = []

        self.metrics["cache_performance"][cache_type][operation].append(
            {"duration": duration, "timestamp": time.time()}
        )

    def record_error(
        self, error_type: str, message: str, context: Dict[str, Any] = None
    ):
        """Record an error for monitoring."""
        self.metrics["errors"].append(
            {
                "type": error_type,
                "message": message,
                "context": context or {},
                "timestamp": time.time(),
            }
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report."""
        report = {
            "uptime": time.time() - self.start_time,
            "total_builds": sum(
                len(times) for times in self.metrics["build_times"].values()
            ),
            "average_build_time": self._calculate_average_build_time(),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "error_count": len(self.metrics["errors"]),
            "recent_errors": self.metrics["errors"][-10:],  # Last 10 errors
        }

        return report

    def _calculate_average_build_time(self) -> float:
        """Calculate average build time across all targets."""
        all_times = []
        for target_times in self.metrics["build_times"].values():
            all_times.extend([t["duration"] for t in target_times])

        return sum(all_times) / len(all_times) if all_times else 0.0

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_operations = 0
        total_hits = 0

        for cache_type in self.metrics["cache_performance"].values():
            for operation_times in cache_type.values():
                total_operations += len(operation_times)
                # Assume "get" operations with duration < 0.1s are hits
                total_hits += sum(1 for t in operation_times if t["duration"] < 0.1)

        return total_hits / max(1, total_operations)
