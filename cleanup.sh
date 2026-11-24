#!/usr/bin/env bash
# Deletes everything in reverse order. KMS keys enter a 7-day pending-deletion window.
set -euo pipefail
PROJECT="${PROJECT:-fortress3t}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"
export AWS_DEFAULT_REGION="$REGION"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"

empty_bucket() {  # versioned buckets need every version and delete marker removed
  python3 - "$1" <<'PY'
import sys, boto3
b = boto3.resource("s3").Bucket(sys.argv[1])
try:
    b.object_versions.delete()
except Exception as e:
    print("skip:", e)
PY
}

empty_bucket "${PROJECT}-audit-${ACCOUNT}-${REGION}"
empty_bucket "${PROJECT}-app-${ACCOUNT}-${REGION}"

for s in 08-incident-response 07-config-remediation 06-waf 05-compute 04-data 03-network 02-detection-audit 01-kms-iam; do
  echo ">>> Deleting ${PROJECT}-${s}"
  aws cloudformation delete-stack --stack-name "${PROJECT}-${s}"
  aws cloudformation wait stack-delete-complete --stack-name "${PROJECT}-${s}"
done
aws ssm delete-parameter --name "/${PROJECT}/app/config" 2>/dev/null || true
echo "Cleanup complete."
