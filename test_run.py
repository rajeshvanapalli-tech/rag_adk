import subprocess
import sys

with open("full_error.log", "w") as f:
    try:
        result = subprocess.run(
            [sys.executable, "backend/main.py"],
            capture_output=True,
            text=True,
            timeout=15
        )
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
    except subprocess.TimeoutExpired as e:
        f.write("TIMEOUT\n")
        f.write("STDOUT:\n")
        f.write(e.stdout or "")
        f.write("\nSTDERR:\n")
        f.write(e.stderr or "")
    except Exception as e:
        f.write(f"FAILED: {e}")
