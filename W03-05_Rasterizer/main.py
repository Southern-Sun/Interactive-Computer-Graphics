import sys

command_file = sys.argv[1]
if "file=" in command_file:
    _, _, command_file = command_file.partition("=")

