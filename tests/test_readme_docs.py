"""Documentation checks for the install guidance requested in issue #117.

Homebrew's Python is marked as externally managed (PEP 668), so
``pip install pyseoanalyzer`` aborts with ``error: externally-managed-environment``
on those systems. The README must point macOS/Homebrew users at ``pipx`` instead,
while keeping the existing ``pip`` and Docker instructions.
"""

from pathlib import Path

import pytest

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


@pytest.fixture(scope="module")
def readme():
    return README_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def installation(readme):
    """The Installation section, so the guidance lives where users look for it."""
    start = readme.index("\nInstallation\n---")
    end = readme.index("\nCommand-line Usage\n---")
    assert start < end, "README.md has no Installation section before Command-line Usage"
    return readme[start:end]


def test_installation_documents_pipx(installation):
    assert "pipx" in installation
    assert "pipx install pyseoanalyzer" in installation


def test_installation_explains_why_pip_fails(installation):
    assert "externally-managed-environment" in installation
    assert "pep-0668" in installation.lower()


def test_installation_tells_homebrew_users_how_to_get_pipx(installation):
    assert "brew install pipx" in installation
    assert "pipx ensurepath" in installation


def test_installation_shows_command_without_activating_a_venv(installation):
    assert "python-seo-analyzer http://www.domain.com/" in installation
    assert "no virtual environment" in installation


def test_installation_documents_upgrade_and_removal(installation):
    assert "pipx upgrade pyseoanalyzer" in installation
    assert "pipx uninstall pyseoanalyzer" in installation


def test_existing_pip_and_docker_instructions_are_preserved(readme, installation):
    assert "pip install pyseoanalyzer" in installation
    assert "### Docker" in installation
    assert "docker run --rm sethblack/python-seo-analyzer http://example.com/" in readme
