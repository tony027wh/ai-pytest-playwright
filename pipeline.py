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
    subprocess.run(test_cmd)  # 有意忽略退出码 —— 测试可能失败

    subprocess.run([sys.executable, "analyze/analyze_failures.py", "--html"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行完整的 AI 测试流水线")
    parser.add_argument("--story", help="仅生成此故事（例如 login.md）")
    parser.add_argument("--test", help="仅运行此测试文件（例如 test_login.py）")
    args = parser.parse_args()
    run_pipeline(story=args.story, test=args.test)
