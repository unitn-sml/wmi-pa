from wmipa.integration.integrand import Integrand
from wmipa.utils import apply_aliases


class Expression(Integrand):
    """Generic Expression to integrate"""

    def __init__(self, expression, aliases=None):
        super().__init__()
        if aliases is None:
            aliases = {}

        self.expression = apply_aliases(expression, aliases)
        self.variables = set(map(str, self.expression.get_free_variables()))

    def __str__(self):
        return self.expression.serialize()

    def to_pysmt(self):
        return self.expression
