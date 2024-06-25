

class Integrand:
    """Generic integrand."""

    def __init__(self, expression):

        super().__init__()
        self.variables = set(map(str, self.expression.get_free_variables()))

    def __str__(self):
        return self.expression.serialize()

    def to_pysmt(self):
        return self.expression
