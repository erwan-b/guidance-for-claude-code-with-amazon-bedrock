"""Tests for AWS utility helpers."""

from botocore.exceptions import ClientError

from claude_code_with_bedrock.cli.utils.aws import check_s3_bucket_exists, get_stack_outputs


def test_get_stack_outputs_returns_outputs(monkeypatch):
    """Stack outputs should be converted into a simple dict."""

    class FakeClient:
        def describe_stacks(self, StackName):
            assert StackName == "demo-stack"
            return {
                "Stacks": [
                    {
                        "Outputs": [
                            {"OutputKey": "BucketName", "OutputValue": "demo-bucket"},
                            {"OutputKey": "RoleArn", "OutputValue": "arn:aws:iam::123456789012:role/demo"},
                        ]
                    }
                ]
            }

    monkeypatch.setattr("claude_code_with_bedrock.cli.utils.aws.boto3.client", lambda *args, **kwargs: FakeClient())

    outputs = get_stack_outputs("demo-stack", "eu-west-3")

    assert outputs == {
        "BucketName": "demo-bucket",
        "RoleArn": "arn:aws:iam::123456789012:role/demo",
    }


def test_get_stack_outputs_missing_stack_is_quiet(monkeypatch, capsys):
    """Missing optional stacks should not print errors."""

    class FakeClient:
        def describe_stacks(self, StackName):
            raise ClientError(
                {"Error": {"Code": "ValidationError", "Message": f"Stack with id {StackName} does not exist"}},
                "DescribeStacks",
            )

    monkeypatch.setattr("claude_code_with_bedrock.cli.utils.aws.boto3.client", lambda *args, **kwargs: FakeClient())

    outputs = get_stack_outputs("missing-stack", "eu-west-3")

    captured = capsys.readouterr()
    assert outputs == {}
    assert captured.out == ""
    assert captured.err == ""


def test_check_s3_bucket_exists_returns_true(monkeypatch):
    """Existing buckets should return True."""

    class FakeClient:
        def head_bucket(self, Bucket):
            assert Bucket == "demo-bucket"

    monkeypatch.setattr("claude_code_with_bedrock.cli.utils.aws.boto3.client", lambda *args, **kwargs: FakeClient())

    assert check_s3_bucket_exists("demo-bucket", "eu-west-3") is True


def test_check_s3_bucket_exists_returns_false_for_missing_bucket(monkeypatch):
    """Missing buckets should return False."""

    class FakeClient:
        def head_bucket(self, Bucket):
            raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket")

    monkeypatch.setattr("claude_code_with_bedrock.cli.utils.aws.boto3.client", lambda *args, **kwargs: FakeClient())

    assert check_s3_bucket_exists("missing-bucket", "eu-west-3") is False
