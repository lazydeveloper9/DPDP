import pytest
from pathlib import Path
from cs01.pipeline.stage2_parse.env_parser import parse_env_file, parse_json_config
from cs01.utils import sha256_of


def test_parse_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Database Credentials\n"
        "DB_PASSWORD=super_secret_pass_12345678901234567\n"
        "APP_ENV=production\n"
        "API_KEY=xyz987654321012345678901234567890\n",
        encoding="utf-8",
    )

    records = parse_env_file(env_file, ".env")
    assert len(records) == 3

    pwd_record = next(r for r in records if r.key == "DB_PASSWORD")
    assert pwd_record.value_sha256 == sha256_of("super_secret_pass_12345678901234567")
    assert pwd_record.is_potential_secret is True
    assert pwd_record.line == 2

    # Verify zero-leak: raw secret is not stored
    assert not hasattr(pwd_record, "value")


def test_parse_json_config(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        '{"db": {"host": "localhost", "secret_token": "token123456789012345678901234"}}',
        encoding="utf-8",
    )

    records = parse_json_config(cfg_file, "config.json")
    assert len(records) == 2

    token_rec = next(r for r in records if r.key == "db.secret_token")
    assert token_rec.is_potential_secret is True
    assert token_rec.value_sha256 == sha256_of("token123456789012345678901234")
