# ─────────────────────────────────────────────────────────────────────────────
# utils/helpers.py  –  Sample-data generator + misc utilities
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta

import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Realistic ticket content pools
# ─────────────────────────────────────────────────────────────────────────────

_TICKET_POOL: dict[str, list[dict]] = {
    "CPU": [
        {"sd": "High CPU utilisation on production server",
         "desc": "CPU usage on PROD-APP-01 has crossed 95% threshold for the past 30 minutes. Datadog alert triggered. Need immediate investigation."},
        {"sd": "CPU spike causing application slowness",
         "desc": "End users are reporting slow response times. CPU utilisation on web-server-03 is at 98%. Suspected runaway process."},
        {"sd": "CPU threshold breach – DB server",
         "desc": "Splunk alert: DB-PROD-02 CPU at 92%. Slow queries detected. DBA team needs to review."},
        {"sd": "Processor performance degraded",
         "desc": "vCPU saturation on VM cluster. Workload balancing required. CPU steal time above 30%."},
        {"sd": "CPU overload on middleware node",
         "desc": "Middleware server CPU load average is 24 on an 8-core machine. Service is unresponsive."},
    ],
    "Memory": [
        {"sd": "Out of memory error on application server",
         "desc": "Java heap space exhausted on app-server-07. JVM restart performed but root cause unresolved. Memory leak suspected."},
        {"sd": "RAM utilisation above 90%",
         "desc": "Nagios alert: memory usage on web-01 is at 93%. Swap usage also elevated at 60%."},
        {"sd": "Low memory causing service restart",
         "desc": "Tomcat service restarted automatically due to OOM killer. Heap dump captured. Needs analysis."},
        {"sd": "Memory leak identified in application",
         "desc": "Application memory grows by ~200 MB/hour without release. GC logs show frequent full GC cycles."},
        {"sd": "Insufficient RAM on reporting server",
         "desc": "Reporting service crashes during large data exports. Server only has 8 GB RAM. Upgrade requested."},
    ],
    "Storage": [
        {"sd": "Disk space critical – /var filesystem",
         "desc": "SolarWinds alert: /var/log partition at 96% on db-server-01. Old log rotation not working. Need immediate cleanup."},
        {"sd": "Storage pool capacity exceeded",
         "desc": "NetApp SAN volume group at 94%. LUN expansion required. Storage team notified."},
        {"sd": "Disk IO latency spike",
         "desc": "Disk read/write latency on PROD-DB-03 exceeded 200 ms. IOPS saturation suspected. NVMe replacement planned."},
        {"sd": "Volume mount failure after reboot",
         "desc": "After last patch reboot, /data volume failed to auto-mount. fstab entry appears correct. Manual mount succeeded."},
        {"sd": "RAID controller degraded",
         "desc": "RAID-5 array reporting one failed disk. Hot spare kicked in. Replacement disk required urgently."},
    ],
    "Network": [
        {"sd": "Network connectivity loss to production subnet",
         "desc": "Servers in 10.20.30.0/24 are unreachable from management network. Switch port flapping detected on core-sw-02."},
        {"sd": "High latency on inter-DC link",
         "desc": "RTT between DC-East and DC-West jumped from 8 ms to 210 ms. BGP route advertisement changed. Investigation in progress."},
        {"sd": "VPN tunnel down – remote site",
         "desc": "Site-to-site VPN between HQ and Branch-04 is down. Remote users cannot access internal resources."},
        {"sd": "DNS resolution failure",
         "desc": "Internal DNS servers not resolving corporate domain names. Secondary DNS unreachable. Impact to all office users."},
        {"sd": "Firewall rule causing blocked traffic",
         "desc": "After change request CR-4521, application traffic on port 8443 is being blocked. Rule rollback needed."},
    ],
    "Hardware": [
        {"sd": "Server fan failure – thermal warning",
         "desc": "iDRAC alert: Fan-03 on server ESXI-HOST-02 failed. CPU temperature rising. Maintenance window opened."},
        {"sd": "Power supply unit failure",
         "desc": "Redundant PSU failed on rack server R03-U14. Single PSU running. Replacement parts ordered."},
        {"sd": "Physical server hardware error",
         "desc": "BIOS POST error on server BLD-02. Memory DIMM slot B1 showing uncorrectable ECC errors. DIMM replacement needed."},
        {"sd": "UPS battery needs replacement",
         "desc": "UPS in DC-Row-4 reporting battery fault. Runtime on battery reduced to 2 minutes. Replacement scheduled."},
        {"sd": "NIC port failure on host",
         "desc": "NIC-01 on VMware host ESXI-07 shows link down. Bonded interface in degraded state. NIC replacement required."},
    ],
    "Middleware": [
        {"sd": "WebLogic server not accepting new connections",
         "desc": "WebLogic thread pool exhausted on wl-server-01. Stuck threads detected. Server restart required."},
        {"sd": "Apache Kafka consumer lag spike",
         "desc": "Consumer group order-service showing lag of 500,000 messages. Partition rebalancing in progress."},
        {"sd": "Nginx reverse proxy returning 502",
         "desc": "Nginx upstream returning HTTP 502 Bad Gateway. Backend app-server pool health-check failing."},
        {"sd": "RabbitMQ queue overflow",
         "desc": "RabbitMQ queue payment-events has exceeded max length. Messages being dropped. Consumer throughput issue."},
        {"sd": "Tomcat connector timeout",
         "desc": "Tomcat connector maxThreads=200 reached. New connections queuing. Response time > 30s."},
    ],
    "Application": [
        {"sd": "Application service down – customer portal",
         "desc": "Customer portal returning HTTP 500. Deployment CR-7812 pushed 2 hours ago. Suspected regression. Rollback needed."},
        {"sd": "Application crashing on startup",
         "desc": "PaymentService crashes with NullPointerException on boot. Stack trace points to missing config property."},
        {"sd": "Application deployment failure",
         "desc": "CI/CD pipeline failed at deployment stage. Docker image push to registry timed out. Jenkins build #3421 failed."},
        {"sd": "Batch job not completing",
         "desc": "Nightly EOD batch job stuck since 02:00 AM. Investigating deadlock in job scheduler. Data processing delayed."},
        {"sd": "App throwing unhandled exceptions",
         "desc": "Application logs showing 2,300 unhandled exceptions in the last hour. OutOfBoundsException in data parser module."},
    ],
    "Database": [
        {"sd": "Oracle database tablespace almost full",
         "desc": "APP_DATA tablespace at 97% on ORCL-PROD. Auto-extend disabled. DBA action required immediately."},
        {"sd": "Slow SQL queries degrading performance",
         "desc": "30 slow queries identified in AWR report. Missing indexes on orders_fact table. Execution plan changed after stats gather."},
        {"sd": "Database replication lag",
         "desc": "MySQL replica on db-replica-02 is 45 minutes behind primary. Large transaction causing replication delay."},
        {"sd": "Database connection pool exhausted",
         "desc": "Connection pool to PostgreSQL maxed out at 500 connections. Application returning DB connection errors."},
        {"sd": "Backup failure – Oracle RMAN",
         "desc": "Nightly RMAN backup failed with ORA-19809 disk quota exceeded. Backup destination /backup is full."},
    ],
    "Security": [
        {"sd": "SSL certificate expiring in 7 days",
         "desc": "SSL certificate for api.company.com expires on the 15th. Auto-renewal failed. Manual renewal in progress."},
        {"sd": "Multiple failed login attempts detected",
         "desc": "SIEM alert: 450 failed SSH login attempts from IP 185.220.x.x in 10 minutes. Potential brute-force. IP blocked."},
        {"sd": "User account locked – access issue",
         "desc": "Service account SVC-APPMON locked after 5 failed password attempts. Application monitoring affected."},
        {"sd": "Vulnerability scan found critical CVE",
         "desc": "Qualys scan identified CVE-2024-1234 (CVSS 9.8) on web-server-02. Patch available. Emergency change required."},
        {"sd": "Unauthorised access attempt on database",
         "desc": "Audit log shows user EXTERNAL-USR tried to query sensitive HR tables. Access revoked. Incident under investigation."},
    ],
    "OS": [
        {"sd": "Linux server kernel panic",
         "desc": "Server LNX-PROD-04 crashed with kernel panic – not syncing. vmcore dump captured. Analysis pending."},
        {"sd": "Windows Server update causing blue screen",
         "desc": "After Windows Update KB5034441 applied, server rebooted into BSOD. Update rolled back. Systems restored."},
        {"sd": "OS filesystem read-only due to error",
         "desc": "Filesystem /opt mounted read-only after disk IO error. fsck required. Maintenance window needed."},
        {"sd": "Scheduled OS patching request",
         "desc": "Monthly OS patching cycle for 45 Linux servers. Patch Tuesday schedule. Reboot required for kernel updates."},
        {"sd": "Zombie processes consuming resources",
         "desc": "250 zombie processes detected on app-server-09. Parent process not reaping children. OS-level investigation needed."},
    ],
    "Monitoring": [
        {"sd": "Datadog alert – false positive suppression",
         "desc": "Datadog CPU monitor firing false positives during batch window 02:00-04:00. Alert suppression / downtime needed."},
        {"sd": "Splunk forwarder not sending logs",
         "desc": "Splunk universal forwarder on server app-07 stopped sending logs 6 hours ago. Splunkd service restarted."},
        {"sd": "SolarWinds node unreachable alert",
         "desc": "SolarWinds showing node ROUTER-CORE-01 as unreachable. SNMP polling failing. Network team to investigate."},
        {"sd": "Monitoring dashboard not loading",
         "desc": "Grafana dashboard times out for the Network Overview panel. InfluxDB query taking > 60s. Optimisation needed."},
        {"sd": "Alert storm from patching activity",
         "desc": "Patching activity triggered 300+ monitoring alerts. Alert acknowledgement and suppression window required."},
    ],
}

