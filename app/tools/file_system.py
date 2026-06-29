import os
import shutil
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger("tools.file_system")

WORKSPACE = Path(os.path.abspath("./workspace"))


class FileSystem:
    """
    Safe file operations confined to the ./workspace directory.
    Any attempt to escape the workspace raises ValueError.
    """

    def __init__(self, workspace: Path = WORKSPACE) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _safe(self, path: str) -> Path:
        full = (self.workspace / path).resolve()
        if not str(full).startswith(str(self.workspace.resolve())):
            raise ValueError(f"Path '{path}' escapes workspace")
        return full

    def read(self, path: str) -> Dict[str, Any]:
        try:
            p = self._safe(path)
            if not p.exists():
                return {"success": False, "error": f"Not found: {path}"}
            return {"success": True, "path": path, "content": p.read_text(encoding="utf-8"), "size_bytes": p.stat().st_size}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def write(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        try:
            p = self._safe(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": path, "bytes_written": len(content.encode()), "mode": "append" if append else "write"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        try:
            p = self._safe(path)
            if not p.exists():
                return {"success": False, "error": f"Not found: {path}"}
            items = [
                {"name": item.name, "type": "dir" if item.is_dir() else "file", "size_bytes": item.stat().st_size if item.is_file() else None}
                for item in sorted(p.iterdir())
            ]
            return {"success": True, "path": path, "items": items}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def delete(self, path: str) -> Dict[str, Any]:
        try:
            p = self._safe(path)
            if not p.exists():
                return {"success": False, "error": f"Not found: {path}"}
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            return {"success": True, "deleted": path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def exists(self, path: str) -> bool:
        try:
            return self._safe(path).exists()
        except Exception:
            return False


file_system = FileSystem()
