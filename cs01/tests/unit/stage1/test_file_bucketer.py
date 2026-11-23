import pytest
from pathlib import Path
from cs01.pipeline.stage1_ingest.bucket_patterns import classify_bucket
from cs01.models import Bucket

def test_secrets_bucket():
    bucket, extra = classify_bucket(".env", ".env", ".env")
    assert bucket == Bucket.SECRETS

    bucket, extra = classify_bucket("config/.env.local", ".env.local", ".local")
    assert bucket == Bucket.SECRETS

    bucket, extra = classify_bucket("certs/server.key", "server.key", ".key")
    assert bucket == Bucket.SECRETS

def test_db_schema_bucket():
    bucket, extra = classify_bucket("migrations/001_init.sql", "001_init.sql", ".sql")
    assert bucket == Bucket.DB_SCHEMA

    bucket, extra = classify_bucket("prisma/schema.prisma", "schema.prisma", ".prisma")
    assert bucket == Bucket.DB_SCHEMA

    bucket, extra = classify_bucket("src/models/user.py", "user.py", ".py")
    assert bucket == Bucket.DB_SCHEMA

def test_infra_bucket():
    bucket, extra = classify_bucket("terraform/main.tf", "main.tf", ".tf")
    assert bucket == Bucket.INFRA

    bucket, extra = classify_bucket("Dockerfile", "Dockerfile", "")
    assert bucket == Bucket.INFRA

    bucket, extra = classify_bucket("k8s/deployment.yaml", "deployment.yaml", ".yaml")
    assert bucket == Bucket.INFRA

def test_frontend_bucket():
    bucket, extra = classify_bucket("src/components/Header.tsx", "Header.tsx", ".tsx")
    assert bucket == Bucket.FRONTEND

    bucket, extra = classify_bucket("public/index.html", "index.html", ".html")
    assert bucket == Bucket.FRONTEND

def test_backend_bucket():
    bucket, extra = classify_bucket("src/routes/api.py", "api.py", ".py")
    assert bucket == Bucket.BACKEND

    bucket, extra = classify_bucket("src/controllers/auth.go", "auth.go", ".go")
    assert bucket == Bucket.BACKEND

def test_dual_bucket_assignment():
    bucket, extra = classify_bucket("src/components/Form.js", "Form.js", ".js")
    assert bucket == Bucket.BACKEND or bucket == Bucket.FRONTEND
    assert (Bucket.FRONTEND in extra) or (Bucket.BACKEND in extra)

    bucket, extra = classify_bucket("src/pages/api/login.ts", "login.ts", ".ts")
    assert bucket == Bucket.BACKEND
    assert Bucket.FRONTEND in extra
