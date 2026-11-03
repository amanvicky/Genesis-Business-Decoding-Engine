"""Market-sizing & capital KB (Tab 14 backbone).

Planning-grade, bottom-up numbers with the basis stated per row — every figure
is an editable ASSUMPTION, not a fact. `buying_units` counts what actually pays
(companies for B2B, individuals for B2C); ARPA comes from the pricing/financial
tabs at runtime, so TAM/SAM/SOM recompute when the founder edits the sandbox.

Bases are deliberately conservative order-of-magnitude estimates from public
industry sources; the point is a defensible starting model, not precision.
"""
from __future__ import annotations

MarketBase = dict

# sector -> geo -> {buying_units, unit, basis}
MARKET_BASES: dict[str, dict[str, MarketBase]] = {
    "payroll": {
        "us": {"buying_units": 1_600_000, "unit": "employer firms (10–500 employees)",
               "basis": "US Census SUSB: ~6M employer firms; ~1.6M in the 10–500 band that outsource payroll in some form"},
        "india": {"buying_units": 620_000, "unit": "establishments running formal payroll",
                  "basis": "EPF-registered establishments + formal-sector SMEs (~6.3Cr EPF members across ~6L establishments; MSME universe far larger but informal)"},
        "global": {"buying_units": 8_000_000, "unit": "employer firms in outsourced-payroll markets",
                   "basis": "US + EU + India formal establishments using payroll providers"},
    },
    "fintech": {
        "us": {"buying_units": 33_000_000, "unit": "SMBs + consumers in the wedge segment",
               "basis": "~33M US SMBs; consumer wallets far larger — size the specific wedge, not all fintech"},
        "india": {"buying_units": 64_000_000, "unit": "MSMEs digitizing payments/finance",
                  "basis": "Udyam-registered + GST-registered enterprises (~64L GST registrations as base for B2B fintech)"},
        "global": {"buying_units": 120_000_000, "unit": "digitally-active SMBs",
                   "basis": "World Bank SME universe × digital-adoption estimates"},
    },
    "commerce": {
        "us": {"buying_units": 2_500_000, "unit": "online sellers / retail SMBs",
               "basis": "Amazon/eBay/Shopify seller counts + independent retail"},
        "india": {"buying_units": 4_500_000, "unit": "SMEs selling online or ready to",
                  "basis": "ONDC + marketplace seller counts + digital-ready retail"},
        "global": {"buying_units": 12_000_000, "unit": "online sellers",
                   "basis": "Shopify + marketplace seller universes"},
    },
    "health": {
        "us": {"buying_units": 260_000, "unit": "clinics/practices (non-hospital)",
               "basis": "US physician practices + dental/urgent care sites"},
        "india": {"buying_units": 900_000, "unit": "clinics, nursing homes, diagnostic labs",
                  "basis": "registered clinical establishments; private majority"},
        "global": {"buying_units": 2_000_000, "unit": "private practices & clinics",
                  "basis": "OECD private-practice densities across major markets"},
    },
    "edu": {
        "us": {"buying_units": 130_000, "unit": "K12 schools + tutoring/edtech buyers",
               "basis": "public+private schools; districts gate most B2G sales"},
        "india": {"buying_units": 1_500_000, "unit": "private schools + coaching institutes",
                  "basis": "UDISE+ private schools (~5L) + coaching centers"},
        "global": {"buying_units": 4_000_000, "unit": "schools & institutes",
                  "basis": "UNESCO school counts × private share"},
    },
    "devtools": {
        "us": {"buying_units": 500_000, "unit": "engineering teams (5+ devs)",
               "basis": "US software employment / average team size"},
        "india": {"buying_units": 180_000, "unit": "product & services engineering teams",
                  "basis": "NASSCOM member universe estimate + GCC teams"},
        "global": {"buying_units": 1_800_000, "unit": "engineering teams",
                  "basis": "global developer population (~27M) ÷ typical team size"},
    },
    "saas": {
        "us": {"buying_units": 8_000_000, "unit": "SMBs buying horizontal SaaS",
               "basis": "~33M US SMBs × ~25% software-buying share for the wedge"},
        "india": {"buying_units": 10_000_000, "unit": "SMBs adopting business software",
                  "basis": "MSME universe × digitization share"},
        "global": {"buying_units": 30_000_000, "unit": "SMB software buyers",
                  "basis": "global SMB universe × software-adoption share"},
    },
    "logistics": {
        "us": {"buying_units": 200_000, "unit": "shippers, 3PLs, fleets",
               "basis": "FMCSA active carriers + shipper base"},
        "india": {"buying_units": 400_000, "unit": "transporters, fleets, 3PLs",
                  "basis": "registered goods carriers + fleet operators"},
        "global": {"buying_units": 1_500_000, "unit": "logistics operators",
                  "basis": "registered carriers/forwarders across major trade blocs"},
    },
    "generic": {
        "us": {"buying_units": 5_000_000, "unit": "SMB buyers in the wedge",
               "basis": "generic SMB base — refine the wedge and re-size"},
        "india": {"buying_units": 8_000_000, "unit": "SMB buyers in the wedge",
                  "basis": "generic MSME base — refine the wedge and re-size"},
        "global": {"buying_units": 20_000_000, "unit": "SMB buyers in the wedge",
                   "basis": "generic global SMB base — refine the wedge and re-size"},
    },
}

# Bottom-up adoption the founder must EARN, not a forecast: year-3 3% of the
# serviceable base is already an outlier outcome for a bootstrapped team.
ADOPTION_CURVE = {1: 0.005, 2: 0.015, 3: 0.03}

# Geo-typical pre-seed/seed economics (planning-grade; edit before a real raise).
FUNDING_NORMS = {
    "us": {"pre_seed_cap_usd": 3_000_000, "seed_valuation_usd": 12_000_000,
           "note": "US pre-seed SAFE caps $2–6M; seed priced rounds $8–20M post. Dilution 10–20% per round."},
    "india": {"pre_seed_cap_usd": 1_500_000, "seed_valuation_usd": 6_000_000,
              "note": "India pre-seed ₹5–12Cr caps (SAFE/CCPS); seed ₹30–60Cr post. Dilution 15–25% per round; CCD/SAFE documents standard."},
    "global": {"pre_seed_cap_usd": 2_000_000, "seed_valuation_usd": 8_000_000,
               "note": "Blended global norms; check localSAFE/CCPS conventions."},
}
