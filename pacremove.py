import subprocess
import sys

def format_size(size_bytes):
    """Converts bytes to human readable string."""
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TiB"

def get_removal_size(package_name):
    """
    Uses pacman's --print-format to get raw bytes for all targets.
    """
    # -Rcs: Recursive cascade removal
    # -p: Print only (don't remove)
    # --print-format '%s': Print only the size in bytes for each package
    cmd = ["sudo", "pacman", "-Rcs", "-p", "--print-format", "%s", package_name]

    try:
        # LC_ALL=C is still good practice, though less critical here
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={"LC_ALL": "C", "PATH": "/usr/bin"}
        )

        if result.returncode != 0:
            print(f"Error: Pacman returned an error.")
            print(result.stderr.strip())
            return None

        total_bytes = 0

        # Iterate over output lines. Each valid line should be a number (bytes).
        for line in result.stdout.splitlines():
            line = line.strip()
            # Skip empty lines or lines that might be warnings/text
            if line.isdigit():
                total_bytes += int(line)

        return total_bytes

    except FileNotFoundError:
        print("Error: pacman not found.")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_removal_size_v3.py <package_name>")
        sys.exit(1)

    pkg = sys.argv[1]

    print(f"Calculating space freed by removing '{pkg}' recursively...")

    total_bytes = get_removal_size(pkg)

    if total_bytes is not None:
        readable_size = format_size(total_bytes)
        print("-" * 40)
        print(f"Space to be freed: {readable_size}")
        print("-" * 40)

if __name__ == "__main__":
    main()