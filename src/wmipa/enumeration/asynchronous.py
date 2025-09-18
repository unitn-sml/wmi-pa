import queue
import threading
from typing import TYPE_CHECKING, Iterable

from pysmt.fnode import FNode
from pysmt.environment import Environment

from wmipa.enumeration.enumerator import Enumerator
from wmipa.core.weights import Weights

if TYPE_CHECKING:  # avoid circular import
    from wmipa.solvers import WMISolver


class AsyncWrapper(Enumerator):
    """This class implements a wrapper around an arbitrary Enumerator.
    The enclosed enumerator will run on a separate thread, enabling asychronous execution.

    """

    def __init__(self, enumerator: "Enumerator", max_queue_size: int = 0) -> None:
        """Default constructor.

        Args:
            enumerator: the enclosed Enumerator
            max_queue_size: maximum number of assignments to compute in parallel
        """
        self.enumerator = enumerator
        self.max_queue_size = max_queue_size

    @property
    def support(self) -> FNode:
        return self.enumerator.support

    @property
    def weights(self) -> Weights:
        return self.enumerator.weights

    @property
    def env(self) -> Environment:
        return self.enumerator.env

    def enumerate(self, query: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
        """Enumerates (possibly partial) truth assignments for the given formula using the enclosed enumerator.

        The class attribute max_queue_size controls the size of the queue, regulating how many truth assignments can be enumerated without further processing.

        Args:
            query: the query as a pysmt formula

        Returns:
            An iterable of tuples <TA, NB> where:
            - TA is a dictionary {pysmt_atom : bool} representing (partial) truth assignment
            - NB is a non-negative integer representing the number of unassigned Boolean variables
        """
        q: queue.Queue = queue.Queue(maxsize=self.max_queue_size)
        stop_token = object()
        error_token = object()

        # Thread control
        thread_stop_event = threading.Event()

        def run() -> None:
            try:
                for result in self.enumerator.enumerate(query):
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
