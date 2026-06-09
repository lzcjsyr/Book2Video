import json
import subprocess
import wave
from pathlib import Path

from core.infra.project_paths import ProjectPaths


def _write_wav(path: Path, *, seconds: float) -> None:
    frame_rate = 8000
    frame_count = int(frame_rate * seconds)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(frame_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


def _write_project(project_dir: Path) -> ProjectPaths:
    paths = ProjectPaths(str(project_dir))
    paths.ensure_dirs_exist()
    Path(paths.script_json()).write_text(
        json.dumps(
            {
                "actual_segments": 1,
                "segments": [{"index": 1, "content": "收入同比增长30%，利润承压。", "title": "增长与压力"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _write_wav(Path(paths.voice) / "voice_1.wav", seconds=0.75)
    return paths


def test_embedded_hyperframes_skill_loader_uses_core_resources():
    from core.infra.hyperframes.skill_loader import (
        embedded_hyperframes_skill_dir,
        load_embedded_hyperframes_skill_bundle,
        step4_hyperframes_skill_dirs,
    )

    bundle = load_embedded_hyperframes_skill_bundle()
    skill_dirs = step4_hyperframes_skill_dirs()

    assert "HyperFrames" in bundle
    assert "Layout Before Animation" in bundle
    assert "HyperFrames CLI" in bundle
    assert "GSAP" in bundle
    assert "CSS" in bundle
    assert ".agents/skills" not in bundle
    assert embedded_hyperframes_skill_dir().as_posix().endswith("skills/step4/hyperframes")
    assert [path.name for path in skill_dirs] == [
        "hyperframes",
        "hyperframes-cli",
        "gsap",
        "css-animations",
    ]


def test_segment_renderer_uses_audio_duration_and_render_command(monkeypatch, tmp_path):
    from core.infra.hyperframes import segment_renderer

    paths = _write_project(tmp_path / "project")
    commands = []
    agent_inputs = []

    def fake_agent_runner(**kwargs):
        agent_inputs.append(kwargs)
        work_dir = Path(kwargs["work_dir"])
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "index.html").write_text("<html><body>segment</body></html>", encoding="utf-8")

    def fake_run(command, cwd, check, stdin, stdout, stderr, text, timeout):
        commands.append({"command": command, "cwd": cwd, "check": check, "text": text})
        output_path = Path(command[command.index("--output") + 1])
        assert output_path.is_absolute()
        output_path.write_bytes(b"video")
        return subprocess.CompletedProcess(command, 0, stdout="ok")

    monkeypatch.setattr(segment_renderer, "run_step4_hyperframes_agent", fake_agent_runner)
    monkeypatch.setattr(segment_renderer.subprocess, "run", fake_run)

    result = segment_renderer.render_hyperframes_segments_with_agent(
        project_output_dir=str(tmp_path / "project"),
        script_data=json.loads(Path(paths.script_json()).read_text(encoding="utf-8")),
        image_size="1280x720",
        output_dir=paths.images,
        target_segments=[1],
        keywords_data={"segments": [{"index": 1, "keywords": ["增长"]}]},
        description_data=None,
        style_preset="data_driven",
        max_turns=7,
        render_fps=60,
        concurrency=1,
        session_log_path=str(Path(paths.text) / "_step4_hyperframes_agent_session.jsonl"),
        repo_root=str(tmp_path),
        llm_server="siliconflow",
        llm_model="step4-model",
        llm_base_url="https://llm-gateway.example.test/anthropic",
    )

    assert result["failed_segments"] == []
    assert result["processed_segments"] == [1]
    assert result["image_paths"] == [str(Path(paths.images) / "segment_1.mp4")]
    assert Path(result["image_paths"][0]).exists()
    assert agent_inputs[0]["duration_seconds"] == 0.75
    assert agent_inputs[0]["style_preset"] == "data_driven"
    assert agent_inputs[0]["llm_server"] == "siliconflow"
    assert agent_inputs[0]["llm_model"] == "step4-model"
    assert agent_inputs[0]["llm_base_url"] == "https://llm-gateway.example.test/anthropic"
    assert commands[0]["command"][:4] == ["npx", "--yes", "hyperframes@0.6.84", "render"]
    assert "--fps" in commands[0]["command"]
    assert "60" in commands[0]["command"]
    assert commands[0]["cwd"] == Path(paths.images) / "hyperframes" / "segment_1"


def test_segment_renderer_uses_absolute_render_output_when_project_path_is_relative(
    monkeypatch, tmp_path
):
    from core.infra.hyperframes import segment_renderer

    monkeypatch.chdir(tmp_path)
    paths = _write_project(Path("project"))
    commands = []

    def fake_agent_runner(**kwargs):
        work_dir = Path(kwargs["work_dir"])
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    def fake_run(command, cwd, check, stdin, stdout, stderr, text, timeout):
        commands.append({"command": command, "cwd": cwd})
        output_path = Path(command[command.index("--output") + 1])
        assert output_path.is_absolute()
        output_path.write_bytes(b"video")
        return subprocess.CompletedProcess(command, 0, stdout="ok")

    monkeypatch.setattr(segment_renderer, "run_step4_hyperframes_agent", fake_agent_runner)
    monkeypatch.setattr(segment_renderer.subprocess, "run", fake_run)

    result = segment_renderer.render_hyperframes_segments_with_agent(
        project_output_dir="project",
        script_data=json.loads(Path(paths.script_json()).read_text(encoding="utf-8")),
        image_size="1280x720",
        output_dir=paths.images,
        target_segments=[1],
        keywords_data=None,
        description_data=None,
        style_preset="data_driven",
        max_turns=7,
        render_fps=30,
        concurrency=1,
        session_log_path=str(Path(paths.text) / "_step4_hyperframes_agent_session.jsonl"),
        repo_root=str(tmp_path),
    )

    assert result["failed_segments"] == []
    assert Path(result["image_paths"][0]).exists()
    assert Path(result["image_paths"][0]) == (tmp_path / "project/images/segment_1.mp4")
    assert commands[0]["cwd"] == Path("project/images/hyperframes/segment_1")


def test_segment_renderer_records_render_log_on_failure(monkeypatch, tmp_path):
    from core.infra.hyperframes import segment_renderer

    paths = _write_project(tmp_path / "project")

    def fake_agent_runner(**kwargs):
        work_dir = Path(kwargs["work_dir"])
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    def fake_run(command, cwd, check, stdin, stdout, stderr, text, timeout):
        raise subprocess.CalledProcessError(1, command, output="render failed")

    monkeypatch.setattr(segment_renderer, "run_step4_hyperframes_agent", fake_agent_runner)
    monkeypatch.setattr(segment_renderer.subprocess, "run", fake_run)

    result = segment_renderer.render_hyperframes_segments_with_agent(
        project_output_dir=str(tmp_path / "project"),
        script_data=json.loads(Path(paths.script_json()).read_text(encoding="utf-8")),
        image_size="1280x720",
        output_dir=paths.images,
        target_segments=[1],
        keywords_data=None,
        description_data=None,
        style_preset="data_driven",
        max_turns=7,
        render_fps=30,
        concurrency=1,
        session_log_path=str(Path(paths.text) / "_step4_hyperframes_agent_session.jsonl"),
        repo_root=str(tmp_path),
    )

    log_path = Path(paths.images) / "hyperframes" / "segment_1" / "render.log"
    assert result["failed_segments"] == [1]
    assert "render failed" in log_path.read_text(encoding="utf-8")


def test_segment_renderer_records_render_log_on_timeout(monkeypatch, tmp_path):
    from core.infra.hyperframes import segment_renderer

    paths = _write_project(tmp_path / "project")

    def fake_agent_runner(**kwargs):
        work_dir = Path(kwargs["work_dir"])
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    def fake_run(command, cwd, check, stdin, stdout, stderr, text, timeout):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(segment_renderer, "run_step4_hyperframes_agent", fake_agent_runner)
    monkeypatch.setattr(segment_renderer.subprocess, "run", fake_run)

    result = segment_renderer.render_hyperframes_segments_with_agent(
        project_output_dir=str(tmp_path / "project"),
        script_data=json.loads(Path(paths.script_json()).read_text(encoding="utf-8")),
        image_size="1280x720",
        output_dir=paths.images,
        target_segments=[1],
        keywords_data=None,
        description_data=None,
        style_preset="data_driven",
        max_turns=7,
        render_fps=30,
        concurrency=1,
        session_log_path=str(Path(paths.text) / "_step4_hyperframes_agent_session.jsonl"),
        repo_root=str(tmp_path),
    )

    log_path = Path(paths.images) / "hyperframes" / "segment_1" / "render.log"
    assert result["failed_segments"] == [1]
    assert "渲染超时" in log_path.read_text(encoding="utf-8")
