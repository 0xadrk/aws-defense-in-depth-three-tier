# Well-Architected Security Pillar mapping

| Area | Practice | Implementation |
|---|---|---|
| Identity and access | Least privilege, permission boundaries | App role limited to one secret, one key, one bucket, one SSM path; boundary denies IAM and security-service changes |
| Identity and access | Protect the root user | SCP `scp-deny-root-usage`, Config rules for root MFA and root access keys |
| Detection | Log everything, tamper-evident | Multi-region CloudTrail with log file validation, KMS encryption, versioned bucket, 365-day lifecycle |
| Detection | Automated analysis and alarms | CIS metric-filter alarms on CloudTrail; GuardDuty (S3, EBS malware, RDS login, Lambda network), Security Hub CIS / PCI DSS / FSBP |
| Infrastructure protection | Network layers | Three tiers, SG-to-SG rules, isolated data subnets with NACL, WAF managed rules and rate limit, Shield Standard |
| Infrastructure protection | Harden compute | IMDSv2 required, no SSH (Session Manager via `AmazonSSMManagedInstanceCore`), encrypted EBS |
| Data protection | Encrypt at rest | Customer-managed KMS keys with rotation |
| Data protection | Encrypt in transit | TLS on ALB, enforced on RDS and S3 |
| Data protection | Manage secrets | Secrets Manager with 30-day rotation; SSM SecureString for config |
| Incident response | Prepare and automate | EventBridge -> Lambda quarantine, snapshots, SNS alert; sample-finding test script |
| Application security | Prevent common web attacks | WAF SQLi, common rule set (XSS and others), known bad inputs |
