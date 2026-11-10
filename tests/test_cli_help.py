"""The --no-follow-links flag disables following inner links, so its
--help text must say that (it previously described the opposite)."""

import sys

import pytest

from pyseoanalyzer.__main__ import main


def test_no_follow_links_help_text(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["python-seo-analyzer", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Do not follow inner links" in out
    assert "Analyze all the existing inner links" not in out


def test_no_follow_links_flag_disables_following(monkeypatch):
    import argparse

    captured = {}

    def fake_analyze(site, sitemap, **kwargs):
        captured.update(kwargs)
        return {"pages": []}

    monkeypatch.setattr("pyseoanalyzer.__main__.analyze", fake_analyze)
    monkeypatch.setattr(
        sys, "argv", ["python-seo-analyzer", "--no-follow-links", "http://x/"]
    )
    main()
    assert captured["follow_links"] is False
