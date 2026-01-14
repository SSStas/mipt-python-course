import sys

try:
    from concurrent import interpreters
except ImportError:
    interpreters = None


# Functions for Test 2.1

def append_value(lst: list[int], value: int) -> list[int]:
    lst.append(value)
    return lst

# Functions for Test 2.2

def write_to_first_byte(mv: memoryview, ch: str) -> int:
    if (not ch or len(ch) != 1):
        raise ValueError("ch must be a non-empty string with length 1")
    mv[0] = ord(ch)
    return int(mv[0])

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
    
    print("Test 2.1: non-shareable list (mutable object)")
    data = [1, 2, 3, 4]
    interp = interpreters.create()
    try:
        interp_data = interp.call(append_value, data, 5)
        print("main_interp:", data)
        print("subinterp:", interp_data)
        append_value(data, 10)
        print("main_interp:", data)
        print("subinterp:", interp_data)
    finally:
        interp.close()

    print()

    print("Test 2.2: shareable memoryview")
    buf = bytearray(b"qwerty")
    mv = memoryview(buf)
    interp = interpreters.create()
    try:
        print("main_interp:", mv[0], chr(mv[0]))
        interp_b0 = interp.call(write_to_first_byte, mv, "A")
        print("main_interp:", mv[0], chr(mv[0]))
        print("subinterp:", interp_b0, chr(interp_b0))
    finally:
        interp.close()

if __name__ == "__main__":
    main()
