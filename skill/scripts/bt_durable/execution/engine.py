"""DBOS lifecycle for the durable runtime: one engine per process, ports registered before launch.

Versioning: `enable_patching=True` pins the application version to DBOS's patching mode, so a code change does not
orphan PENDING workflows (DBOS recovers only workflows of the running application version). Changes to a workflow's
step sequence go behind `DBOS.patch("<name>")` (see README, "Upgrading workflows").
"""
from __future__ import annotations

import logging
import threading

from dbos import DBOS, DBOSConfig

from ..ports import Ports
from ..settings import EngineConfig

RUNS, AGENTS, VERIFY, INTEGRATE = "bt-runs", "bt-agents", "bt-verify", "bt-integrate"
APP_VERSION = "PATCHING_ENABLED"        # what DBOS pins when enable_patching is on; clients enqueue for it
LOG = logging.getLogger("bt_durable")

_lock = threading.Lock()
_ports: Ports | None = None
_config: EngineConfig | None = None
_launched = False


def ports() -> Ports:
    if _ports is None:
        raise RuntimeError("bt_durable engine is not started: call engine.start(config, ports) first")
    return _ports


def config() -> EngineConfig:
    if _config is None:
        raise RuntimeError("bt_durable engine is not started")
    return _config


def start(cfg: EngineConfig, wired: Ports) -> None:
    """Configure DBOS, launch it (which recovers this executor's PENDING workflows) and register the queues."""
    global _ports, _config, _launched
    from . import workflows  # noqa: F401  (registers the decorated functions before launch)

    with _lock:
        if _launched:
            raise RuntimeError("bt_durable engine already started in this process")
        cfg.state_dir.mkdir(parents=True, exist_ok=True)
        _ports, _config = wired, cfg
        dbos_config: DBOSConfig = {
            "name": cfg.name,
            "system_database_url": cfg.system_database_url,
            "executor_id": cfg.executor_id,
            "enable_patching": True,
            "max_executor_threads": cfg.max_executor_threads,
        }
        DBOS(config=dbos_config)
        DBOS.launch()
        DBOS.register_queue(RUNS, worker_concurrency=64)
        DBOS.register_queue(AGENTS, worker_concurrency=cfg.agent_concurrency)
        DBOS.register_queue(VERIFY, worker_concurrency=cfg.verify_concurrency)
        DBOS.register_queue(INTEGRATE, worker_concurrency=1)
        _launched = True
        LOG.info("bt_durable engine started (executor %s)", cfg.executor_id)


def stop(timeout: float = 0) -> None:
    """Destroy DBOS. Workflows still running go back to PENDING and are recovered by the next start."""
    global _ports, _config, _launched
    with _lock:
        if not _launched:
            return
        DBOS.destroy(workflow_completion_timeout_sec=int(timeout))
        _ports = _config = None
        _launched = False
