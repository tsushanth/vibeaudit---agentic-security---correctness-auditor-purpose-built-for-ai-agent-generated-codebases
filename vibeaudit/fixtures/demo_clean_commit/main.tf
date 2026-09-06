resource "aws_security_group" "good" {
  name = "good-sg"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_s3_bucket" "good" {
  bucket = "vibeaudit-demo-good-bucket"
  acl    = "private"
}
