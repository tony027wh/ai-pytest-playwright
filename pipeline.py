import argparse
import subprocess
import sys


def run_pipeline(story: str = None, test: str = None) -> None:
    gen_cmd = [sys.executable, "generate_test.py"]
    if story:
        gen_cmd += ["--story", story]
    subprocess.run(gen_cmd, check=True)

    test_cmd = [sys.executable, "-m", "pytest"]
    if test:
        test_cmd.append(f"tests/{test}")
    subprocess.run(test_cmd)  # intentionally ignore exit code — tests may fail

    subprocess.run([sys.executable, "analyze/analyze_failures.py", "--html"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full AI test pipeline")
    parser.add_argument("--story", help="Generate only this story (e.g. login.md)")
    parser.add_argument("--test", help="Run only this test file (e.g. test_login.py)")
    args = parser.parse_args()
    run_pipeline(story=args.story, test=args.test)
