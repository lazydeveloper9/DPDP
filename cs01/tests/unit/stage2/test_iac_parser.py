import pytest
from pathlib import Path
from cs01.pipeline.stage2_parse.iac_parser import (
    parse_terraform_file, parse_kubernetes_yaml, parse_dockerfile,
)


def test_parse_terraform_file(tmp_path: Path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text(
        """
resource "aws_db_instance" "default" {
  allocated_storage = 10
  storage_encrypted = false
  instance_class    = "db.t3.micro"
}

resource "aws_s3_bucket" "pii_bucket" {
  bucket = "my-pii-data-bucket"
}
        """,
        encoding="utf-8",
    )

    trees = parse_terraform_file(tf_file, "main.tf")
    assert len(trees) == 2

    db = next(t for t in trees if t.resource_type == "aws_db_instance")
    assert db.resource_name == "default"
    assert db.attributes.get("storage_encrypted") is False
    assert db.line_map.get("__self__") == 2


def test_parse_kubernetes_yaml(tmp_path: Path):
    k8s_file = tmp_path / "deploy.yaml"
    k8s_file.write_text(
        """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 2
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_MODE: "production"
        """,
        encoding="utf-8",
    )

    trees = parse_kubernetes_yaml(k8s_file, "deploy.yaml")
    assert len(trees) == 2
    assert trees[0].resource_type == "Deployment"
    assert trees[0].resource_name == "api-service"
    assert trees[1].resource_type == "ConfigMap"
    assert trees[1].resource_name == "app-config"


def test_parse_dockerfile(tmp_path: Path):
    df_file = tmp_path / "Dockerfile"
    df_file.write_text(
        """
FROM python:3.11-slim
ENV PORT=8080
ENV APP_SECRET=raw_secret_value
ARG BUILD_ID=123
        """,
        encoding="utf-8",
    )

    trees = parse_dockerfile(df_file, "Dockerfile")
    assert len(trees) == 1
    tree = trees[0]
    assert tree.file_type == "dockerfile"
    assert tree.attributes["envs"]["PORT"] == "8080"
    assert tree.attributes["envs"]["APP_SECRET"] == "raw_secret_value"
    assert tree.attributes["args"]["BUILD_ID"] == "123"
