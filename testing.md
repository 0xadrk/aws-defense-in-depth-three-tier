# Testing and validation

Replace `fortress3t` with your `PROJECT` value if you changed it.

1. **Encryption**
   - `aws rds describe-db-instances --query 'DBInstances[0].[StorageEncrypted,KmsKeyId]'`
   - `aws ec2 describe-volumes --filters Name=tag:Name,Values=fortress3t-app --query 'Volumes[].[Encrypted,KmsKeyId]'`
   - `aws ssm get-parameter --name /fortress3t/app/config` returns ciphertext; add `--with-decryption` to read it.
2. **Secret rotation**
   - `aws secretsmanager rotate-secret --secret-id fortress3t/rds/master`, then
     `describe-secret` should show a new `LastRotatedDate`. Check CloudTrail for `GetSecretValue` events.
3. **CloudTrail integrity**
   - `aws cloudtrail validate-logs --trail-arn <trail arn> --start-time <iso time>`
4. **GuardDuty and incident response**
   - `./scripts/test-incident-response.sh`; within about 15 minutes expect findings in GuardDuty and Security Hub, an SNS email,
     and Lambda logs. Sample findings reference fake instance IDs, so the Lambda reports a failed quarantine for them; that
     is expected. To test real isolation, set `DryRun=false` and trigger a finding against a real instance ID by invoking the
     Lambda with a hand-built event.
5. **Config auto-remediation**
   - Open SSH to the world on a test security group: `aws ec2 authorize-security-group-ingress --group-id <sg> --protocol tcp --port 22 --cidr 0.0.0.0/0`.
     Config flags it and the SSM document removes the rule (allow a few minutes).
   - Create a bucket without encryption or with a public ACL and watch the matching rule remediate it.
6. **WAF**
   - `curl -k "https://<alb-dns>/?id=1' OR '1'='1"` should return 403 once the ACL is associated.
7. **Security Hub**
   - Console -> Security standards: record the CIS and PCI DSS scores for your submission screenshots.

8. **CIS alarms**
   - Make a denied call, for example `aws s3 ls s3://some-bucket-you-cannot-read`, then check the `fortress3t-UnauthorizedApiCalls` alarm
     in CloudWatch (it can take a few minutes) and your e-mail.
