import pytest
from pathlib import Path
from cs01.models import FileRecord, Bucket
from cs01.pipeline.stage1_ingest.stack_signatures import detect_stacks


def test_detect_express_stack(tmp_path: Path):
    pkg_json = tmp_path / "package.json"
    pkg_json.write_text('{"dependencies": {"express": "^4.18.2", "mongoose": "^7.0.0"}}', encoding="utf-8")

    files = [
        FileRecord(path="package.json", bucket=Bucket.BACKEND),
        FileRecord(path="src/index.js", bucket=Bucket.BACKEND),
    ]

    stacks = detect_stacks(str(tmp_path), files)
    assert len(stacks) >= 1
    express_stack = next((s for s in stacks if s.framework == "express"), None)
    assert express_stack is not None
    assert express_stack.language == "javascript"
    assert express_stack.orm_type == "mongoose"


def test_detect_fastapi_stack(tmp_path: Path):
    req_txt = tmp_path / "requirements.txt"
    req_txt.write_text("fastapi==0.100.0\nuvicorn==0.23.0\nsqlalchemy>=2.0.0", encoding="utf-8")

    files = [
        FileRecord(path="requirements.txt", bucket=Bucket.BACKEND),
        FileRecord(path="main.py", bucket=Bucket.BACKEND),
    ]

    stacks = detect_stacks(str(tmp_path), files)
    assert len(stacks) >= 1
    fastapi_stack = next((s for s in stacks if s.framework == "fastapi"), None)
    assert fastapi_stack is not None
    assert fastapi_stack.language == "python"
    assert fastapi_stack.orm_type == "sqlalchemy"


def test_detect_spring_stack(tmp_path: Path):
    pom_xml = tmp_path / "pom.xml"
    pom_xml.write_text('<project><dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>', encoding="utf-8")

    files = [
        FileRecord(path="pom.xml", bucket=Bucket.BACKEND),
        FileRecord(path="src/main/java/App.java", bucket=Bucket.BACKEND),
    ]

    stacks = detect_stacks(str(tmp_path), files)
    assert len(stacks) >= 1
    spring_stack = next((s for s in stacks if s.framework == "spring_boot"), None)
    assert spring_stack is not None
    assert spring_stack.language == "java"
