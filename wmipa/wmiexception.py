"""This module implements the exceptions used throughout the code.

"""

version = '0.99'
author = 'Paolo Morettin'

class WMIException(Exception):
    """This class represents the general exception used in the WMI module.
        Every other exception will inherit from this one.
        
    Attributes:
        message (str): Human readable string describing the exception.
        
    """
    def __init__(self, message):
        """Default constructor.
            
        It assigns the message to the attributes.
        
        Args:
            message (str): Human readable string describing the exception.
        
        """
        self.message = message

    def __str__(self):
        """The str method.
        
        It uses the 'str' method to display the message of the exception.
        
        Returns:
            str: The string representation of the message.
        """
        return str(self.message)

class WMIParsingException(WMIException):
    """This exception handles all the cases where the code fails to parse a given expression of formula.
        
    Attributes:
        code (int): The code of the exception.
        value: Additional info about the value that raised the exception (default: None).
        
    """
    
    """During the parsing of the formula, it was encountered an equality that does not respect
        the specific formatting of an equality. One of the two arguments must return True to the
        pysmt method '.is_symbol()' and the other one must return True to the expression
        '.get_type() == REAL'.
        An example of correct equality is: 'x = Plus(y, Real(3))' where
        x = Symbol('X', REAL) and y = Symbol('Y', REAL).
        
    """
    MALFORMED_ALIAS_EXPRESSION = 0
    
    """During the parsing of the formula, it was encountered a node that cannot exists inside
        the formula representing the weight function. The weight function ammits only these internal nodes:
        PLUS, MINUS, TIMES, DIV, POW, ITE. Also as a leaf node there must be a Real or a Symbol with
        type equal to Real.
        
    """
    INVALID_WEIGHT_FUNCTION = 1
    
    """During the parsing of the formula, it was encountered an expression that couldn't be converted to pysmt.
        The expression must be of one of this types: PLUS, MINUS, TIMES, DIV, POW, SYMBOL, REAL.
        
    """
    CANNOT_CONVERT_SYMPY_FORMULA_TO_PYSMT = 2
    
    """During the parsing of the formula, it was encountered an expression that couldn't be converted to sympy.
        The expression must be of one of this types: PLUS, MINUS, TIMES, DIV, POW, SYMBOL, REAL.
        
    """
    CANNOT_CONVERT_PYSMT_FORMULA_TO_SYMPY = 3
    
    """During the parsing of the formula, it was encountered an expression that is not a monomial.
    
    """
    NOT_A_MONOMIAL = 4
    
    """During the parsing of the formula, it was encountered two or more aliases (equalities) that
        lead to a cyclic assignment (e.g: y = x, x = y).
    
    """
    CYCLIC_ASSIGNMENT_IN_ALIASES = 5
    
    """During the parsing of the formula, it was encountered an expression that does not represent an inequality.
    
    """
    NOT_AN_INEQUALITY = 6
    
    """During the parsing of the formula, it was encountered an expression that represents a polynomial
        with a degree greater than one. This is not supported in this module because it handles only
        linear inequalities over reals.
    
    """
    POLYNOMIAL_WITH_DEGREE_GREATER_THAN_ONE = 7
    
    """During the parsing of the formula, it was encountered a same alias with two or more assignments
        (e.g: z = x+3, z = y-2). This module does not support this kind of operations, for every alias
        there must be at most one assignment.
    
    """
    MULTIPLE_ASSIGNMENT_SAME_ALIAS = 8
    
    messages = {
        MALFORMED_ALIAS_EXPRESSION: "Malformed alias expression",
        INVALID_WEIGHT_FUNCTION: "Invalid weight function",
        CANNOT_CONVERT_SYMPY_FORMULA_TO_PYSMT: "Cannot convert the sympy formula to a pysmt formula",
        CANNOT_CONVERT_PYSMT_FORMULA_TO_SYMPY: "Cannot convert the pysmt formula to a sympy formula",
        NOT_A_MONOMIAL: "Not a monomial",
        CYCLIC_ASSIGNMENT_IN_ALIASES: "Cyclic assignment in the aliases",
        NOT_AN_INEQUALITY: "Not an inequality",
        POLYNOMIAL_WITH_DEGREE_GREATER_THAN_ONE: "Polynomial with degree greater than one",
        MULTIPLE_ASSIGNMENT_SAME_ALIAS: "Multiple assignments to the same alias"
    }

    def __init__(self, code, value=None):
        """Default constructor.
            
        It first calls the init method of the parent and then assignes the expression to the attributes.
        
        Args:
            code (int): The code of the exception.
            value (optional): Additional info about the value that raised the exception (default: None).
        
        """
        self.code = code
        self.value = value
        if value:
            message = "{}: {}".format(self.messages[code], self.value)
        else:
            message = self.messages[code]
        super().__init__(message)

