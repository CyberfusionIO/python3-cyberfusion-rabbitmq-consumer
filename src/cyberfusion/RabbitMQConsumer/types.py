"""Custom types."""

import threading
from typing import Dict, NewType

Locks = NewType("Locks", Dict[str, Dict[str, threading.Lock]])
