import shutil
import tarfile

import pytest

from scripts import package


def names(tgz):
    with tarfile.open(tgz) as tar:
        return tar.getnames()


def test_build_packages_the_app_under_one_top_folder(tmp_path):
    got = names(package.build(out=tmp_path / "stackwatch.tgz"))
    assert "stackwatch/default/app.conf" in got
    assert "stackwatch/lookups/stackwatch_plans.csv" in got
    assert all(n == "stackwatch" or n.startswith("stackwatch/") for n in got)


def test_build_skips_local_and_junk_files(tmp_path):
    app = tmp_path / "stackwatch"
    shutil.copytree(package.APP, app)
    (app / ".DS_Store").write_text("x")
    (app / "local").mkdir()
    (app / "local" / "app.conf").write_text("x")
    got = names(package.build(app=app, out=tmp_path / "out.tgz"))
    assert not any(".DS_Store" in n or "/local" in n for n in got)


def test_build_fails_clearly_when_app_incomplete(tmp_path):
    with pytest.raises(FileNotFoundError, match="default/app.conf"):
        package.build(app=tmp_path, out=tmp_path / "x.tgz")
