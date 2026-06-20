from __future__ import annotations

from pathlib import Path


STEP4_HYPERFRAMES_SKILL_DIR_NAMES = (
    "hyperframes",
    "hyperframes-core",
    "hyperframes-animation",
    "hyperframes-creative",
    "hyperframes-cli",
    "hyperframes-media",
    "hyperframes-registry",
    "general-video",
)

EMBEDDED_SKILL_FILES = (
    "hyperframes/SKILL.md",
    "hyperframes-core/SKILL.md",
    "hyperframes-core/references/minimal-composition.md",
    "hyperframes-core/references/data-attributes.md",
    "hyperframes-core/references/determinism-rules.md",
    "hyperframes-animation/SKILL.md",
    "hyperframes-animation/adapters/gsap.md",
    "hyperframes-animation/adapters/css-animations.md",
    "hyperframes-creative/SKILL.md",
    "hyperframes-cli/SKILL.md",
    "hyperframes-media/SKILL.md",
    "hyperframes-registry/SKILL.md",
    "general-video/SKILL.md",
)


def embedded_hyperframes_skill_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "skills" / "step4" / "hyperframes"


def step4_hyperframes_skills_root() -> Path:
    return Path(__file__).resolve().parents[3] / "skills" / "step4"


def step4_hyperframes_skill_dirs(skills_root: str | Path | None = None) -> list[Path]:
    root = Path(skills_root) if skills_root else step4_hyperframes_skills_root()
    return [root / name for name in STEP4_HYPERFRAMES_SKILL_DIR_NAMES]


def load_embedded_hyperframes_skill_bundle(skill_dir: str | Path | None = None) -> str:
    base_dir = Path(skill_dir).parent if skill_dir else step4_hyperframes_skills_root()
    sections: list[str] = []
    for relative_path in EMBEDDED_SKILL_FILES:
        path = base_dir / relative_path
        if not path.exists():
            raise FileNotFoundError(f"缺少内置 HyperFrames skill 文件: {path}")
        content = path.read_text(encoding="utf-8").strip()
        sections.append(f"<!-- {relative_path} -->\n{content}")
    return "\n\n".join(sections)
