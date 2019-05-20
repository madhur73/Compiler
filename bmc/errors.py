import sys

class ReportableError(Exception):
    """Represents a problem in the compiled program that can be reported to the user.
    
    Different parts of the compiler (scanner, parser, etc.) should subclass this
    so that their errors can be distinguished from each other, which makes
    unit tests more precise.
    """
    
    def __init__(self, message, token=None):
        """Initialize the exception.
        
        Args:
            message: Passed on to the constructor for Exception.  Should be a
                human-readable message describing the problem.
            token: If provided, this token's location will be provided as part
                of the message.
        """
        self.token = token
        if self.token:
            prefix = f"Error ({token.line}:{token.column}): "
        else:
            prefix = "Error: "
        super().__init__(prefix + message)

class ErrorLogger:
    """Deferred reporting of ReportableErrors.
    
    The different phases of compilation can share a single ErrorLogger instance.
    Each phase logs (recoverable) errors as it comes across them.  At the end,
    the ErrorLogger class allows all the logged errors to be printed in sorted
    order.
    """
    
    def __init__(self):
        self.errors = []
    def log(self, reportable_error):
        self.errors.append(reportable_error)
    def count(self):
        return len(self.errors)
    def print_all(self):
        def location(error):
            return error.token.begin if error.token else 0
        for error in sorted(self.errors, key=location):
            print(_red + str(error) + _reset)

if sys.stdout.isatty():
    # ANSI escape codes for printing colored text to the terminal.
    _red = "\033[31m"
    _reset = "\033[0m"
else:
    _red = _reset = ""
