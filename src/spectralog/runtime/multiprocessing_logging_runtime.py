from __future__ import annotations

import logging
from logging import LogRecord
from logging.handlers import QueueHandler
from logging.handlers import QueueListener
from multiprocessing.queues import Queue
from multiprocessing.util import Finalize
from threading import RLock

# multiprocessing closes its queues from finalizers with exitpriority 10 when a
# child process exits. Higher priorities run first, so the listener is stopped
# while the queue is still open.
_STOP_EXIT_PRIORITY = 100


class MultiprocessingLoggingRuntime:
    """Manage the lifecycle of SpectraLog's multiprocessing logging pipeline.

    ``MultiprocessingLoggingRuntime`` owns the queue handler, queue listener, and
    multiprocessing queue used for queue-based file logging.

    The runtime provides explicit :meth:`start` and :meth:`stop` operations and
    tracks whether the listener is currently running or whether the runtime has
    already been permanently closed.

    Lifecycle operations are protected by a reentrant lock so that state changes
    remain consistent when multiple threads attempt to start, stop, or inspect the
    runtime concurrently.

    Starting the runtime launches the configured
    :class:`logging.handlers.QueueListener`. Stopping the runtime first stops the
    listener when necessary, then closes the queue handler and multiprocessing
    queue, waits for the queue's feeder thread to terminate, and marks the runtime
    as closed.

    The multiprocessing queue is exposed through :attr:`log_record_queue` so that
    worker processes can be configured to forward their records to this runtime's
    listener.

    A closed runtime cannot be started again. Both :meth:`start` and :meth:`stop`
    are safe to call repeatedly without duplicating lifecycle operations."""

    def __init__(
        self,
        queue_handler: QueueHandler,
        queue_listener: QueueListener,
        log_record_queue: Queue[LogRecord],
    ) -> None:
        """Initialize the multiprocessing logging runtime.

        Args:
            queue_handler:
                Queue handler attached to the application logger. Accepted log records
                are placed onto the multiprocessing queue for asynchronous processing.

            queue_listener:
                Listener responsible for consuming log records from the queue and
                forwarding them to the configured downstream handlers.

            log_record_queue:
                Multiprocessing queue used to transport log records between the queue
                handler and queue listener."""
        self._queue_handler = queue_handler
        self._queue_listener = queue_listener
        self._log_record_queue = log_record_queue
        self._lock = RLock()
        self._is_running = False
        self._is_closed = False

    @property
    def queue_handler(self) -> logging.Handler:
        """Return the queue handler used by the multiprocessing logging runtime.

        The application logger attaches this handler instead of attaching the file
        handler directly when multiprocessing-safe file logging is enabled.

        Returns:
            logging.Handler:
                The queue handler that publishes log records to the multiprocessing
                logging queue."""
        queue_handler = self._queue_handler

        return queue_handler

    @property
    def is_running(self) -> bool:
        """Return whether the queue listener is currently running.

        The runtime state is read while holding the internal lock to keep lifecycle
        inspection synchronized with concurrent start and stop operations.

        Returns:
            bool:
                ``True`` when the queue listener has been started and has not yet been
                stopped; otherwise ``False``."""
        with self._lock:
            is_running = self._is_running

        return is_running

    @property
    def log_record_queue(self) -> Queue[LogRecord]:
        """Return the multiprocessing queue consumed by this runtime's listener.

        Worker processes can attach a queue handler for this queue so that their
        records are written by the parent's listener and file handler rather than
        by a file handler of their own.

        The queue must be passed to worker processes when they are created, for
        example through :class:`multiprocessing.Process` arguments or a pool
        initializer.

        Returns:
            Queue[LogRecord]:
                The multiprocessing queue that transports log records to the
                listener."""
        log_record_queue = self._log_record_queue

        return log_record_queue

    def start(self) -> None:
        """Start the multiprocessing queue listener.

        The listener is started only when the runtime is not already running and has
        not previously been closed.

        Repeated calls while the runtime is already running have no effect. Calls
        after :meth:`stop` has permanently closed the runtime also have no effect.

        The lifecycle transition is protected by the runtime's internal reentrant
        lock."""
        with self._lock:
            if not self._is_running and not self._is_closed:
                self._queue_listener.start()
                self._is_running = True

                # In multiprocessing child processes (Python 3.12 and earlier),
                # multiprocessing closes the queue before atexit runs
                # ApplicationLogger.shutdown, so the listener thread dies with
                # EOFError/OSError and can drop records still in the queue.
                Finalize(
                    self,
                    self.stop,
                    exitpriority=_STOP_EXIT_PRIORITY,
                )

    def stop(self) -> None:
        """Stop the multiprocessing logging runtime and release its resources.

        If the queue listener is currently running, it is stopped first so that
        queued records can be processed before queue resources are released.

        The queue handler is then closed, followed by the multiprocessing queue. The
        queue's feeder thread is joined to ensure that its background resources have
        terminated before shutdown completes.

        After cleanup, the runtime is marked as permanently closed and cannot be
        started again.

        This method is idempotent. Calling it after the runtime has already been
        closed returns immediately without repeating cleanup operations."""
        with self._lock:
            if self._is_closed:
                return

            if self._is_running:
                self._queue_listener.stop()
                self._is_running = False

            self._queue_handler.close()

            self._log_record_queue.close()
            self._log_record_queue.join_thread()

            self._is_closed = True
