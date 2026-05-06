"""
Circuit Breaker Pattern Implementation
"""
import logging
import time
from enum import Enum
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Service is failing, requests are rejected
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 30
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout  # seconds to wait before trying again

        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()

    def can_execute(self) -> bool:
        """Check if a request can be executed"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.stats.last_failure_time:
                elapsed = time.time() - self.stats.last_failure_time
                if elapsed >= self.timeout:
                    # Transition to half-open
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self) -> None:
        """Record a successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.stats.successes += 1
            if self.stats.successes >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failures = 0

    def record_failure(self) -> None:
        """Record a failed request"""
        self.stats.failures += 1
        self.stats.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open returns to open
            self._transition_to(CircuitState.OPEN)
        elif self.state == CircuitState.CLOSED:
            if self.stats.failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state"""
        old_state = self.state
        self.state = new_state

        # Reset stats on state change
        if new_state == CircuitState.CLOSED:
            self.stats = CircuitStats()
        elif new_state == CircuitState.HALF_OPEN:
            self.stats.successes = 0

        logger.info(f"Circuit breaker '{self.name}': {old_state.value} -> {new_state.value}")

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN


# Service circuit breakers
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a service"""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(service_name)
    return _circuit_breakers[service_name]
