# ─────────────────────────────────────────────────────────────────────────────
# config/settings.py  –  Global configuration for Ticket Volume Analyser
# ─────────────────────────────────────────────────────────────────────────────

# ── IT Infrastructure Classification Categories ──────────────────────────────
# Each category has a list of keywords used for fallback keyword-based
# classification when Ollama LLM is unavailable.

CATEGORIES = {
    "CPU": [
        "cpu", "processor", "core", "high cpu", "cpu usage", "cpu spike",
        "cpu utilization", "cpu load", "cpu alert", "cpu threshold",
        "processing power", "cpu perf", "cpu performance", "vcpu",
        "compute", "cpu bottleneck", "cpu 100", "cpu overload", "cpu high",
        "processor utilization", "core usage", "hyperthread",
    ],
    "Memory": [
        "memory", "ram", "heap", "out of memory", "oom", "swap",
        "paging", "memory leak", "memory usage", "memory alert",
        "memory utilization", "memory threshold", "low memory",
        "insufficient memory", "memory exhausted", "jvm heap",
        "gc overhead", "garbage collection", "virtual memory",
        "page file", "memory dump", "mem usage",
    ],
    "Storage": [
        "storage", "disk", "volume", "partition", "filesystem",
        "disk space", "disk usage", "iops", "disk io", "disk alert",
        "disk threshold", "disk full", "drive", "san", "nas",
        "disk utilization", "lun", "mount", "file system",
        "disk capacity", "storage pool", "disk 90%", "disk 80%",
        "volume group", "logical volume", "pvs", "vgs", "lvs",
        "disk read", "disk write", "io wait",
    ],
    "Network": [
        "network", "connectivity", "latency", "bandwidth", "packet",
        "firewall", "vpn", "dns", "ip address", "port", "interface",
        "network alert", "network down", "connection", "routing",
        "switch", "router", "ping", "timeout", "network failure",
        "packet loss", "network congestion", "link", "vlan", "subnet",
        "load balancer", "proxy", "nat", "bgp", "ospf", "network lag",
        "ssh", "rdp", "ftp", "sftp", "http", "https", "connection refused",
    ],
    "Hardware": [
        "hardware", "server", "physical", "blade", "rack",
        "power supply", "ups", "battery", "fan", "temperature",
        "thermal", "hardware failure", "nic", "hba", "psu", "raid",
        "controller", "physical server", "motherboard", "bios",
        "firmware", "hardware error", "hardware alert", "overheating",
        "power outage", "hardware fault", "dead server", "hardware crash",
        "tape library", "decommission",
    ],
    "Middleware": [
        "middleware", "weblogic", "jboss", "tomcat", "iis",
        "apache", "nginx", "websphere", "mq", "message queue",
        "broker", "service bus", "middleware alert", "app server",
        "web server", "application server", "activemq", "rabbitmq",
        "kafka", "ibm mq", "tibco", "jms", "soap", "rest api",
        "microservice", "container", "docker", "kubernetes", "k8s",
        "pod", "helm", "service mesh", "istio",
    ],
    "Application": [
        "application", "app", "service", "process", "crash",
        "exception", "error", "application error", "app down",
        "deployment", "release", "code", "bug", "application failure",
        "software", "program", "application crash", "app unavailable",
        "500 error", "404", "application timeout", "build fail",
        "ci/cd", "jenkins", "pipeline", "rollback", "hotfix",
        "patch", "upgrade", "version",
    ],
    "Database": [
        "database", "db", "oracle", "sql server", "mysql", "postgresql",
        "postgres", "mongodb", "query", "tablespace", "db alert",
        "database down", "db performance", "replication", "backup failed",
        "db error", "data", "schema", "index", "slow query",
        "deadlock", "connection pool", "db connection", "db timeout",
        "stored procedure", "db crash", "corruption", "db recovery",
        "asm", "rac", "dataguard", "always on",
    ],
    "Security": [
        "security", "certificate", "ssl", "tls", "vulnerability",
        "access denied", "permission", "unauthorized", "breach", "malware",
        "antivirus", "firewall rule", "compliance", "audit", "password",
        "authentication", "authorization", "account locked", "mfa",
        "2fa", "intrusion", "threat", "phishing", "ransomware",
        "expired certificate", "cert renewal", "ssl error", "token",
        "privilege", "access control", "iam", "sso",
    ],
    "OS": [
        "operating system", "windows", "linux", "unix", "rhel",
        "centos", "ubuntu", "kernel", "patch", "reboot", "restart",
        "os update", "system update", "bsod", "blue screen",
        "os crash", "system down", "boot", "grub", "system hang",
        "kernel panic", "os upgrade", "os patch", "cron", "systemd",
        "service not running", "process hang", "zombie process",
        "os performance", "windows update",
    ],
    "Monitoring": [
        "monitoring", "alert", "datadog", "splunk", "solarwinds",
        "nagios", "zabbix", "prometheus", "grafana", "monitor",
        "threshold", "metric", "log", "event", "notification",
        "alarm", "pagerduty", "opsgenie", "new relic", "dynatrace",
        "appdynamics", "false alert", "alert storm", "snmp",
        "syslog", "event log", "log monitoring", "apm",
    ],
    "Others": [],
}

