"""
Plugin for the agent
"""

from pkg_resources import get_distribution, DistributionNotFound
from .agent_capability_plugin import AgentPlugin

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = '0.0.0'
