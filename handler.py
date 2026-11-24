"""Incident response automation.

Triggered by EventBridge for:
  * GuardDuty findings with severity >= SEVERITY_THRESHOLD
  * Security Hub CRITICAL findings

For EC2 instances named in a GuardDuty finding it:
  1. tags the instance with the finding id and its original security groups
  2. snapshots every attached EBS volume (forensic evidence)
  3. swaps the instance onto the quarantine security group (no in/out traffic)
Every event, including non-EC2 ones, is reported to the SNS alert topic.
"""
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client("ec2")
sns = boto3.client("sns")

QUARANTINE_SG = os.environ["QUARANTINE_SG"]
TOPIC_ARN = os.environ["TOPIC_ARN"]
THRESHOLD = float(os.environ.get("SEVERITY_THRESHOLD", "7"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event, default=str))
    source = event.get("source")
    if source == "aws.guardduty":
        return _handle_guardduty(event.get("detail", {}))
    if source == "aws.securityhub":
        return _handle_securityhub(event.get("detail", {}))
    logger.warning("Ignoring event from unexpected source: %s", source)
    return {"status": "ignored"}


def _handle_guardduty(detail):
    severity = float(detail.get("severity", 0))
    if severity < THRESHOLD:
        return {"status": "below-threshold", "severity": severity}

    resource = detail.get("resource", {})
    actions = []
    if resource.get("resourceType") == "Instance":
        instance_id = resource.get("instanceDetails", {}).get("instanceId")
        if instance_id:
            actions = _quarantine_instance(instance_id, detail.get("id", "unknown"))
    else:
        actions = ["notify-only (resource type: %s)" % resource.get("resourceType")]

    _notify(
        subject="[GuardDuty %.1f] %s" % (severity, detail.get("type", "finding")),
        body={
            "title": detail.get("title"),
            "type": detail.get("type"),
            "severity": severity,
            "account": detail.get("accountId"),
            "region": detail.get("region"),
            "finding_id": detail.get("id"),
            "dry_run": DRY_RUN,
            "automated_actions": actions,
        },
    )
    return {"status": "handled", "actions": actions}


def _handle_securityhub(detail):
    findings = detail.get("findings", [])
    for finding in findings:
        _notify(
            subject="[Security Hub CRITICAL] %s" % finding.get("Title", "finding")[:70],
            body={
                "title": finding.get("Title"),
                "description": finding.get("Description"),
                "product": finding.get("ProductName"),
                "resources": [r.get("Id") for r in finding.get("Resources", [])],
                "finding_id": finding.get("Id"),
            },
        )
    return {"status": "notified", "count": len(findings)}


def _quarantine_instance(instance_id, finding_id):
    actions = []
    try:
        reservations = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"]
        instance = reservations[0]["Instances"][0]
        original_sgs = [g["GroupId"] for g in instance.get("SecurityGroups", [])]
        if original_sgs == [QUARANTINE_SG]:
            return ["already quarantined"]
        volume_ids = [
            m["Ebs"]["VolumeId"]
            for m in instance.get("BlockDeviceMappings", [])
            if "Ebs" in m
        ]

        if DRY_RUN:
            return [
                "DRY RUN: would tag %s" % instance_id,
                "DRY RUN: would snapshot %s" % volume_ids,
                "DRY RUN: would move %s to %s" % (instance_id, QUARANTINE_SG),
            ]

        ec2.create_tags(
            Resources=[instance_id],
            Tags=[
                {"Key": "SecurityStatus", "Value": "Quarantined"},
                {"Key": "QuarantinedByFinding", "Value": finding_id[:250]},
                {"Key": "OriginalSecurityGroups", "Value": ",".join(original_sgs)[:250]},
            ],
        )
        actions.append("tagged %s" % instance_id)

        for volume_id in volume_ids:
            snap = ec2.create_snapshot(
                VolumeId=volume_id,
                Description="Forensic snapshot for GuardDuty finding %s" % finding_id,
                TagSpecifications=[
                    {
                        "ResourceType": "snapshot",
                        "Tags": [
                            {"Key": "Purpose", "Value": "forensics"},
                            {"Key": "SourceInstance", "Value": instance_id},
                        ],
                    }
                ],
            )
            actions.append("snapshot %s of %s" % (snap["SnapshotId"], volume_id))

        ec2.modify_instance_attribute(InstanceId=instance_id, Groups=[QUARANTINE_SG])
        actions.append("moved %s to quarantine SG %s" % (instance_id, QUARANTINE_SG))
    except ClientError as err:
        logger.exception("Quarantine failed for %s", instance_id)
        actions.append("FAILED for %s: %s" % (instance_id, err.response["Error"]["Code"]))
    return actions


def _notify(subject, body):
    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=subject[:100],
        Message=json.dumps(body, indent=2, default=str),
    )
