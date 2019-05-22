import argparse
import bmc.errors
import bmc.scanner
import bmc.parse

parser = argparse.ArgumentParser(description="Biyani-Marrone Compiler")

parser.add_argument("input_file", type=argparse.FileType(), help="The source file to read in, or the '-' character for stdin.")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--output-tokens", action="store_true", help="Output a list of the scanned tokens.")
group.add_argument("--output-ast", action="store_true", help="Output the pretty-printed abstract syntax tree.")
group.add_argument("--output-llvm", action="store_true", help="Output the LLVM intermediate representation source.")

args = parser.parse_args()

logger = bmc.errors.ErrorLogger()

scanner = bmc.scanner.Scanner(file=args.input_file, error_logger=logger)

if not args.output_tokens:
    ast = bmc.parse.parse(scanner, logger)
    if not args.output_ast:
        llvm = ast.compile(logger) # To do: Incorporate error logger.

if logger.count():
    logger.print_all()
elif args.output_tokens:
    for token in scanner:
        print(token)
elif args.output_ast:
    print(ast)
else: # --output-llvm
    print(llvm)
