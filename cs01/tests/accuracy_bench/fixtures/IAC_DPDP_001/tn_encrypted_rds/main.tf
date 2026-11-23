resource "aws_db_instance" "users_prod" {
  allocated_storage    = 20
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  storage_encrypted    = true
  publicly_accessible  = false
}
