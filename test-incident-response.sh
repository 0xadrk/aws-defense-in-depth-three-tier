#!/usr/bin/env bash
# Generates GuardDuty sample findings (Recon, Backdoor, CryptoCurrency) to exercise the EventBridge -> Lambda -> SNS path.
set -euo pipefail
DETECTOR="$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)"
aws guardduty create-sample-findings --detector-id "$DETECTOR" --finding-types \
  "Recon:EC2/PortProbeUnprotectedPort" \
  "Backdoor:EC2/C&CActivity.B!DNS" \
  "CryptoCurrency:EC2/BitcoinTool.B!DNS"
echo "Sample findings created. Check your email, CloudWatch Logs (/aws/lambda/*-incident-response) and Security Hub."
