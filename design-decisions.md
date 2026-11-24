# Design decisions, risks and future work

| Decision | Why | Trade-off |
|---|---|---|
| Two CMKs (data, audit) | Separates who can decrypt workload data from who can read audit logs | More keys to manage |
| Key policy delegates to IAM | Standard pattern; keeps policies in IAM and avoids lockout | Anyone with `kms:*` in IAM is a key admin; protect with SCPs |
| Hosted rotation Lambda | AWS maintains the rotation code | Less customisable than a hand-written function |
| Security Hub with CIS, PCI DSS and FSBP | Shows the compliance score per framework | Needs Config recording; some controls fail in a lab (for example root MFA) |
| Quarantine by security group swap | Fast and reversible; keeps memory and disk for forensics | Instance is replaced by the ASG after failing health checks |
| One NAT gateway | Cost | AZ failure removes outbound access for the app tier |
| Remediate only S3 and SGs automatically | Safe, idempotent fixes | EBS/RDS encryption needs rebuild, so detective only |

## Risks
- Auto-remediation can break a legitimate workload. Run new rules in review mode first (set `Automatic: false`).
- The responder isolates on severity alone; sample or false-positive findings can quarantine a healthy instance. Use `DryRun=true` while tuning.
- SCPs can lock out administrators. Test on a sandbox OU.
- Always-on services (NAT, ALB, RDS, GuardDuty, Config) generate cost until `cleanup.sh` runs.

## Future work
- Multi-account: delegated administrator for GuardDuty and Security Hub, organization trail, Config aggregator.
- WAF logging to a `aws-waf-logs-*` destination and CloudWatch alarms for root login (CIS 3.x metric filters).
- VPC endpoints for Secrets Manager, KMS and SSM to remove the NAT dependency for AWS API calls.
- Step Functions workflow with human approval before isolating production instances.

## Additional decisions
| Decision | Why | Trade-off |
|---|---|---|
| One shared encrypted SNS topic (stack 02) for alarms and responder | A single place to subscribe | Topic and key policy must allow CloudWatch and Lambda |
| CIS metric-filter alarms in addition to Security Hub | Real-time paging for the highest-risk API events | Alarms fire on legitimate admin work too; tune thresholds |
| S3 gateway endpoint | Free, removes S3 from NAT path | Interface endpoints for KMS/Secrets/SSM are still future work (hourly cost) |
