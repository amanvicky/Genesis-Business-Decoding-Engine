"""Auto-generated starter-code scaffolding for the MVP (Tab 10).

Returns a file map {path: {language, content}}. Files are rendered in the UI
with copy buttons and included in the downloadable playbook ZIP.
Templates use @TOKEN@ replacement (not str.format) because the embedded code
is full of literal braces.
"""
from __future__ import annotations

FASTAPI_MAIN = '''# backend/main.py — Genesis MVP scaffold (FastAPI)
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os

app = FastAPI(title="@TITLE@ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Health(BaseModel):
    status: str
    version: str


@app.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(status="ok", version=app.version)


# --- Domain model (edit to your entity) ---
class Item(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    meta: dict = Field(default_factory=dict)


# In-memory for day 1; swap for Postgres (schema.sql included) when you have users.
_DB: dict[str, Item] = {}


@app.post("/api/items", response_model=Item, status_code=201)
def create(payload: Item) -> Item:
    key = f"item_{len(_DB) + 1}"
    payload.id = key
    _DB[key] = payload
    return payload


@app.get("/api/items")
def list_all() -> list[Item]:
    return list(_DB.values())


@app.get("/api/items/{item_id}", response_model=Item)
def get(item_id: str) -> Item:
    item = _DB.get(item_id)
    if not item:
        raise HTTPException(404)
    return item
'''

SCHEMA_SQL = '''-- schema.sql — Postgres starter (run with psql -f schema.sql)
create extension if not exists "uuid-ossp";

create table users (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    created_at timestamptz not null default now()
);

create table items (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    name text not null,
    status text not null default 'active',
    meta jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_items_user on items(user_id);

-- Audit trail you will need the moment money or compliance is involved
create table audit_log (
    id bigserial primary key,
    actor text not null,
    action text not null,
    entity text not null,
    entity_id uuid,
    payload jsonb not null default '{}'::jsonb,
    at timestamptz not null default now()
);
'''

WEBHOOK = '''# backend/payments.py — gateway webhook with idempotency (the #1 thing
# first-time founders get wrong: processing a @GATEWAY@ event twice).
import hashlib
import os
import json
import hmac
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()
_seen: set[str] = set()  # swap for redis SETNX in production


@router.post("/api/webhooks/@GATEWAY@")
async def webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("@SIG_HEADER@", "")
    secret = os.environ["WEBHOOK_SECRET"]
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig.removeprefix("sha256=")):
        raise HTTPException(400, "bad signature")

    event = json.loads(raw)
    event_id = event.get("id") or (event.get("event") or {}).get("id", "")
    if not event_id or event_id in _seen:
        return {"status": "duplicate-ignored"}
    _seen.add(event_id)

    # Order of operations that survives crashes:
    # 1) persist event + state change in ONE transaction
    # 2) THEN acknowledge. Never do side effects before persisting.
    # TODO: with conn.transaction():
    #           upsert event(event_id, payload, status='received')
    #           apply state change to your domain object
    return {"status": "ok"}
'''

NEXT_PAGE = '''// app/(app)/dashboard/page.tsx — Next.js App Router starter
import { redirect } from "next/navigation";

async function getItems() {
  const res = await fetch(`${process.env.API_URL}/api/items`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${process.env.SERVICE_TOKEN ?? ""}` },
  });
  if (!res.ok) redirect("/login");
  return (await res.json()) as { id: string; name: string }[];
}

export default async function Dashboard() {
  const items = await getItems();
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-xl font-semibold">Your workspace</h1>
      <ul className="mt-4 space-y-2">
        {items.map((it) => (
          <li key={it.id} className="rounded border border-zinc-800 p-3">
            {it.name}
          </li>
        ))}
      </ul>
    </main>
  );
}
'''

DOCKER = '''# docker-compose.yml — local dev in one command (all free software)
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
  api:
    build: ./backend
    environment:
      DATABASE_URL: postgres://app:app@db:5432/app
      WEB_ORIGIN: http://localhost:3000
    ports: ["8000:8000"]
    depends_on: [db]
  web:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports: ["3000:3000"]
    depends_on: [api]
volumes:
  pgdata:
'''

ENVFILE = '''# .env.example
DATABASE_URL=postgres://app:app@localhost:5432/app
WEB_ORIGIN=http://localhost:3000
# Payments
@GATEWAY_ENV@
# Compliance (sector-specific secrets)
AUDIT_LOG_SINK=stdout
'''

PAYROLL_CALC = '''# backend/payroll/pay_period.py — US pay-period + OT starter
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class PayPeriod:
    start: date
    end: date
    frequency: str  # weekly | biweekly | semimonthly | monthly


def previous_period(p: PayPeriod) -> PayPeriod:
    d = p.end - p.start + timedelta(days=1)
    return PayPeriod(p.start - d, p.start - timedelta(days=1), p.frequency)


def overtime(hours: float, rate: float, state: str = "tx") -> float:
    # FLSA: 1.5x past 40h/week. CA adds daily OT (8h) + doubletime (12h) —
    # the classic first bug in every homegrown payroll engine.
    if state.lower() == "ca":
        # Weekly model here; add daily-hour inputs before shipping CA.
        return 0.0
    ot = max(0.0, hours - 40)
    return ot * rate * 1.5
'''

GST_CALC = '''# backend/tax/gst.py — India GST split starter (CGST/SGST vs IGST)
from dataclasses import dataclass


@dataclass
class GstLine:
    amount: float  # taxable value in INR
    rate: float    # e.g. 0.18
    intrastate: bool


def split(line: GstLine) -> dict[str, float]:
    tax = round(line.amount * line.rate, 2)
    if line.intrastate:
        return {"cgst": round(tax / 2, 2), "sgst": round(tax / 2, 2), "igst": 0.0}
    return {"cgst": 0.0, "sgst": 0.0, "igst": tax}


def hsn_summary(lines: list[GstLine]) -> dict:
    out: dict[str, float] = {}
    for l in lines:
        out["taxable"] = out.get("taxable", 0.0) + l.amount
        for k, v in split(l).items():
            out[k] = out.get(k, 0.0) + v
    return {k: round(v, 2) for k, v in out.items()}
'''


def build_scaffold(title: str, sector: str, geography: str) -> list[dict]:
    gateway = "razorpay" if geography == "india" else "stripe"
    sig = "X-Razorpay-Signature" if gateway == "razorpay" else "Stripe-Signature"
    files: list[dict] = [
        {"path": "backend/main.py", "language": "python", "content": FASTAPI_MAIN.replace("@TITLE@", title)},
        {"path": "backend/payments.py", "language": "python", "content": WEBHOOK.replace("@GATEWAY@", gateway).replace("@SIG_HEADER@", sig)},
        {"path": "db/schema.sql", "language": "sql", "content": SCHEMA_SQL},
        {"path": "frontend/app/(app)/dashboard/page.tsx", "language": "tsx", "content": NEXT_PAGE},
        {"path": "docker-compose.yml", "language": "yaml", "content": DOCKER},
        {"path": ".env.example", "language": "bash", "content": ENVFILE.replace("@GATEWAY_ENV@", f"{gateway.upper()}_KEY_ID=\n{gateway.upper()}_KEY_SECRET=\nWEBHOOK_SECRET=")},
    ]
    if sector == "payroll" and geography != "india":
        files.append({"path": "backend/payroll/pay_period.py", "language": "python", "content": PAYROLL_CALC})
    if geography == "india":
        files.append({"path": "backend/tax/gst.py", "language": "python", "content": GST_CALC})
    return files
