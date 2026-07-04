from __future__ import annotations

from pathlib import Path

from src.cli import build_parser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_current_status_doc_exists_and_defines_mvp_1_boundary():
    content = (PROJECT_ROOT / "docs" / "00-当前实现状态.md").read_text(encoding="utf-8")

    assert "已实现能力" in content
    assert "未实现能力" in content
    assert "当前 MVP-1 开发目标" in content
    assert "PubMed 按关键词获取摘要" in content
    assert "MVP-1 不要求自动全文下载" in content
    assert "WebUI 审核工作台" in content


def test_readme_current_commands_match_cli_parser():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    parser = build_parser()

    documented_commands = {
        "python -m src.cli init db": ["init", "db"],
        "python -m src.cli status summary": ["status", "summary"],
        "python -m src.cli status keywords": ["status", "keywords"],
        'python -m src.cli collect abstracts --source pubmed --query "genOway[Affiliation] AND (mouse OR mice OR model)" --limit 20': [
            "collect",
            "abstracts",
            "--source",
            "pubmed",
            "--query",
            "genOway[Affiliation] AND (mouse OR mice OR model)",
            "--limit",
            "20",
        ],
        "python -m src.cli report simple --format csv": ["report", "simple", "--format", "csv"],
        "python -m src.cli report simple --format markdown": [
            "report",
            "simple",
            "--format",
            "markdown",
        ],
        "python -m src.cli report evidence --format csv": ["report", "evidence", "--format", "csv"],
    }
    for documented, argv in documented_commands.items():
        assert documented in readme
        parser.parse_args(argv)

    assert "当前代码只支持以下命令" in readme
