import queue
import threading
from typing import TYPE_CHECKING, Iterable

from pysmt.fnode import FNode

from wmipa.enumeration.enumerator import Enumerator

if TYPE_CHECKING:  # avoid circular import
    from wmipa.solver import AllSMTSolver


class AsyncWrapper:
    def __init__(self, enumerator: "Enumerator", max_queue_size: int = 0) -> None:
        """
        Initializes the AsyncEnumerator with the given enumerator and queue size.

        Args:
            enumerator: An instance of Enumerator to be used for enumeration.
            max_queue_size: Maximum number of assignments to compute in parallel.
                             0 means no limit.
        """
        self.enumerator = enumerator
        self.max_queue_size = max_queue_size

    def initialize(self, solver: "AllSMTSolver") -> None:
        """
        Initializes the enumerator with the given solver.

        Args:
            solver: An instance of AllSMTSolver to be used for enumeration.
        """
        self.enumerator.initialize(solver)

    def enumerate(self, phi: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
        """
        Enumerates the convex fragments of the given formula.

        Args:
            phi: The formula to be enumerated.

        Yields:
            A tuple containing a dictionary of truth assignments and the number of unassigned variables.
        """
        q: queue.Queue = queue.Queue(maxsize=self.max_queue_size)
        stop_token = object()
        error_token = object()

        # Thread control
        thread_stop_event = threading.Event()

        def run() -> None:
            try:
                for result in self.enumerator.enumerate(phi):
                    q.put(result)
                    if thread_stop_event.is_set():
                        break
                q.put(stop_token)
            except Exception as e:
                q.put((error_token, e))

        t = threading.Thread(target=run, daemon=True)
        t.start()  # We enumerate async

        try:
            while True:
                item = q.get()
                if item is stop_token:
                    break
                elif isinstance(item, tuple) and item[0] is error_token:
                    raise item[1]  # Re-raise the exception from the thread
                else:
                    # Only yield valid assignments
                    yield item
        finally:
            if t is not None and t.is_alive():
                thread_stop_event.set()
                t.join()  # Ensure the thread is cleaned up
