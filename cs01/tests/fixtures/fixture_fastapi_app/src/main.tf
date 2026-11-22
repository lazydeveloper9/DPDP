# Violation: Storage unencrypted on database instance (IAC-DPDP-001)
resource "aws_db_instance" "app_db" {
  allocated_storage = 20
  storage_encrypted = false
  instance_class    = "db.t3.micro"
}