# ── Ollama Configuration ─────────────────────────────────────────────────────
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "default_model": "llama3.2",
    "timeout": 30,
    "max_retries": 2,
    "temperature": 0.1,
    "num_predict": 15,
}

# ── Supported Ollama Models ──────────────────────────────────────────────────
SUPPORTED_MODELS = [
    "llama3.2",
    "llama3.2:1b",
    "llama3.1",
    "llama3",
    "llama2",
    "mistral",
    "mistral-nemo",
    "codellama",
    "phi3",
    "phi3.5",
    "gemma2",
    "gemma2:2b",
    "qwen2.5",
    "qwen2.5:3b",
    "deepseek-r1",
    "smollm2",
]

# ── Column Auto-Detection Mappings ───────────────────────────────────────────
# Maps internal field name → list of possible column name variations
COLUMN_MAPPINGS = {
    "id": [
        "id", "ticket_id", "incident_id", "number", "ticket_number",
        "inc_number", "sr_number", "change_number", "sys_id",
        "ticket no", "incident no", "request no",
    ],
    "type": [
        "type", "ticket_type", "incident_type", "request_type",
        "sys_class_name", "call_type",
    ],
    "short_description": [
        "short_description", "short description", "subject",
        "title", "summary", "brief_description", "name",
    ],
    "description": [
        "description", "details", "comments", "work_notes",
        "worknotes", "notes", "body", "long_description",
        "incident_description", "problem_description",
    ],
    "status": [
        "status", "state", "ticket_status", "incident_status",
        "request_state", "current_status",
    ],
    "assignment_group": [
        "assignment_group", "assignment group", "group",
        "team", "assigned_group", "assigned_to_group",
        "support_group", "resolver_group",
    ],
    "caller_id": [
        "caller_id", "caller", "requester", "reporter",
        "raised_by", "opened_by", "created_by", "user",
    ],
    "domain": [
        "domain", "service", "business_service",
        "service_category", "business_domain",
    ],
    "remarks": [
        "remarks", "resolution", "resolution_notes",
        "close_notes", "resolution_code", "closure_notes",
        "work_notes",
    ],
    "priority": [
        "priority", "severity", "impact", "urgency",
    ],
}

# ── Status Normalisation Map ─────────────────────────────────────────────────
# Maps raw status values to normalised display values
STATUS_NORMALISE = {
    "1": "New",
    "2": "In Progress",
    "3": "On Hold",
    "4": "Resolved",
    "6": "Closed",
    "7": "Cancelled",
    "new": "New",
    "open": "New",
    "assigned": "In Progress",
    "work in progress": "In Progress",
    "wip": "In Progress",
    "in progress": "In Progress",
    "in-progress": "In Progress",
    "pending": "On Hold",
    "on hold": "On Hold",
    "on-hold": "On Hold",
    "resolved": "Resolved",
    "closed": "Closed",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
}

# ── Category Colour Palette (hex, no #) ─────────────────────────────────────
CATEGORY_COLORS = {
    "CPU":         "FF6B6B",
    "Memory":      "4ECDC4",
    "Storage":     "45B7D1",
    "Network":     "96CEB4",
    "Hardware":    "F6C90E",
    "Middleware":  "C39BD3",
    "Application": "76D7C4",
    "Database":    "F7DC6F",
    "Security":    "EC407A",
    "OS":          "AB47BC",
    "Monitoring":  "29B6F6",
    "Others":      "BDBDBD",
}

# ── UI Colour Theme ──────────────────────────────────────────────────────────
THEME = {
    "primary":   "#0D47A1",
    "secondary": "#1565C0",
    "accent":    "#42A5F5",
    "success":   "#2E7D32",
    "warning":   "#F57F17",
    "error":     "#C62828",
    "bg_dark":   "#0A1628",
    "bg_card":   "#F8FAFF",
}

APP_VERSION = "1.0.0"
APP_NAME    = "IT Ticket Volume Dump Analyser"
