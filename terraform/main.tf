# 1. Kinesis Data Stream (Initial ingestion)
resource "aws_kinesis_stream" "telemetry_stream" {
  name             = "iot-telemetry-stream"
  shard_count      = 1
  retention_period = 24
}

# 2. DynamoDB (Hot path - Current state view)
resource "aws_dynamodb_table" "hot_storage" {
  name           = "iot-device-status"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "device_id"
  attribute { 
    name = "device_id"
    type = "S" 
  }
}

# 3. S3 Bucket (Cold path - Historical data)
resource "aws_s3_bucket" "cold_storage" {
  bucket = "iot-sentinel-archive-julgomezgon"
}

# 4. Kinesis Firehose (The pipeline that moves data from Kinesis to S3)

resource "aws_kinesis_firehose_delivery_stream" "extended_s3_stream" {
  name        = "kinesis-to-s3-history"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.telemetry_stream.arn
    role_arn           = aws_iam_role.firehose_role.arn
  }

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose_role.arn
    bucket_arn = aws_s3_bucket.cold_storage.arn
    # This stores data in date-based folders automatically
    prefix     = "telemetry/year=!{timestamp:YYYY}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
    error_output_prefix = "errors/!{firehose:error-output-type}/!{timestamp:YYYY}/"
  }
}

# 5. IAM Role that allows Firehose to write to S3 and read from Kinesis
resource "aws_iam_role" "firehose_role" {
  name = "firehose_telemetry_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "firehose_inline_policy" {
  name = "firehose_inline_policy"
  role = aws_iam_role.firehose_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetBucketLocation"]
        Resource = ["${aws_s3_bucket.cold_storage.arn}", "${aws_s3_bucket.cold_storage.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["kinesis:GetShardIterator", "kinesis:GetRecords", "kinesis:DescribeStream"]
        Resource = [aws_kinesis_stream.telemetry_stream.arn]
      }
    ]
  })
}


