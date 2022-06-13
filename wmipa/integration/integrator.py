from abc import ABC, abstractmethod


class Integrator(ABC):
    """This class represents the general integrator with which to compute integrals.

    For the moment there is only one integrator that uses LattE Integrale.

    """

    @abstractmethod
    def __init__(self, **options):
        """Default constructor.

        Args:
            **options: whatever option is needed for the integrator

        """
        pass

    @abstractmethod
    def integrate(self, atom_assignments, weight, aliases):
        """Integrates a problem of the type {atom_assignments, weight, aliases}

        Args:
            problem (atom_assignments, weight, aliases): The problem to integrate.

        Returns:
            real: The integration result.

        """
        pass

    @abstractmethod
    def integrate_batch(self, problems):
        """Integrates a batch of problems of the type {atom_assignments, weight, aliases}

        Args:
            problems (list(atom_assignments, weight, aliases)): The list of problems to
                integrate.

        """
        pass
