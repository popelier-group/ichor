import sys


def is_ascii(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        content.encode("ascii")
        return True
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False


def main():
    non_ascii_files = [f for f in sys.argv[1:] if not is_ascii(f)]
    if non_ascii_files:
        print("Error: Non-ASCII characters found in:")
        for file in non_ascii_files:
            print(f"  - {file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
