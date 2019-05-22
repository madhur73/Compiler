# Project Status

See DESCRIPTION.md.

# Dependencies

BMC is tested on Python 3.6.

# Usage Example

    python3 bmc.py example.boris --output-llvm > example.ll
    clang example.ll
    ./a.out
    
Run `python3 bmc.py --help` for details.

# Unit Tests

BMC uses [pytest](https://docs.pytest.org/en/latest/) to run unit tests.  To install it:

    pip3 install --user pytest

Then, to run the tests, from the root directory:

    pytest-3
