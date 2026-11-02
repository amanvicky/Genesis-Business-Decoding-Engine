"""Tab 10 — Technical Architecture & Code Scaffolding."""
from __future__ import annotations

from ..data import scaffold as SC
from ..models import Evidence
from .base import Agent

ARCH_BY_SECTOR = {
    "generic": ["Next.js (App Router) UI", "FastAPI service layer", "Postgres (single source of truth)", "Auth: email OTP → session cookies", "Queue: none — do work synchronously until it hurts", "Payments: gateway-hosted checkout (SAQ-A scope)"],
    "saas": ["Next.js dashboard + multi-tenant row-level security (tenant_id on every row)", "FastAPI + Postgres + Redis (cache/rate-limit)", "Background jobs: Postgres SKIP LOCKED (no extra infra)", "Billing: Stripe/Razorpay checkout + webhook with idempotency key", "Observability: structured JSON logs first, OpenTelemetry when >3 services"],
    "fintech": ["Ledger is append-only double-entry — never UPDATE money rows", "Idempotency keys on every mutating endpoint", "Gateway-hosted flows only (stay SAQ-A; never touch PANs)", "Ledger service + reconciliation job (gateway CSV vs ledger, daily)", "Audit log is a first-class table, not a nice-to-have", "Secrets in env/KMS; PII columns encrypted at app layer"],
    "payroll": ["Per-state tax rules as versioned data tables, NOT code branches", "Pay-period engine (calendar + frequency + retro rules)", "General-ledger export (the integration every accountant demands)", "E-filing adapters behind an interface (vendor-swappable)", "Every run is immutable + re-runnable: run_id → snapshots", "Audit trail with who/what/when for every calculation change"],
    "commerce": ["Storefront: Next.js ISR for catalog pages", "Cart/checkout: server actions + gateway-hosted checkout", "Inventory: Postgres with SELECT ... FOR UPDATE on stock mutation", "Search: Postgres full-text first; Meilisearch when needed"],
    "health": ["PHI segregation: separate DB/schema, stricter access", "BAA-compliant hosting choices documented", "Audit logging on every PHI read", "Encryption: field-level for identifiers"],
    "edu": ["Content pipeline separate from user data", "COPPA/DPDP-aware: no third-party trackers on minor flows"],
    "devtools": ["API-first: the UI is a client of your public API", "SDKs generated from OpenAPI spec", "Usage metering table → billing joins", "Self-serve onboarding with sandbox keys"],
    "logistics": ["Event-driven: shipment lifecycle as state machine", "Driver/vehicle assignment = constraint problem (start greedy)", "Geo data in PostGIS"],
}


class TechArchAgent(Agent):
    id = "techarch"
    title = "Technical Architecture & Code Scaffolding"
    icon = "🏗"
    tab = 10

    async def build(self, ev: Evidence) -> dict:
        sector = ev.sector
        geo = ev.req.geography.value
        gateway = "Razorpay" if geo == "india" else "Stripe"
        files = SC.build_scaffold(f"{ev.subject} MVP", sector, geo)
        stack = ARCH_BY_SECTOR.get(sector, ARCH_BY_SECTOR["generic"])
        decisions = [
            {"decision": f"Payments: {gateway} hosted checkout + webhook idempotency", "why": "Tokenized card data keeps you out of PCI scope; hosted page carries the compliance burden."},
            {"decision": "Postgres for everything (data, queue via SKIP LOCKED, audit)", "why": "One dependency to learn/backup/secure. Add Kafka/Redis when a measured bottleneck exists, never before."},
            {"decision": "FastAPI + Pydantic models mirrored to TS types", "why": "One schema definition shared FE/BE kills the drift bug class."},
            {"decision": "Deploy: Fly.io free allowance / Render free tier / a $5 VPS", "why": "Zero-cost constraint: no managed Kubernetes fantasy at this stage."},
        ]
        return {
            "stack": stack,
            "architecture": {
                "client": "Next.js 14 (App Router, RSC for data fetch, Tailwind UI)",
                "api": "FastAPI (Pydantic v2 models, OpenAPI auto-docs)",
                "db": "Postgres 16 (row-level security for multi-tenancy)",
                "payments": f"{gateway} (hosted checkout, webhooks with idempotency)",
                "auth": "Email OTP + httpOnly session cookies (no JWT-in-localStorage)",
                "deploy": "Fly.io/Render free tier + GitHub Actions CI (free for public repos)",
            },
            "decisions": decisions,
            "files": files,
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        return f"{len(data['stack'])}-layer stack decoded ({ev.sector}/{ev.req.geography.value}); {len(data['files'])} starter files generated ({', '.join(f['path'] for f in data['files'][:3])}…)."
