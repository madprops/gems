import subprocess
import re
import shutil
import sys

def get_installed_size_batch(packages):
    """
    Queries pacman for a list of packages in one go.
    Returns a dictionary: {'package_name': size_in_bytes}
    """
    if not packages:
        return {}

    # We pass all packages to pacman -Si at once for speed
    cmd = ["pacman", "-Si"] + packages

    try:
        # LC_ALL=C ensures standard English output for parsing
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env={"LC_ALL": "C", "PATH": "/usr/bin"}
        )
    except FileNotFoundError:
        print("Error: pacman not found.")
        sys.exit(1)

    sizes = {}
    current_pkg = None

    # Simple parser for pacman -Si output blocks
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Name"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                current_pkg = parts[1].strip()
        elif line.startswith("Installed Size") and current_pkg:
            parts = line.split(":", 1)
            if len(parts) > 1:
                size_str = parts[1].strip()
                sizes[current_pkg] = parse_size(size_str)
                current_pkg = None # Reset for safety

    return sizes

def parse_size(size_str):
    """Converts '123.45 MiB' to bytes."""
    parts = size_str.split()
    if len(parts) != 2:
        return 0

    val = float(parts[0])
    unit = parts[1]

    multipliers = {
        'B': 1,
        'KiB': 1024,
        'MiB': 1024**2,
        'GiB': 1024**3,
        'TiB': 1024**4
    }
    return val * multipliers.get(unit, 1)

def format_size(bytes_val):
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TiB"

def get_all_dependencies(target):
    """Uses pactree to get a flat list of all dependencies."""
    if not shutil.which("pactree"):
        print("Error: 'pactree' command not found.")
        print("Please install it with: sudo pacman -S pacman-contrib")
        sys.exit(1)

    print(f"Resolving full dependency tree for {target}...")
    # -u: unique, -s: sync database (remote packages)
    result = subprocess.run(
        ["pactree", "-u", "-s", target],
        stdout=subprocess.PIPE,
        text=True
    )

    # Filter out empty lines
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def guess_location(pkg_name):
    """
    Heuristic: ROCm packages almost always go to /opt/rocm.
    Standard libs go to /usr.
    """
    # Regex for packages known to install to /opt/rocm
    opt_pattern = r"^(rocm-|hip-|hsa-|miopen-|rccl|comgr|roc|amd|migraphx|mivisionx)"

    if re.match(opt_pattern, pkg_name):
        return "/opt"
    return "/usr"

def main():
    target = "rocm-hip-sdk"

    # 1. Get List
    deps = get_all_dependencies(target)
    print(f"Found {len(deps)} dependencies.")

    # 2. Get Sizes (Batch)
    print("Querying package sizes...")
    size_map = get_installed_size_batch(deps)

    # 3. Calculate Distribution
    stats = {"/opt": 0, "/usr": 0}

    # Sort for pretty printing big packages
    sorted_pkgs = sorted(size_map.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'Top 10 Largest Packages':<30} {'Dest':<10} {'Size':<10}")
    print("-" * 50)

    count = 0
    for pkg, size in sorted_pkgs:
        loc = guess_location(pkg)
        stats[loc] += size

        if count < 10:
            print(f"{pkg:<30} {loc:<10} {format_size(size):<10}")
            count += 1

    total = sum(stats.values())
    opt_pct = (stats['/opt'] / total) * 100 if total > 0 else 0
    usr_pct = (stats['/usr'] / total) * 100 if total > 0 else 0

    print("-" * 50)
    print(f"\n--- ESTIMATED DISTRIBUTION ---")
    print(f"/opt Usage : {format_size(stats['/opt']):<10} ({opt_pct:.1f}%)")
    print(f"/usr Usage : {format_size(stats['/usr']):<10} ({usr_pct:.1f}%)")
    print(f"TOTAL      : {format_size(total)}")

if __name__ == "__main__":
    main()