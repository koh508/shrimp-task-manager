import dotenv
import sys

print(f"Python Executable: {sys.executable}")
print(f"System Path: {sys.path}")
print("--- Attempting to locate dotenv module ---")

try:
    print(f"dotenv module location: {dotenv.__file__}")
    from dotenv import load_dotenv

    print("Successfully imported 'load_dotenv' from 'dotenv'")
    print("python-dotenv package seems to be installed correctly.")
except Exception as e:
    print(f"An error occurred: {e}")
    print("There might be a conflicting 'dotenv' package or an installation issue.")
