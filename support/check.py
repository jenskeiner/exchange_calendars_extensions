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


def lint_and_format_snippet(snippet: str) -> tuple[bool, str]:
    """
    Lints and formats a Python code snippet using ruff.
    Returns tuple: (success, formatted_code_or_error_message).
    """
    # Create a temporary file to hold the snippet
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
        tf.write(snippet)
        temp_path = tf.name

    try:
        # First, lint with ruff check --fix for all safe auto-fixes (including import optimization)
        # Ignore E402 (module level import not at top of file) for documentation snippets
        lint_result = subprocess.run(
            ["ruff", "check", "--fix", temp_path],
            capture_output=True,
            text=True,
        )

        if lint_result.returncode != 0:
            error_msg = lint_result.stderr or lint_result.stdout or "Unknown error"
            return False, f"Linting failed: {error_msg}"

        # Then format with ruff format
        format_result = subprocess.run(
            ["ruff", "format", temp_path],
            capture_output=True,
            text=True,
        )

        if format_result.returncode != 0:
            return False, f"Formatting failed: {format_result.stderr}"

        # Read the formatted code back
        with open(temp_path, encoding="utf-8") as f:
            formatted_code = f.read()

        return True, formatted_code

    finally:
        # Clean up temporary file
        os.unlink(temp_path)


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

    # Process snippets in reverse order to avoid line number conflicts when replacing
    for i in range(len(snippets) - 1, -1, -1):
        start_line, end_line, code = snippets[i]
        snippet_num = i + 1
        print(f"\nProcessing snippet {snippet_num} (lines {start_line}-{end_line}):")

        success, error = run_snippet(code)

        if success:
            print("✓ Snippet ran successfully")

            # Lint and format the snippet
            lint_success, formatted_code = lint_and_format_snippet(code)

            if lint_success:
                # Check if the code actually changed
                if formatted_code.strip() != code.strip():
                    print("  → Linting and formatting applied")

                    # Read the entire file
                    with open(readme_path, encoding="utf-8") as f:
                        lines = f.readlines()

                    # Replace the snippet lines with formatted code
                    # Ensure formatted code ends with newline if original did
                    formatted_lines = formatted_code.splitlines(True)
                    if not formatted_lines[-1].endswith("\n") and lines[
                        end_line - 1
                    ].endswith("\n"):
                        formatted_lines[-1] += "\n"
                    elif formatted_lines[-1].endswith("\n") and not lines[
                        end_line - 1
                    ].endswith("\n"):
                        formatted_lines[-1] = formatted_lines[-1].rstrip("\n")

                    # Replace the lines
                    new_lines = (
                        lines[: start_line - 1] + formatted_lines + lines[end_line:]
                    )

                    # Write back to file
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)

                    line_diff = len(formatted_lines) - (end_line - start_line + 1)
                    if line_diff != 0:
                        print(f"  → Line count changed by {line_diff:+d} lines")
                else:
                    print("  → No formatting changes needed")
            else:
                print(f"  → Linting/formating failed: {formatted_code}")
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
