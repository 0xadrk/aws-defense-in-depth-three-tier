#!/usr/bin/env bash
# Run in the AWS Organizations MANAGEMENT account. Usage: ./scripts/apply-scps.sh <target-id: OU or account id>
# Test on a sandbox OU first: an SCP can lock people out.
set -euo pipefail
TARGET="${1:?Usage: $0 <OU-or-account-id>}"
DIR="$(cd "$(dirname "$0")/../policies" && pwd)"
for f in "$DIR"/scp-*.json; do
  name="$(basename "$f" .json)"
  id="$(aws organizations create-policy --type SERVICE_CONTROL_POLICY \
        --name "$name" --description "Project 8: $name" \
        --content "file://$f" --query Policy.PolicySummary.Id --output text)"
  aws organizations attach-policy --policy-id "$id" --target-id "$TARGET"
  echo "Attached $name ($id) to $TARGET"
done
