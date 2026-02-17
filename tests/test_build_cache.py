import json


def test_build_fingerprint_changes_with_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "content").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "static").mkdir()
    (tmp_path / "pages").mkdir()
    (tmp_path / "site_config.yaml").write_text("site_name: Test\n", encoding="utf-8")
    (tmp_path / "authors.yaml").write_text("authors: []\n", encoding="utf-8")

    from generator import generate as gen

    fp1 = gen.compute_build_fingerprint()
    (tmp_path / "content" / "chapter.md").write_text("hello", encoding="utf-8")
    fp2 = gen.compute_build_fingerprint()

    assert fp1 != fp2


def test_build_cache_persist_and_match(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    from generator import generate as gen

    monkeypatch.setattr(gen, "BUILD_DIR", str(build_dir))
    monkeypatch.setattr(gen, "BUILD_CACHE_FILE", str(build_dir / ".build_cache.json"))

    fp = "abc123"
    gen.persist_build_fingerprint(fp)

    cache_path = build_dir / ".build_cache.json"
    assert cache_path.exists()
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert payload["fingerprint"] == fp
    assert gen.should_skip_build(fp)
    assert not gen.should_skip_build("different")
