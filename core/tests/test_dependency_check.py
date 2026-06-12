from pathlib import Path

from core.dependency_check import DependencyChecker


def _write_hyperframes_skill_bundle(repo_root: Path) -> None:
    required = {
        "hyperframes": (
            "SKILL.md",
            "house-style.md",
            "data-in-motion.md",
            "visual-styles.md",
            "references/motion-principles.md",
            "references/video-composition.md",
            "references/typography.md",
        ),
        "hyperframes-cli": ("SKILL.md",),
        "gsap": ("SKILL.md",),
        "css-animations": ("SKILL.md",),
    }
    for skill_name, rel_paths in required.items():
        for rel_path in rel_paths:
            path = repo_root / "skills" / "step4" / skill_name / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(skill_name, encoding="utf-8")


def test_dependency_checker_reports_missing_runtime_and_hyperframes_dependencies(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / ".env.example").write_text("MIMO_API_KEY=\n", encoding="utf-8")
    hyperframes_app = repo_root / "core" / "infra" / "hyperframes" / "app"
    hyperframes_app.mkdir(parents=True)
    (hyperframes_app / "package.json").write_text("{}", encoding="utf-8")
    (repo_root / "pyproject.toml").write_text('dependencies = ["requests>=2"]\n', encoding="utf-8")

    checker = DependencyChecker(
        repo_root=repo_root,
        which=lambda _name: None,
        import_checker=lambda _name: False,
        python_version=(3, 9, 0),
    )

    report = checker.check()

    failed_names = {item.name for item in report.items if not item.ok}
    assert "Python" in failed_names
    assert "FFmpeg" in failed_names
    assert "Node.js" in failed_names
    assert "npm" in failed_names
    assert "HyperFrames template" in failed_names
    assert "HyperFrames embedded skills" in failed_names
    assert "Python packages" in failed_names
    assert "Environment file" in failed_names
    assert not report.ok


def test_dependency_checker_passes_when_core_dependencies_are_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / ".env").write_text("MIMO_API_KEY=test\n", encoding="utf-8")
    (repo_root / ".env.example").write_text("MIMO_API_KEY=\n", encoding="utf-8")
    (repo_root / "input").mkdir()
    (repo_root / "music").mkdir()
    hyperframes_app = repo_root / "core" / "infra" / "hyperframes" / "app"
    hyperframes_app.mkdir(parents=True)
    (hyperframes_app / "package.json").write_text("{}", encoding="utf-8")
    (hyperframes_app / "index.html").write_text("<html></html>", encoding="utf-8")
    _write_hyperframes_skill_bundle(repo_root)
    (repo_root / "pyproject.toml").write_text('dependencies = ["requests>=2", "python-dotenv>=1"]\n', encoding="utf-8")

    checker = DependencyChecker(
        repo_root=repo_root,
        which=lambda name: f"/fake/bin/{name}",
        import_checker=lambda _name: True,
        python_version=(3, 13, 0),
    )

    report = checker.check()

    assert report.ok
    assert all(item.ok for item in report.items)


def test_dependency_checker_can_require_configured_api_keys(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / ".env").write_text("", encoding="utf-8")
    (repo_root / ".env.example").write_text("", encoding="utf-8")
    (repo_root / "input").mkdir()
    (repo_root / "music").mkdir()
    hyperframes_app = repo_root / "core" / "infra" / "hyperframes" / "app"
    hyperframes_app.mkdir(parents=True)
    (hyperframes_app / "package.json").write_text("{}", encoding="utf-8")
    (hyperframes_app / "index.html").write_text("<html></html>", encoding="utf-8")
    _write_hyperframes_skill_bundle(repo_root)
    (repo_root / "pyproject.toml").write_text('dependencies = []\n', encoding="utf-8")

    from core.dependency_check import PROVIDER_KEY_GROUPS
    for keys in PROVIDER_KEY_GROUPS.values():
        for key in keys:
            monkeypatch.setenv(key, "")

    checker = DependencyChecker(
        repo_root=repo_root,
        which=lambda name: f"/fake/bin/{name}",
        import_checker=lambda _name: True,
        python_version=(3, 13, 0),
    )

    report = checker.check(require_api_keys=True)

    assert any(item.name == "API keys" and not item.ok for item in report.items)
