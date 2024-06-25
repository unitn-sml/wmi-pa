from abc import ABC, abstractmethod


class Integrator(ABC):
    """This class represents the general integrator with which to compute integrals.

    """

    @abstractmethod
    def __init__(self, **options):
        """Default constructor.

        Args:
            **options: whatever option is needed for the integrator

        """
        raise NotImplementedError()

    @abstractmethod
    def integrate(self, polytope, integrand, *args, **kwargs):
        """Integrates a single (polytope, integrand)

        Args:
            polytope (Polytope): A polytope (H-representation).
            integrand (Integrand): The integrand function.

        Returns:
            real: The integration result.
            bool: Was the result in cache?.

        """
        raise NotImplementedError()

    @abstractmethod
    def integrate_batch(self, integrals, *args, **kwargs):
        """Integrates a list of (polytope, integrand)

        Args:
            integrals (list(Polytope, Integrand)).

        Returns:
            list(real): The list of integrals.
            int: The number of cache hits.

        """
        raise NotImplementedError()
