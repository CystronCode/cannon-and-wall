# openenv.py — local stub satisfying "from openenv import Environment"
class Environment:
    """Minimal OpenEnv-compatible base class."""
    def __init__(self):
        self.state = {}

    def reset(self, **kwargs):
        raise NotImplementedError

    def step(self, action: dict):
        raise NotImplementedError
