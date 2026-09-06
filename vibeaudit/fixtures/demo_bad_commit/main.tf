resource "aws_security_group" "bad" {
  name = "bad-sg"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "bad" {
  bucket = "vibeaudit-demo-bad-bucket"
  acl    = "public-read"
}
