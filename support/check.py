import sys
import subprocess
import tempfile
import os
import argparse


def extract_python_snippets(readme_path: str) -> list[tuple[int, int, str]]:
    """
    Extracts Python code snippets from README.md file.
    Returns list of tuples: (start_line, end_line, code).
    """
    snippets = []
    with open(readme_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_snippet = False
    start_line = 0
    current_snippet = []

    for i, line in enumerate(lines, 1):
        if line.strip() == "```python":
            in_snippet = True
            start_line = i
            current_snippet = []
        elif line.strip() == "```" and in_snippet:
            in_snippet = False
            snippets.append((start_line + 1, i - 1, "".join(current_snippet)))
        elif in_snippet:
            current_snippet.append(line)

    return snippets


def run_snippet(snippet: str) -> tuple[bool, str]:
    """
    Runs a Python code snippet in a new interpreter process.
    Returns tuple: (success, error_message).
    """
    # Create a temporary file to hold the snippet
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
        tf.write(snippet)
        temp_path = tf.name

    try:
        # Run the snippet in a new Python interpreter process
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            env=os.environ.copy(),  # Use current environment (including virtual env)
        )

        # Check if there was an error
        if result.returncode != 0:
            return False, result.stderr
        return True, ""

    finally:
        # Clean up temporary file
        os.unlink(temp_path)


def main(readme_path: str, exit_on_error: bool = False):
    """Main function to process README.md and run snippets."""
    if not os.path.exists(readme_path):
        print(f"Error: File {readme_path} not found!")
        return

    snippets = extract_python_snippets(readme_path)

    for i, (start_line, end_line, code) in enumerate(snippets, 1):
        print(f"\nProcessing snippet {i} (lines {start_line}-{end_line}):")

        success, error = run_snippet(code)

        if success:
            print("✓ Snippet ran successfully")
        else:
            print("✗ Error occurred while running snippet:")
            print("\nCode:")
            print("-" * 40)
            print(code.strip())
            print("-" * 40)
            print("\nError:")
            print(error)
            if exit_on_error:
                sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Python code snippets from README.md"
    )
    parser.add_argument("readme_path", help="Path to README.md file")
    parser.add_argument(
        "-e",
        "--exit-on-error",
        action="store_true",
        help="Exit on first error encountered",
    )

    args = parser.parse_args()
    main(args.readme_path, args.exit_on_error)
