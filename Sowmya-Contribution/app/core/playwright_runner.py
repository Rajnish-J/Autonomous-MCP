import asyncio
import tempfile
import subprocess

async def run_test_code(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as f:
        f.write("from playwright.sync_api import sync_playwright\n")
        f.write("def run():\n")
        for line in code.splitlines():
            f.write("    " + line + "\n")
        if "__main__" not in code:
            f.write("\nif __name__ == '__main__':\n")
            f.write("    run()\n")
        f.flush()
        try:
            result = subprocess.run(["python", f.name], capture_output=True, timeout=5000, creationflags=subprocess.CREATE_NEW_CONSOLE)
            # result = subprocess.Popen(
            #     ["python", f.name],
            #     creationflags=subprocess.CREATE_NEW_CONSOLE, 
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.PIPE
            # )
            if result.returncode == 0:
                return "Passed"
            else:
                return result.stderr.decode(errors='ignore')
        except Exception as e:
            return f"Failed: {e}"