_TYPES     = ["Incident", "Service Request", "Change Request"]
_GROUPS    = [
    "L1-Service Desk", "L2-Server Team", "L2-Network Team",
    "L2-Database Admin", "L2-Security Team", "L3-Application Support",
    "L3-Infrastructure", "L3-Cloud Team", "L2-Storage Team",
    "L2-Middleware Team",
]
_STATUSES  = ["New", "In Progress", "On Hold", "Resolved", "Closed"]
_DOMAINS   = [
    "IT Infrastructure", "Application Services", "Network Services",
    "Security Operations", "Cloud & Virtualisation", "Database Services",
]
_CALLERS   = [
    "john.smith", "sarah.jones", "mike.patel", "linda.wu",
    "raj.kumar", "emily.chen", "carlos.garcia", "anna.brown",
    "ahmed.ali", "priya.nair", "tom.wilson", "jessica.lee",
]
_WORKNOTES = [
    "Investigated the issue. Root cause identified. Fix applied.",
    "Escalated to L3 team for further analysis.",
    "Vendor engaged. Awaiting response.",
    "Temporary workaround applied. Permanent fix pending.",
    "Issue resolved after server restart.",
    "Change request raised for permanent resolution.",
    "Monitoring in place. No recurrence in past 2 hours.",
    "User confirmed resolution. Ticket closing.",
    "Patch applied successfully during maintenance window.",
    "Awaiting business approval before proceeding.",
]
_PRIORITIES = ["P1 - Critical", "P2 - High", "P3 - Medium", "P4 - Low"]