class WMIRuntimeException(WMIException):
    """This exception handles all the cases where the code fails because of wrong parameters or settings.
        
    Attributes:
        code (int): The code of the exception.
        value: Additional info about the value that raised the exception (default: None).
    """
    
    """The domain of integration of the numerical variables should be all the variables in the formula. 
        The domain of integration of the Boolean variables should be a superset of all the boolean
        variables in the formula.
    """
    DOMAIN_OF_INTEGRATION_MISMATCH = 0
    
    """The mode selected is not correct. Check which are the possibilities (it should be displayed
        in the error message).
    
    """
    INVALID_MODE = 1
    
    messages = {
        DOMAIN_OF_INTEGRATION_MISMATCH: "Domain of integration mismatch",
        INVALID_MODE: "Invalid mode"
    }
    
    def __init__(self, code, value=None):
        """Default constructor.
            
        It calls the init method of the parent.
            
        Args:
            code (int): The code of the exception.
            value: Additional info about the value that raised the exception (default: None).
        
        """
        self.code = code
        self.value = value
        if value:
            message = "{}: {}".format(self.messages[code], self.value)
        else:
            message = self.messages[code]
        super().__init__(message)
        
class WMIParsingFileException(WMIException):
    """This exception handles all the cases where the code fails parsing the input file.
        
    Attributes:
        code (int): The code of the exception.
        value: Additional info about the value that raised the exception (default: None).
    """
    
    """During the parsing of the file it was encountered an operation that is not supported by
        WMI module.
        
    """
    OPERATION_NOT_SUPPORTED = 0
    
    """During the parsing of the file it was encountered a type error. More info in the error message
        itself.
        
    """
    TYPE_ERROR = 1
    
    """During the parsing of the file it was encountered a double type declaration, that is the same
        variable was declared twice in the file (e.g: y=5; y=10).
        
    """
    DOUBLE_DECLARATION = 2
    
    """During the parsing of the file it was encountered a type that is not supported by WMI.
    
    """
    TYPE_NOT_SUPPORTED = 3
    
    """During the parsing of the file it was encountered a variable that was not declared in the model.
        More info in the error message itself.
    
    """
    VARIABLE_NOT_DECLARED = 4
    
    """During the parsing of the file it was encountered a variable that was not initialized.
        More info in the error message itself.
    
    """
    VARIABLE_NOT_INITIALIZED = 5
    
    """During the parsing of the file it was encountered a type that is not supported by WMI.
        More info in the error message itself.
    
    """
    DOUBLE_WEIGHT_DECLARATION = 6
    
    """During the parsing of the file it was encountered a query declaration in a model file.
        This type of declaration can only be declared in the query or complete file.
    
    """
    QUERY_IN_MODEL = 7
    
    """During the parsing of the file it was encountered a syntax error (this could be an error
        in the format itself or something that is not recognized by WMI.
        More info in the error message itself.
    
    """
    SYNTAX_ERROR = 8
    
    messages = {
        OPERATION_NOT_SUPPORTED: "Operation not supported",
        TYPE_ERROR: "Type error",
        DOUBLE_DECLARATION: "Variable already defined",
        TYPE_NOT_SUPPORTED: "Type not supported",
        VARIABLE_NOT_DECLARED: "Variable not declared",
        VARIABLE_NOT_INITIALIZED: "Variable not initialized",
        DOUBLE_WEIGHT_DECLARATION: "Double weight declaration",
        QUERY_IN_MODEL: "Query declaration in model file",
        SYNTAX_ERROR: "Syntax error"
    }
    
    def __init__(self, code, value=None):
        """Default constructor.
            
        It calls the init method of the parent.
            
        Args:
            code (int): The code of the exception.
            value: Additional info about the value that raised the exception (default: None).
        
        """
        self.code = code
        self.value = value
        if value:
            message = "{}: {}".format(self.messages[code], self.value)
        else:
            message = self.messages[code]
        super().__init__(message)
