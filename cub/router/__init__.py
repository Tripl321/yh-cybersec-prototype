"""Model Router / Policy Decision Point (ADR 0006).

Routes on *original* sensitivity (never the LLM-rewritten text) and required
capability. The model never chooses its own tier. Default = local.
"""
from __future__ import annotations

from enum import Enum

from cub.config import CubConfig
from cub.providers import build_local_model, build_cloud_model


class Sensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


def route(cfg: CubConfig, sensitivity: Sensitivity, requires_cloud_capability: bool = False):
    if requires_cloud_capability and cfg.cloud_enabled:
        return build_cloud_model(cfg)
    return build_local_model(cfg)
