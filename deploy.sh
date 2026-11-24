#!/usr/bin/env bash
# Deploys all stacks in dependency order.
# Usage: ALERT_EMAIL=you@example.com [CERTIFICATE_ARN=arn:aws:acm:...] [PROJECT=fortress3t] ./scripts/deploy.sh
set -euo pipefail

PROJECT="${PROJECT:-fortress3t}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"
CERT="${CERTIFICATE_ARN:-}"
: "${ALERT_EMAIL:?Set ALERT_EMAIL to receive security alerts}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CF="$ROOT/cloudformation"
export AWS_DEFAULT_REGION="$REGION"

deploy() {
  local name="$1" file="$2"; shift 2
  echo ">>> Deploying ${PROJECT}-${name}"
  aws cloudformation deploy \
    --stack-name "${PROJECT}-${name}" \
    --template-file "$file" \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --no-fail-on-empty-changeset \
    --parameter-overrides ProjectName="$PROJECT" "$@"
}

deploy 01-kms-iam              "$CF/01-kms-iam.yaml"
deploy 02-detection-audit      "$CF/02-detection-audit.yaml" AlertEmail="$ALERT_EMAIL"

# Centralised parameter: SecureString encrypted with the customer-managed key
# (CloudFormation cannot create SecureString parameters, so it is created here).
aws ssm put-parameter --name "/${PROJECT}/app/config" --type SecureString \
  --key-id "alias/${PROJECT}-data" --value '{"feature_flags":{"beta":false}}' --overwrite >/dev/null

deploy 03-network              "$CF/03-network.yaml"
deploy 04-data                 "$CF/04-data.yaml"
deploy 05-compute              "$CF/05-compute.yaml" CertificateArn="$CERT"
deploy 06-waf                  "$CF/06-waf.yaml"
deploy 07-config-remediation   "$CF/07-config-remediation.yaml"

# Stack 08 ships Lambda code, so it is packaged to S3 first.
BUCKET="$(aws cloudformation describe-stacks --stack-name "${PROJECT}-02-detection-audit" \
  --query "Stacks[0].Outputs[?OutputKey=='AuditBucketName'].OutputValue" --output text)"
aws cloudformation package --template-file "$CF/08-incident-response.yaml" \
  --s3-bucket "$BUCKET" --s3-prefix lambda-artifacts \
  --output-template-file /tmp/08-incident-response.packaged.yaml
deploy 08-incident-response    /tmp/08-incident-response.packaged.yaml

echo
echo "Done. Confirm the SNS subscription email, then see docs/testing.md."
aws cloudformation describe-stacks --stack-name "${PROJECT}-05-compute" \
  --query "Stacks[0].Outputs[?OutputKey=='AlbDnsName'].OutputValue" --output text
