import os

from snowflake import SnowflakeGenerator

WORKER_ID: int = int(os.getenv("WORKER_ID", "1"))
_gen = SnowflakeGenerator(WORKER_ID)


def snowflake_id() -> int:
    """
    Returns a unique, time-sortable integer ID.
    Format: (timestamp << x) | worker_id << y | sequence
    """
    _xid = next(_gen)
    if not isinstance(_xid, int):
        raise TypeError(f"Expected int, got {_xid.__class__.__name__}")
    return int(_xid)
