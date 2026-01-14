import sys

try:
    from concurrent import interpreters
except ImportError:
    interpreters = None


# Functions for Test 1.1

def set_global_var(var_name: str, var_value: int):
    globals()[var_name] = var_value

def is_global_var_exists(var_name: str) -> bool:
    return (var_name in globals())

# Functions for Test 1.2

def import_math():
    import math

def check_math_import() -> bool:
    import sys
    return ("math" in sys.modules)

# Functions for Test 1.3

def monkeypatch_len():
    import builtins
    builtins.len = lambda obj: -1

def get_len_of_str(s: str) -> int:
    return len(s)

# Main function

def main() -> int:
    if (interpreters is None):
        print(
            "Error: subinterpreters are not available in this Python",
            "Requires Python 3.14+ (concurrent.interpreters)",
            f"Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            file=sys.stderr,
            sep="\n",
        )
        sys.exit(1)
    
    print("Test 1.1: globals() isolation")
    interp1 = interpreters.create()
    interp2 = interpreters.create()
    try:
        interp1.call(set_global_var, "x", 123)
        print("main_interp:", is_global_var_exists("x"))
        print("interp1:", interp1.call(is_global_var_exists, "x"))
        print("interp2:", interp2.call(is_global_var_exists, "x"))
    finally:
        interp1.close()
        interp2.close()

    print()

    print("Test 1.2: sys.modules isolation")
    interp1 = interpreters.create()
    interp2 = interpreters.create()
    try:
        interp1.call(import_math)
        print("main_interp:", check_math_import())
        print("interp1:", interp1.call(check_math_import))
        print("interp2:", interp2.call(check_math_import))
    finally:
        interp1.close()
        interp2.close()

    print()

    print("Test 1.3: built-ins isolation")
    interp1 = interpreters.create()
    interp2 = interpreters.create()
    try:
        interp1.call(monkeypatch_len)
        print("main_interp:", get_len_of_str("qwerty"))
        print("interp1:", interp1.call(get_len_of_str, "qwerty"))
        print("interp2:", interp2.call(get_len_of_str, "qwerty"))
    finally:
        interp1.close()
        interp2.close()


if __name__ == "__main__":
    main()
