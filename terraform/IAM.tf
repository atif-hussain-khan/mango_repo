# IAM Role for all Lambda Functions
resource "aws_iam_role" "lambda_role" {
    name = "${var.group_name}_lambda_role"
    description = "this role is for the extract, transform and load lambda functions"
    assume_role_policy = <<EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sts:AssumeRole"
                ],
                "Principal": {
                    "Service": [
                        "lambda.amazonaws.com"
                    ]
                }
            }
        ]
    }
    EOF
}

/*
The policy setup for each of the services below follows the following patter:
  aws_iam_policy_document - create a document that defines permission and resources for the service
  aws_iam_policy - using the policy document, create a policy resource for the service
  aws_iam_role_policy_attachment - attach the policy resource for the service to the lambda role
*/

# SecretsManager Policy

data "aws_iam_policy_document" "sm_document" {
  # Allow the getting of secret values from the specified SecretManager resrouces
  statement {

    actions = ["secretsmanager:GetSecretValue"]

    resources = [
      "${var.db_secrets_arn}",
      "${var.table_names_secrets_arn}"
    ]
  }
}

resource "aws_iam_policy" "sm_policy_resource" {
    name = "sm_policy"
    policy = data.aws_iam_policy_document.sm_document.json
}

resource "aws_iam_role_policy_attachment" "sm_policy_attachment" {
    role = aws_iam_role.lambda_role.name
    policy_arn = aws_iam_policy.sm_policy_resource.arn
}

# S3 Policy

data "aws_iam_policy_document" "s3_document" {
  # Allow the uploading and downloading of an object, and listing of buckets from the S3 resources
  statement {

    actions = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]

    resources = [
      "${aws_s3_bucket.ingestion_zone.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_policy_resource" {
    name = "s3_policy"
    policy = data.aws_iam_policy_document.s3_document.json
}

resource "aws_iam_role_policy_attachment" "lambda_s3_policy_attachment" {
    role = aws_iam_role.lambda_role.name
    policy_arn = aws_iam_policy.s3_policy.arn
}


# Cloudwatch Policy

data "aws_iam_policy_document" "cw_document" {
  # Allow the creation of a log group inside the specified account
  statement {

    actions = [ "logs:CreateLogGroup" ]

    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
    ]
  }
  
  # Allow the creation of a log stream and put log events in the specified log group  
  statement {

    actions = [ "logs:CreateLogStream", "logs:PutLogEvents" ]

    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.extract_lambda_name}:*"
    ]
  }
}

resource "aws_iam_policy" "cw_policy_resource" {
    name = "cw_policy"
    policy = data.aws_iam_policy_document.cw_document.json
}

resource "aws_iam_role_policy_attachment" "lambda_cw_policy_attachment" {
    role = aws_iam_role.lambda_role.name
    policy_arn = aws_iam_policy.cw_policy_resource.arn
}