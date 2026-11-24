"""Generates architecture.svg (repo root) - AWS-style architecture diagram (service tiles use AWS category colours).
Swap in the official AWS Architecture Icons in diagrams.net if you want the exact logos."""
W, H = 1400, 940
COL = {"sec": "#DD344C", "cmp": "#ED7100", "net": "#8C4FFF", "sto": "#7AA116",
       "db": "#C925D1", "mgmt": "#E7157B", "app": "#E7157B", "usr": "#232F3E"}
out = []
def add(s): out.append(s)

def box(x, y, w, h, label, stroke, dash=False, fill="none", lab_color=None):
    d = ' stroke-dasharray="8 5"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"{d}/>')
    add(f'<text x="{x+14}" y="{y+24}" font-size="15" font-weight="700" fill="{lab_color or stroke}">{label}</text>')

def icon(cx, cy, abbr, label, kind, sub=None):
    x, y = cx - 32, cy - 32
    add(f'<rect x="{x}" y="{y}" width="64" height="64" rx="9" fill="{COL[kind]}"/>')
    add(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="{16 if len(abbr)<5 else 13}" font-weight="700" fill="#fff">{abbr}</text>')
    add(f'<text x="{cx}" y="{cy+50}" text-anchor="middle" font-size="12.5" fill="#232F3E">{label}</text>')
    if sub:
        add(f'<text x="{cx}" y="{cy+65}" text-anchor="middle" font-size="11" fill="#5a6877">{sub}</text>')

def arrow(x1, y1, x2, y2, color="#232F3E", dash=False, label=None):
    d = ' stroke-dasharray="6 5"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"{d} marker-end="url(#a)"/>')
    if label:
        add(f'<text x="{(x1+x2)/2}" y="{(y1+y2)/2-6}" text-anchor="middle" font-size="11" fill="{color}">{label}</text>')

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif">')
add('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
add('<text x="700" y="38" text-anchor="middle" font-size="24" font-weight="700" fill="#232F3E">Secure Multi-Tier Architecture - Defense in Depth</text>')
add('<text x="700" y="60" text-anchor="middle" font-size="13" fill="#5a6877">KMS - Secrets Manager - GuardDuty - Security Hub - Config - CloudTrail - WAF - EventBridge + Lambda</text>')

# AWS cloud + VPC
box(150, 72, 1235, 848, "AWS Cloud (single region, two Availability Zones)", "#232F3E")
box(300, 104, 700, 541, "VPC 10.20.0.0/16", "#248814", dash=True)

# tiers
box(320, 135, 660, 140, "Web tier - public subnets (10.20.0.0/24, 10.20.1.0/24)", "#248814", fill="#f3faf1")
box(320, 290, 660, 170, "App tier - private subnets (10.20.10.0/24, 10.20.11.0/24)", "#147EBA", fill="#f1f8fc")
box(320, 475, 660, 150, "Data tier - isolated subnets (10.20.20.0/24, 10.20.21.0/24) - no internet route", "#DD344C", fill="#fdf3f4")

# edge
icon(60, 330, "USERS", "Internet users", "usr")
icon(225, 330, "WAF", "AWS WAF", "sec", "SQLi / XSS / rate limit")
icon(225, 450, "SHLD", "Shield Standard", "sec", "DDoS protection")
arrow(95, 330, 190, 330)
arrow(262, 330, 395, 205)

# web
icon(430, 205, "ALB", "Application LB", "net", "TLS 1.2 / 1.3")
icon(600, 205, "IGW", "Internet Gateway", "net")
icon(770, 205, "NAT", "NAT Gateway", "net")
# app
icon(430, 380, "EC2", "EC2 Auto Scaling", "cmp", "IMDSv2, KMS-encrypted EBS")
icon(620, 380, "SSM", "Session Manager", "mgmt", "no SSH")
icon(810, 380, "LAMBDA", "Rotation Lambda", "cmp", "30-day rotation")
arrow(430, 282, 430, 345)
# data
icon(430, 545, "RDS", "RDS MySQL", "db", "KMS at rest, TLS in transit")
icon(620, 545, "NACL", "NACL + SGs", "net", "3306 from app only")
arrow(430, 415, 430, 510)
add('<text x="440" y="470" font-size="11" fill="#232F3E">3306</text>')
arrow(780, 415, 466, 540, color="#8C4FFF")

# right column: encryption + secrets
box(1030, 105, 335, 540, "Encryption and secrets", "#DD344C")
icon(1110, 190, "KMS", "KMS CMKs", "sec", "data key + audit key")
icon(1285, 190, "SECRETS", "Secrets Manager", "sec", "RDS creds, rotated")
icon(1110, 360, "PARAM", "SSM Parameter Store", "mgmt", "SecureString (CMK)")
icon(1285, 360, "S3", "S3 app bucket", "sto", "SSE-KMS, TLS only")
icon(1195, 530, "IAM", "IAM + boundary", "sec", "least privilege + SCPs")

# bottom band: detection / audit / response
box(170, 665, 1195, 240, "Detection, audit and automated response", "#E7157B")
y = 760
icon(240, y, "TRAIL", "CloudTrail", "mgmt", "multi-region, validated")
icon(385, y, "CFG", "AWS Config", "mgmt", "rules + SSM fixes")
icon(530, y, "GD", "GuardDuty", "sec", "Recon / Backdoor / Crypto")
icon(700, y, "HUB", "Security Hub", "sec", "CIS - PCI DSS - FSBP")
icon(870, y, "EVT", "EventBridge", "app", "severity >= 7, CRITICAL")
icon(1020, y, "LAMBDA", "Responder Lambda", "cmp", "quarantine + snapshot")
icon(1170, y, "SNS", "SNS alerts", "app", "email")
icon(1300, y, "CW", "CW Alarms", "mgmt", "CIS metric filters")
arrow(562, y, 667, y)
arrow(733, y, 837, y)
arrow(903, y, 987, y)
arrow(1053, y, 1137, y)
add(f'<path d="M385,{y+74} C385,{y+116} 700,{y+116} 700,{y+76}" fill="none" stroke="#232F3E" stroke-width="2" marker-end="url(#a)"/>')
add(f'<text x="470" y="{y+122}" font-size="11" fill="#232F3E">compliance findings</text>')
arrow(1268, y, 1206, y)
add('<text x="190" y="900" font-size="12" fill="#5a6877">Logs land in a KMS-encrypted, versioned audit bucket. Config auto-remediates public/unencrypted S3 and open SSH. Quarantine = no-traffic security group + EBS forensic snapshots.</text>')
add('</svg>')
open(__file__.replace("docs/diagram/generate_diagram.py", "architecture.svg"), "w").write("\n".join(out))
print("written")
