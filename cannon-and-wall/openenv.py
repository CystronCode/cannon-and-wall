"""
Local shim for the OpenEnv Environment base class.
The PyPI `openenv` package (v0.1.x) exposes only openenv.env.Env
and does not include an `Environment` class. This module provides
the abstract base that CannonWallEnvironment subclasses, matching
the interface declared in openenv.yaml.
"""

class Environment:
    """Base class for OpenEnv-compatible environments."""

    def __init__(self):
        self.state = {}

    def reset(self, **kwargs) -> dict:
        raise NotImplementedError

    def step(self, action: dict) -> dict:
        raise NotImplementedError

    def get_state(self) -> dict:
        return self.state
