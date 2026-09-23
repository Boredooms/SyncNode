"""
SyncNode — Resource Lock Manager.

Prevents conflicting agents from simultaneously controlling a shared resource
(the desktop, an Office application, a specific file, a workspace).

Locks are:
  - leased      (acquired for a bounded time)
  - renewable   (the owner can extend)
  - expirable   (a stale lease is reclaimable)
  - owner-attributed (each lease records who holds it)
  - audited     (acquire/release are logged)

This is an in-process async lock manager (Phase-1 single-process backend). It is
NOT a distributed lock; that is out of scope until the backend runs multi-process.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Lease:
    resource: str
    owner: str
    lease_id: str
    acquired_at: float
    expires_at: float

    def expired(self, now: Optional[float] = None) -> bool:
        return (now or time.monotonic()) >= self.expires_at


@dataclass
class _ResourceState:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    lease: Optional[Lease] = None


class ResourceLockManager:
    """Async, owner-attributed, expirable resource locks."""

    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self._default_ttl = default_ttl_seconds
        self._resources: dict[str, _ResourceState] = {}
        self._guard = asyncio.Lock()

    def _state(self, resource: str) -> _ResourceState:
        st = self._resources.get(resource)
        if st is None:
            st = _ResourceState()
            self._resources[resource] = st
        return st

    async def acquire(
        self,
        resource: str,
        owner: str,
        *,
        ttl_seconds: Optional[float] = None,
        wait_timeout: float = 30.0,
    ) -> Lease:
        """Acquire an exclusive lease on a resource.

        Reclaims an expired lease automatically. Raises LockTimeoutError if the
        resource stays held by a live lease past ``wait_timeout``.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        deadline = time.monotonic() + wait_timeout

        async with self._guard:
            st = self._state(resource)

        while True:
            # Reclaim expired lease.
            if st.lease is not None and st.lease.expired():
                logger.warning(
                    "Reclaiming expired lease on %s (was owner=%s)",
                    resource, st.lease.owner,
                )
                if st.lock.locked():
                    try:
                        st.lock.release()
                    except RuntimeError:
                        pass
                st.lease = None

            try:
                remaining = max(0.0, deadline - time.monotonic())
                await asyncio.wait_for(st.lock.acquire(), timeout=remaining)
            except asyncio.TimeoutError:
                from syncnode_backend.errors.exceptions import LockTimeoutError
                held_by = st.lease.owner if st.lease else "unknown"
                raise LockTimeoutError(
                    f"Could not acquire lock on {resource!r} within {wait_timeout}s "
                    f"(held by {held_by})."
                )

            now = time.monotonic()
            lease = Lease(
                resource=resource,
                owner=owner,
                lease_id=uuid.uuid4().hex,
                acquired_at=now,
                expires_at=now + ttl,
            )
            st.lease = lease
            logger.info("Lock acquired — resource=%s owner=%s lease=%s", resource, owner, lease.lease_id[:8])
            return lease

    def renew(self, lease: Lease, *, ttl_seconds: Optional[float] = None) -> Lease:
        st = self._resources.get(lease.resource)
        if not st or st.lease is None or st.lease.lease_id != lease.lease_id:
            from syncnode_backend.errors.exceptions import LockTimeoutError
            raise LockTimeoutError(f"Lease {lease.lease_id[:8]} for {lease.resource!r} is no longer valid.")
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        st.lease.expires_at = time.monotonic() + ttl
        return st.lease

    def release(self, lease: Lease) -> None:
        st = self._resources.get(lease.resource)
        if not st:
            return
        if st.lease is not None and st.lease.lease_id != lease.lease_id:
            logger.warning(
                "Release ignored — lease mismatch on %s (holder=%s, caller=%s)",
                lease.resource, st.lease.lease_id[:8], lease.lease_id[:8],
            )
            return
        st.lease = None
        if st.lock.locked():
            try:
                st.lock.release()
            except RuntimeError:
                pass
        logger.info("Lock released — resource=%s owner=%s", lease.resource, lease.owner)

    def status(self) -> dict[str, Optional[dict]]:
        out: dict[str, Optional[dict]] = {}
        for res, st in self._resources.items():
            if st.lease is None:
                out[res] = None
            else:
                out[res] = {
                    "owner": st.lease.owner,
                    "lease_id": st.lease.lease_id,
                    "expires_in": round(st.lease.expires_at - time.monotonic(), 1),
                }
        return out


class _LeaseGroup:
    """Async context manager that acquires/releases a set of leases together."""

    def __init__(self, manager: ResourceLockManager, resources: list[str], owner: str,
                 ttl_seconds: Optional[float], wait_timeout: float) -> None:
        self._m = manager
        self._resources = sorted(set(resources))  # sorted => deterministic order, avoids deadlock
        self._owner = owner
        self._ttl = ttl_seconds
        self._wait = wait_timeout
        self._leases: list[Lease] = []

    async def __aenter__(self) -> list[Lease]:
        try:
            for r in self._resources:
                self._leases.append(
                    await self._m.acquire(r, self._owner, ttl_seconds=self._ttl, wait_timeout=self._wait)
                )
        except Exception:
            for lease in reversed(self._leases):
                self._m.release(lease)
            raise
        return self._leases

    async def __aexit__(self, *exc) -> None:
        for lease in reversed(self._leases):
            self._m.release(lease)


def lease_group(manager: ResourceLockManager, resources: list[str], owner: str,
                *, ttl_seconds: Optional[float] = None, wait_timeout: float = 30.0) -> _LeaseGroup:
    """Acquire multiple locks atomically (sorted order prevents deadlock)."""
    return _LeaseGroup(manager, resources, owner, ttl_seconds, wait_timeout)


# Module-level singleton for the single-process backend.
lock_manager = ResourceLockManager()
