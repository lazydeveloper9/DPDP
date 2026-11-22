import pytest
from pathlib import Path
from cs01.pipeline.stage2_parse.schema_parser import (
    parse_sql_ddl, parse_prisma_schema, parse_sqlalchemy_models, parse_mongoose_schema,
)


def test_parse_sql_ddl(tmp_path: Path):
    sql_file = tmp_path / "schema.sql"
    sql_file.write_text(
        """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            aadhaar_number VARCHAR(12) NOT NULL, -- encrypted KMS
            email VARCHAR(255) NULL -- retention 365 days
        );
        """,
        encoding="utf-8",
    )

    records = parse_sql_ddl(sql_file, "schema.sql")
    assert len(records) == 3

    aadhaar = next(r for r in records if r.column_or_field == "aadhaar_number")
    assert aadhaar.table_or_model.lower() == "users"
    assert aadhaar.is_nullable is False
    assert aadhaar.has_encryption_marker is True

    email = next(r for r in records if r.column_or_field == "email")
    assert email.has_retention_comment is True


def test_parse_prisma_schema(tmp_path: Path):
    prisma_file = tmp_path / "schema.prisma"
    prisma_file.write_text(
        """
        model User {
            id      Int     @id @default(autoincrement())
            pan     String  @encrypted
            phone   String? // retention 180 days
        }
        """,
        encoding="utf-8",
    )

    records = parse_prisma_schema(prisma_file, "schema.prisma")
    assert len(records) == 3

    pan = next(r for r in records if r.column_or_field == "pan")
    assert pan.table_or_model == "User"
    assert pan.has_encryption_marker is True
    assert pan.is_nullable is False

    phone = next(r for r in records if r.column_or_field == "phone")
    assert phone.is_nullable is True
    assert phone.has_retention_comment is True


def test_parse_sqlalchemy_models(tmp_path: Path):
    py_file = tmp_path / "models.py"
    py_file.write_text(
        """
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    aadhaar = Column(String(12), nullable=False, encrypt=True)
    dob = Column(Date, nullable=True)
        """,
        encoding="utf-8",
    )

    records = parse_sqlalchemy_models(py_file, "models.py")
    assert len(records) == 3

    aadhaar = next(r for r in records if r.column_or_field == "aadhaar")
    assert aadhaar.table_or_model == "Customer"
    assert aadhaar.is_nullable is False
    assert aadhaar.has_encryption_marker is True


def test_parse_mongoose_schema(tmp_path: Path):
    js_file = tmp_path / "user.js"
    js_file.write_text(
        """
const UserSchema = new mongoose.Schema({
    passport: { type: String, encrypted: true },
    mobile: String
});
        """,
        encoding="utf-8",
    )

    records = parse_mongoose_schema(js_file, "user.js")
    assert len(records) == 2

    passport = next(r for r in records if r.column_or_field == "passport")
    assert passport.table_or_model == "UserSchema"
    assert passport.has_encryption_marker is True
