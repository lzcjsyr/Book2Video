import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_video_composer_does_not_import_process_level_media_modules():
    composer_path = REPO_ROOT / "core" / "domain" / "composer.py"
    tree = ast.parse(composer_path.read_text(encoding="utf-8"))
    imported_roots = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "subprocess" not in imported_roots
    assert "shutil" not in imported_roots