def _random_ticket_id(prefix: str = "INC", num: int = 1) -> str:
    return f"{prefix}{num:07d}"


def generate_sample_data(n: int = 750) -> pd.DataFrame:
    """
    Generate *n* realistic-looking IT ITSM tickets across all categories.

    Returns a DataFrame with columns matching a typical ServiceNow export.
    """
    random.seed(42)
    cats = list(_TICKET_POOL.keys())

    # Weighted category distribution (realistic)
    weights = [12, 10, 12, 10, 6, 7, 12, 10, 8, 8, 8, 7]
    if len(weights) > len(cats):
        weights = weights[: len(cats)]
    weights = weights + [5] * (len(cats) - len(weights))

    records = []
    start_date = datetime(2024, 1, 1)

    for i in range(1, n + 1):
        cat = random.choices(cats, weights=weights, k=1)[0]
        pool = _TICKET_POOL[cat]
        tpl  = random.choice(pool)

        t_type = random.choices(
            _TYPES, weights=[60, 30, 10], k=1
        )[0]
        prefix = "INC" if t_type == "Incident" else ("RITM" if t_type == "Service Request" else "CHG")
        number = _random_ticket_id(prefix, i)

        opened = start_date + timedelta(
            days=random.randint(0, 364),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        resolved = opened + timedelta(
            hours=random.randint(1, 72)
        )
        status   = random.choices(_STATUSES, weights=[5, 20, 10, 30, 35], k=1)[0]
        priority = random.choices(_PRIORITIES, weights=[5, 20, 50, 25], k=1)[0]

        records.append({
            "Number":           number,
            "Type":             t_type,
            "Short_Description": tpl["sd"],
            "Description":       tpl["desc"],
            "Caller_ID":         random.choice(_CALLERS),
            "Assignment_Group":  random.choice(_GROUPS),
            "Priority":          priority,
            "Status":            status,
            "Domain":            random.choice(_DOMAINS),
            "Opened_At":         opened.strftime("%Y-%m-%d %H:%M"),
            "Resolved_At":       resolved.strftime("%Y-%m-%d %H:%M") if status in ("Resolved", "Closed") else "",
            "Work_Notes":        random.choice(_WORKNOTES),
            "Remarks":           "Resolved by " + random.choice(_GROUPS) if status == "Closed" else "",
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────────────────────────────────────
# Misc helpers
# ─────────────────────────────────────────────────────────────────────────────

def format_duration(seconds: float) -> str:
    """Human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes/60:.1f}h"


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    return (text[:max_len] + "…") if len(text) > max_len else text


def sanitise_filename(name: str) -> str:
    """Remove characters unsafe for filenames."""
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
