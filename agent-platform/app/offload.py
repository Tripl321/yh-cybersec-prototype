"""
Result Offloading
=========================

Offload big tool results to a database instead of the context window.
"""

from agno.offload import ResultStore

RESULT_TTL_SECONDS = 7 * 24 * 60 * 60

result_store = ResultStore(ttl_seconds=RESULT_TTL_SECONDS)
