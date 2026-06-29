import os
import sys
import subprocess
import tempfile
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger("tools.code_runner")


class CodeRunner:
    """
    Safe Python code execution via subprocess.
    Runs code in an isolated temp file; captures stdout/stderr.
    """

    TIMEOUT = 30
    MAX_OUTPUT = 10_000

    def run(self, code: str, language: str = "python") -> Dict[str, Any]:
        if language != "python":
            return {"success": False, "error": f"Unsupported language: {language}", "output": ""}
        return self._run_python(code)

    def _run_python(self, code: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp = f.name
        try:
            proc = subprocess.run(
                [sys.executable, tmp],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            stdout = proc.stdout[: self.MAX_OUTPUT]
            stderr = proc.stderr[: self.MAX_OUTPUT]
            ok = proc.returncode == 0
            return {
                "success": ok,
                "output": stdout,
                "error": stderr if not ok else "",
                "warnings": stderr if ok and stderr else "",
                "return_code": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Timed out after {self.TIMEOUT}s", "return_code": -1}
        except Exception as exc:
            return {"success": False, "output": "", "error": str(exc), "return_code": -1}
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    def syntax_check(self, code: str) -> Dict[str, Any]:
        try:
            compile(code, "<string>", "exec")
            return {"valid": True, "error": None}
        except SyntaxError as exc:
            return {"valid": False, "error": str(exc)}


code_runner = CodeRunner()
