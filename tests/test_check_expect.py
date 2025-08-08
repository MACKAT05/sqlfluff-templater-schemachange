import subprocess
import sys
from pathlib import Path

# List of test subdirectories to skip
SKIP_DIRS = {"extends"}


def run_check_expect_tests():
    base_dir = Path(__file__).parent
    tests_dir = base_dir
    all_test_dirs = [
        d for d in tests_dir.iterdir() if d.is_dir() and d.name not in SKIP_DIRS
    ]
    failed = False

    for test_dir in all_test_dirs:
        print(f"\n=== Running check/expect test in: {test_dir} ===")
        env = dict(**os.environ)
        env_sh = test_dir / "env.sh"
        if env_sh.exists():
            # Source env.sh and update env for subprocess
            source_cmd = f"set -a && source '{env_sh}' && env"
            proc = subprocess.Popen(["bash", "-c", source_cmd], stdout=subprocess.PIPE)
            out, _ = proc.communicate()
            for line in out.decode().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k] = v

        # Run sqlfluff render
        sql_file = test_dir / "test.sql"
        expect_file = test_dir / "test.expect"
        out_file = test_dir / "test.out"
        if not sql_file.exists() or not expect_file.exists():
            print(f"Skipping {test_dir}: missing test.sql or test.expect")
            continue
        config_file = test_dir / ".sqlfluff"
        cmd = ["sqlfluff", "render", "--config", str(config_file), str(sql_file)]
        with open(out_file, "w") as f:
            result = subprocess.run(
                cmd, cwd=test_dir, env=env, stdout=f, stderr=subprocess.PIPE, text=True
            )
        # Compare output
        diff_cmd = ["diff", "-u", str(expect_file), str(out_file)]
        if result.returncode != 0:
            print(f"❌ Error running sqlfluff render in {test_dir}: {result.stderr}")
            failed = True
            continue
        diff_result = subprocess.run(
            diff_cmd, cwd=test_dir, capture_output=True, text=True
        )
        if diff_result.returncode != 0:
            print(f"❌ Output differs in {test_dir}:")
            print(diff_result.stdout)
            failed = True
        else:
            print(f"✅ {test_dir.name} passed.")
    if failed:
        print("\nSome check/expect tests failed.")
        sys.exit(1)
    else:
        print("\nAll check/expect tests passed.")


if __name__ == "__main__":
    import os

    run_check_expect_tests()
