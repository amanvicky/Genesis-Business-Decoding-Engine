"""Curated jurisdictional compliance knowledge (US federal/state, India central/sector).

This is the offline backbone of Tab 3. Each entry is (item, why, cost, time,
severity) where severity in {critical, high, medium}. Costs are rough planning
ranges, not legal advice — the UI and exports say so explicitly.
"""
from __future__ import annotations

Item = dict  # {item, why, cost, time, severity}

US_FEDERAL: list[Item] = [
    {"item": "EIN (IRS)", "why": "Tax ID required for bank accounts, hiring, and 1099 filings. Free and instant online.", "cost": "$0", "time": "Same day", "severity": "critical"},
    {"item": "Business entity registration (Secretary of State)", "why": "LLC/C-Corp shields personal assets; banks and payment processors require it.", "cost": "$50–$500 (state dependent)", "time": "1–7 days", "severity": "critical"},
    {"item": "FLSA compliance (Fair Labor Standards Act)", "why": "Federal minimum wage, overtime (>40h/week at 1.5x), recordkeeping, child labor rules.", "cost": "$0 (process)", "time": "Ongoing", "severity": "critical"},
    {"item": "Workers' compensation insurance", "why": "Mandatory in nearly every state the moment you hire W-2 employees; penalties for lapse are severe.", "cost": "$500–$2,500/yr (small team)", "time": "1–2 weeks", "severity": "critical"},
    {"item": "EEO-1 / anti-discrimination (Title VII, ADA, ADEA)", "why": "Hiring workflows, job posts, and interview questions are legally constrained from employee #1.", "cost": "$0 (process)", "time": "Ongoing", "severity": "high"},
    {"item": "Sales tax economic nexus tracking", "why": "Post-Wayfair, selling into a state past its threshold ($100k typical) creates filing obligations there — even with zero offices.", "cost": "$0–$600/mo (automation tool)", "time": "Ongoing monitoring", "severity": "high"},
    {"item": "FTC data-security & privacy enforcement", "why": "Section 5 unfairness applies to consumer data handling even without a federal privacy law.", "cost": "$0 (process)", "time": "Ongoing", "severity": "medium"},
    {"item": "IRS 1099-K / 1099-NEC filings", "why": "If you pay contractors ($600+ /yr) or operate a payment platform, reporting is mandatory and processor-shared.", "cost": "$0–$10/yr per form", "time": "Annual (Jan 31)", "severity": "high"},
    {"item": "ACA employer mandate (50+ FTE)", "why": "At 50 full-time equivalents: offer minimum-essential coverage costing ≤ the indexed share (9.5%+ of household income proxy) or pay per-FTE penalties. Tracking must start before you hire #45 — lookback measurement catches fast-growing teams late.", "cost": "$2k–$3k/yr per unapproved FTE if penalized", "time": "at 50 FTE", "severity": "high"},
    {"item": "FMLA (50 employees within 75mi)", "why": "12 weeks unpaid, job-protected leave with restoration duties — HR workflow and tracking obligations appear at 50, not 49.", "cost": "process", "time": "at 50 employees", "severity": "medium"},
    {"item": "COBRA continuation (20+ employees)", "why": "Group health plans at 20+ employees trigger 18–36 month continuation offers with strict notice deadlines — the classic first-HR-audit failure.", "cost": "admin per event", "time": "at 20 employees", "severity": "medium"},
    {"item": "FUTA & credit-reduction states", "why": "Effective FUTA is 0.6% after the 5.4% SUI credit — but federal-loan states (CA, NY, IL historically) add credit-reduction surtaxes that quietly raise per-employee federal UI cost.", "cost": "$42–$63/employee/yr", "time": "annual", "severity": "low"},
]

US_STATES: dict[str, Item] = {
    "California": {
        "item": "CA employer obligations",
        "why": "AB5 ABC-test makes almost everyone an employee, not a contractor. SDI payroll deduction, $16+ minimum wage (2024+), wage statements (Labor Code 226) with 9 mandatory items, final-pay on termination day, mandatory harassment training at 5 employees.",
        "cost": "Highest payroll-compliance burden in the US",
        "time": "Ongoing", "severity": "critical",
    },
    "New York": {
        "item": "NY employer obligations",
        "why": "SUI rates up to ~10%+ for new employers in some industries, Wage Theft Prevention Act notices, paid family leave (0.455% of wages cap), NYC Earned Safe & Sick Time, salary-transparency law for job posts.",
        "cost": "High", "time": "Ongoing", "severity": "critical",
    },
    "Texas": {
        "item": "TX employer obligations",
        "why": "No state income tax withholding; SUI new-employer rate 2.7%; simple final-pay rules. Traditionally the first state payroll platforms expand to after home state.",
        "cost": "Low", "time": "Ongoing", "severity": "medium",
    },
    "Florida": {
        "item": "FL employer obligations",
        "why": "No state income tax; workers' comp mandatory at 4+ employees (1+ in construction); new-employer SUI 2.7%. Low-friction expansion state.",
        "cost": "Low", "time": "Ongoing", "severity": "medium",
    },
    "Washington": {
        "item": "WA employer obligations",
        "why": "WA Cares Fund (0.58% employee payroll tax), Paid Family & Medical Leave premiums split employer/employee, high minimum wage (~$16.28), no income tax but high L&I rates.",
        "cost": "Medium-High", "time": "Ongoing", "severity": "high",
    },
    "Illinois": {
        "item": "IL employer obligations",
        "why": "Paid leave for any reason Act (40h/yr) at 2+ employees, SUI new rate ~3.475%, Chicago minimum wage exceeds state; local taxes (Cook County).",
        "cost": "Medium", "time": "Ongoing", "severity": "medium",
    },
    "Massachusetts": {
        "item": "MA employer obligations",
        "why": "Paid Family & Medical Leave contributions, sick time law, health-insurance mandate (employers 11+), notably aggressive independent-contractor misclassification enforcement.",
        "cost": "Medium-High", "time": "Ongoing", "severity": "high",
    },
    "Colorado": {
        "item": "CO employer obligations",
        "why": "FAMLI payroll premium (0.9% split), wage-transparency in postings, COMPS order pay-stamp rules, sales tax on many SaaS subscriptions.",
        "cost": "Medium", "time": "Ongoing", "severity": "medium",
    },
    "Georgia": {
        "item": "GA employer obligations",
        "why": "Low-friction: SUI 2.7% new rate, no state-mandated paid leave, final pay by next regular payday. Common second state for payroll firms.",
        "cost": "Low", "time": "Ongoing", "severity": "low",
    },
    "New Jersey": {
        "item": "NJ employer obligations",
        "why": "Stacked programs: UI 3.5% new rate, SDI 0.42% + FLI 0.06% (employee-paid), mandatory earned sick leave, NJ minimum wage $15+. Highest program-stack complexity after CA/NY.",
        "cost": "High", "time": "Ongoing", "severity": "high",
    },
    "Virginia": {
        "item": "VA employer obligations",
        "why": "SUI new-employer 2.51%, no state-mandated paid leave, final wages by next regular payday, Virginia Overtime Act adds semi-monthly OT computation.",
        "cost": "Low", "time": "Ongoing", "severity": "low",
    },
    "Maryland": {
        "item": "MD employer obligations",
        "why": "SUI 2.6% new, Earned Sick & Safe Leave (1h per 30h worked), Healthy Working Families Act notices; Montgomery County local minimum wage exceeds state.",
        "cost": "Medium", "time": "Ongoing", "severity": "medium",
    },
    "Tennessee": {
        "item": "TN employer obligations",
        "why": "No state income tax, SUI 2.7% new, final pay next regular payday or by 21 days after separation — among the lowest-friction expansion states.",
        "cost": "Low", "time": "Ongoing", "severity": "low",
    },
    "North Carolina": {
        "item": "NC employer obligations",
        "why": "New-employer SUI 1.0% (lowest tier in the nation), flat 4.5% income withholding, minimal local wage law — a payroll-engine favorite third state.",
        "cost": "Low", "time": "Ongoing", "severity": "low",
    },
    "Oregon": {
        "item": "OR employer obligations",
        "why": "Paid Leave Oregon (1.0% premium, 60/40 employee split), Statewide Transit Tax 0.1%, Portland/Multnomah local income taxes, same-day final pay on firing.",
        "cost": "Medium-High", "time": "Ongoing", "severity": "high",
    },
    "Arizona": {
        "item": "AZ employer obligations",
        "why": "SUI new rate 2.0%, no state-mandated sick leave beyond earned paid sick time (Employer Paid Sick Time Act), minimum wage indexed annually.",
        "cost": "Low", "time": "Ongoing", "severity": "low",
    },
}

# Structured payroll-engine matrix: columns map 1:1 to what a payroll product
# must compute per state (engineers, not lawyers, read this table).
US_PAYROLL_MATRIX: list[dict] = [
    {"state": "California", "income_tax": "progressive to 13.3%", "sui_new": "3.4%", "sdi": "SDI 1.2% (employee)", "paid_leave": "CFRA + PDL", "final_pay": "same day / 72h after quit", "local_taxes": False, "gotcha": "AB5 ABC test; 9-item wage statements"},
    {"state": "New York", "income_tax": "progressive to 10.9%", "sui_new": "4.1%", "sdi": "DBL 0.5% (employee)", "paid_leave": "PFML 0.455% (employee)", "final_pay": "next regular payday", "local_taxes": True, "gotcha": "Yonkers/NYC resident taxes; wage notices"},
    {"state": "Texas", "income_tax": "none", "sui_new": "2.7%", "sdi": "—", "paid_leave": "—", "final_pay": "next regular payday", "local_taxes": False, "gotcha": "cleanest major-state launch"},
    {"state": "Florida", "income_tax": "none", "sui_new": "2.7%", "sdi": "—", "paid_leave": "—", "final_pay": "by next payday", "local_taxes": False, "gotcha": "workers' comp at 4+ employees"},
    {"state": "Washington", "income_tax": "none", "sui_new": "~1.97%", "sdi": "WA Cares 0.58% (employee)", "paid_leave": "PFML ~0.6% split", "final_pay": "72h / next payday", "local_taxes": False, "gotcha": "L&I rates vary by risk class"},
    {"state": "Illinois", "income_tax": "flat 4.95%", "sui_new": "3.475%", "sdi": "—", "paid_leave": "40h Paid Leave for All", "final_pay": "day & date on firing", "local_taxes": True, "gotcha": "Chicago/Cook minimum wage"},
    {"state": "Massachusetts", "income_tax": "5% (+4% surtax)", "sui_new": "2.56%", "sdi": "—", "paid_leave": "PFML 0.88% split", "final_pay": "day of firing / next payday quit", "local_taxes": False, "gotcha": "aggressive 1099 enforcement"},
    {"state": "Colorado", "income_tax": "flat 4.4%", "sui_new": "1.7%", "sdi": "—", "paid_leave": "FAMLI 0.9% split", "final_pay": "immediate / next payday", "local_taxes": True, "gotcha": "SaaS taxable; local minimum wages"},
    {"state": "Georgia", "income_tax": "flat ~5.39%", "sui_new": "2.7%", "sdi": "—", "paid_leave": "—", "final_pay": "next payday", "local_taxes": True, "gotcha": "Atlanta occupational taxes"},
    {"state": "Arizona", "income_tax": "flat 2.5%", "sui_new": "2.0%", "sdi": "—", "paid_leave": "earned sick time", "final_pay": "7 days / next payday", "local_taxes": False, "gotcha": "—"},
    {"state": "New Jersey", "income_tax": "progressive to 10.75%", "sui_new": "3.5%", "sdi": "SDI 0.42% + FLI 0.06% (employee)", "paid_leave": "FLI", "final_pay": "next payday / 15th", "local_taxes": False, "gotcha": "program-stack complexity"},
    {"state": "Virginia", "income_tax": "2.0–5.75%", "sui_new": "2.51%", "sdi": "—", "paid_leave": "—", "final_pay": "next payday", "local_taxes": False, "gotcha": "VA Overtime Act semi-monthly OT"},
    {"state": "Maryland", "income_tax": "2.0–5.75%", "sui_new": "2.6%", "sdi": "—", "paid_leave": "Earned Sick & Safe Leave", "final_pay": "next payday / 7 days", "local_taxes": True, "gotcha": "Montgomery County wage floor"},
    {"state": "Tennessee", "income_tax": "none", "sui_new": "2.7%", "sdi": "—", "paid_leave": "—", "final_pay": "next payday / 21 days", "local_taxes": False, "gotcha": "—"},
    {"state": "North Carolina", "income_tax": "flat 4.5%", "sui_new": "1.0%", "sdi": "—", "paid_leave": "—", "final_pay": "next regular payday", "local_taxes": False, "gotcha": "lowest new-employer SUI"},
    {"state": "Oregon", "income_tax": "4.95–9.9%", "sui_new": "2.4%", "sdi": "—", "paid_leave": "Paid Leave Oregon 1.0% split", "final_pay": "same day fired / 72h quit", "local_taxes": True, "gotcha": "transit tax 0.1%; Portland local tax"},
]

US_SECTOR: dict[str, list[Item]] = {
    "fintech": [
        {"item": "Money Transmitter Licenses (state-by-state)", "why": "Holding/transmitting customer funds across state lines typically requires MTLs in ~49 states + DC. The single biggest capital moat in US fintech — multi-year, seven-figure processes.", "cost": "$100k–$1M+ cumulative", "time": "1–3 years", "severity": "critical"},
        {"item": "FinCEN MSB registration", "why": "Register as Money Services Business within 180 days, AML program required, SAR filing obligations.", "cost": "$0 (filing) / AML program $10k+", "time": "1–3 months", "severity": "critical"},
        {"item": "BSA/AML + KYC program", "why": "CIP under USA PATRIOT Act §326: verify identity, screen OFAC SDN lists, monitor transactions.", "cost": "Vendor KYC $0.50–$2/check + ops", "time": "1–2 months build", "severity": "critical"},
        {"item": "PCI-DSS scope minimization", "why": "Never touch raw PANs; use tokenized gateways (Stripe/Adyen) to stay in SAQ-A instead of full PCI audit.", "cost": "$0 if architected correctly", "time": "Design phase", "severity": "high"},
        {"item": "Bank Sponsorship / BaaS partner", "why": "The realistic zero-license path: FDIC-insured partner bank holds funds; you operate under their program bank's regulatory umbrella (and their scrutiny).", "cost": "Rev-share + program fees", "time": "6–18 months BD cycle", "severity": "critical"},
        {"item": "Regulation E (consumer error resolution)", "why": "Unauthorized-transaction disputes must be resolved in 10 business days; drives your ops headcount math.", "cost": "Ops burden", "time": "Ongoing", "severity": "high"},
    ],
    "payroll": [
        {"item": "Per-state payroll tax registrations", "why": "Each state where an employee works needs: withholding registration, SUI account, and local registrations (OH/PA/KY municipal). Nucleus of why payroll is a brutal first product.", "cost": "$0–$100/state + your time", "time": "2–6 weeks/state", "severity": "critical"},
        {"item": "Third-party sick pay / PEO-style filings", "why": "Reporting agent status (Form 8655) if you file taxes on the client's behalf — required by the IRS.", "cost": "$0 (filing)", "time": "2–4 weeks", "severity": "high"},
        {"item": "Garnishment order handling", "why": "CCAP/child support orders carry statutory deadlines and liability transfer to you as employer/agent.", "cost": "Ops process", "time": "Ongoing", "severity": "high"},
        {"item": "State Unemployment Insurance (SUI) rate engine", "why": "Experience-rating, voluntary contribution optimization, and multi-state 'localization' rules (physical location, residence, telework) drive correctness.", "cost": "Engineering cost", "time": "Months of rules work", "severity": "critical"},
    ],
    "health": [
        {"item": "HIPAA (if touching PHI)", "why": "BAAs with every subprocessor, encryption at rest/in transit, audit logging, breach-notification within 60 days.", "cost": "$10k–$50k initial program", "time": "2–4 months", "severity": "critical"},
        {"item": "State telehealth licensure", "why": "Physicians must be licensed in the patient's state — kills single-provider nationwide models.", "cost": "Per-provider per-state", "time": "Ongoing", "severity": "critical"},
    ],
    "edu": [
        {"item": "FERPA (if serving schools)", "why": "Student-record handling agreements and data-deletion promises are procurement gates for districts.", "cost": "Contract + process", "time": "Per deal", "severity": "high"},
        {"item": "COPPA (if under-13 users)", "why": "Verifiable parental consent, strict data minimization; FTC fines are per-violation.", "cost": "Product redesign if retrofitted", "time": "Design phase", "severity": "critical"},
    ],
    "commerce": [
        {"item": "Sales tax registration & remittance", "why": "Marketplace-facilitator laws or direct nexus; registrations per state past threshold.", "cost": "$0–$600/mo tooling", "time": "Ongoing", "severity": "high"},
        {"item": "FTC Mail/Internet Order Rule + consumer returns policy", "why": "Ship-within-30-days rule, clear refund disclosures; chargeback ratios above ~1% get you dropped by processors.", "cost": "$0 (process)", "time": "Ongoing", "severity": "medium"},
    ],
    "logistics": [
        {"item": "DOT/FMCSA authority (if operating vehicles)", "why": "MC number, UCR fees, drug-testing consortium, ELD mandate.", "cost": "$300–$2,000 initial", "time": "3–6 weeks", "severity": "critical"},
        {"item": "State-by-state warehouse/cannabis-adjacent rules", "why": "Storage of regulated goods (alcohol, nicotine, pharma) changes warehouse licensing per state.", "cost": "Varies", "time": "Per state", "severity": "medium"},
    ],
    "saas": [
        {"item": "SOC 2 Type II readiness (enterprise sales gate)", "why": "Not legally required but a de-facto procurement requirement past ~$10k AC; 3–12 month evidence window.", "cost": "$15k–$60k (audit + tooling)", "time": "6–12 months", "severity": "high"},
        {"item": "State privacy laws (CCPA/CPRA, VCDPA, CPA...)", "why": "Consumer-facing apps past revenue/record thresholds need notice, opt-out (sale/share), and deletion workflows.", "cost": "Product + legal process", "time": "1–2 months", "severity": "high"},
    ],
}

INDIA_CENTRAL: list[Item] = [
    {"item": "Company incorporation (MCA: DIN + DSC)", "why": "Pvt Ltd (SPICe+) needed for funded startups; LLP or OPC cheaper for services. DSC takes days; name approval is where founders lose weeks.", "cost": "₹7k–₹20k (professional fees)", "time": "1–3 weeks", "severity": "critical"},
    {"item": "PAN + TAN", "why": "Corporate PAN and TDS deduction TAN arrive with incorporation but must be activated for filings.", "cost": "₹0 (bundled)", "time": "1–2 weeks", "severity": "critical"},
    {"item": "GST registration", "why": "Mandatory above ₹40L goods / ₹20L services turnover; mandatory regardless if selling inter-state or via marketplaces. SaaS exports are zero-rated with LUT but input credit needs GST.", "cost": "₹0 (filing) / ₹2k–₹5k professional", "time": "3–7 working days", "severity": "critical"},
    {"item": "Shops & Establishments registration", "why": "State-level labour registration needed before hiring even employee #1 in most states; basis of many other labour filings.", "cost": "₹1k–₹10k", "time": "1–4 weeks (state dependent)", "severity": "critical"},
    {"item": "EPF (Provident Fund)", "why": "Mandatory at 20+ employees: 12% employer + 12% employee of basic wages. Joining EPFO mid-growth triggers arrears + damages.", "cost": "12% of PF wages per employee", "time": "Register at 20th employee", "severity": "critical"},
    {"item": "ESI (Employee State Insurance)", "why": "Mandatory at 10+ employees earning ≤₹21k/month: 3.25% employer + 0.75% employee. Commonly missed by startups until inspection.", "cost": "4% of eligible wages", "time": "Register at 10th employee", "severity": "critical"},
    {"item": "Professional Tax (state slab)", "why": "State-level payroll deduction (e.g., Maharashtra ₹200/mo max slab; Karnataka ₹200/mo); registration + monthly/annual returns.", "cost": "₹200/employee/mo (typical max)", "time": "State dependent", "severity": "high"},
    {"item": "Labour Welfare Fund (state)", "why": "Statutory contribution in states like MH, KA, TN — deducted and remitted per state schedule.", "cost": "Small per-employee", "time": "Half-yearly/annual", "severity": "medium"},
    {"item": "POSH Act compliance ( Sexual Harassment )", "why": "Internal Committee MANDATORY at 10+ employees; annual constitution + awareness + annual report filing. Non-compliance fine up to ₹50k and repeat offence can cancel registration.", "cost": "₹5k–₹15k (training/setup)", "time": "Before 10th employee", "severity": "critical"},
    {"item": "DPDP Act 2023 readiness", "why": "India's first cross-sector data-protection law: consent notices, data-principal rights, breach reporting to DPB. Rules being operationalized — design consent flows now.", "cost": "Product + process", "time": "Design phase", "severity": "high"},
    {"item": "TDS compliance (192, 194 series)", "why": "Salary TDS 192, contractor 194C/194J, rent 194-I; quarterly 26Q returns + Form 16/16A issuance. Late filing: ₹200/day penalty.", "cost": "₹0 / accountant time", "time": "Quarterly", "severity": "critical"},
    {"item": "MSME Udyam registration", "why": "Free, unlocks 45-day payment protection ( MSMED Act), priority lending, and tender benefits. Zero downside for a small startup.", "cost": "₹0", "time": "1 day", "severity": "medium"},
    {"item": "The four Labour Codes (Wages / IR / Social Security / OSH)", "why": "Enacted 2019-20 to consolidate 29 central laws; state rules are notifying in waves. The 'wages' definition change will re-base PF/gratuity math — build payroll as configurable rules, never hardcoded formulas.", "cost": "engineering design", "time": "watch state notifications", "severity": "high"},
    {"item": "Payment of Gratuity Act", "why": "15/26 days of wages per completed year after 5 years of service; payroll must accrue the liability from day 1 at establishments with 10+ employees.", "cost": "employer-funded accrual", "time": "at eligibility", "severity": "high"},
    {"item": "Payment of Bonus Act", "why": "Statutory bonus of 8.33–20% of wages for employees earning ≤₹21,000/month at 10+ employees — the most commonly missed SMB payroll obligation.", "cost": "employer-funded", "time": "within 8 months of FY close", "severity": "medium"},
    {"item": "Code on Wages floor wage", "why": "The notified floor wage supersedes state minimum-wage schedules as codes come into force; payroll bands must track both during the transition.", "cost": "process", "time": "ongoing", "severity": "medium"},
    {"item": "GST on OIDAR/SaaS (18%) + export LUT", "why": "B2C foreign SaaS sales trigger OIDAR registration; exports are zero-rated only with a LUT filed — without it, 18% GST blocks working capital on every foreign invoice.", "cost": "₹0 filing", "time": "1–3 days", "severity": "high"},
]

INDIA_SECTOR: dict[str, list[Item]] = {
    "fintech": [
        {"item": "RBI Payment Aggregator (PA) authorization", "why": "Aggregating funds for merchants requires RBI PA licence: ₹15cr net worth at application (₹25cr at scale), escrow account with eligible bank, annual audit. The wall that killed many India payment startups.", "cost": "₹15cr net worth + ₹50L+ process", "time": "12–24 months", "severity": "critical"},
        {"item": "Payment Gateway instead of PA licence", "why": "The zero-licence path: integrate Razorpay/Cashfree/PayU as sub-merchant; settlement flows through their licence. You never touch customer funds.", "cost": "TDR ~1.5–2.3% per transaction", "time": "1–2 weeks KYC", "severity": "critical"},
        {"item": "PMLA + RBI KYC (Master Direction)", "why": "Customer due diligence, UBO checks, transaction monitoring; Nodal/APO officer appointment for escalations.", "cost": "Ops process", "time": "1–2 months", "severity": "critical"},
        {"item": "NPCI / UPI rules (if touching UPI)", "why": "TPAP onboarding needs sponsor bank + NPCI approval; market-share caps and 30-min reversal rules are enforced.", "cost": "Sponsor-bank economics", "time": "3–9 months", "severity": "high"},
        {"item": "RBI Digital Lending Guidelines (if lending)", "why": "Default Loss Guarantees capped, disbursal only via bank's account, LSP fee-payment restrictions, data storage in India.", "cost": "Compliance program", "time": "Quarterly audits", "severity": "critical"},
    ],
    "payroll": [
        {"item": "State-wise PT registration (MH/KA/WB each differ)", "why": "Payroll product must handle state PT slabs, LWF schedules, and form numbers (e.g., MH: PTRC; KA: e-Prerana).", "cost": "Rules engineering", "time": "Per state", "severity": "critical"},
        {"item": "CLRA (Contract Labour Act) at establishments", "why": "If deploying contract staffing: licensing at principal employer + contractor side at 20+ contract workers.", "cost": "Licence fees", "time": "4–8 weeks", "severity": "high"},
        {"item": "Maternity Benefit Act", "why": "26 weeks paid leave funded by employer at 10+ employees — a cost line payroll systems must model.", "cost": "Employer-funded", "time": "Ongoing", "severity": "high"},
    ],
    "commerce": [
        {"item": "FSSAI licence (food)", "why": "Basic/State/Central tier by turnover; marketplace delisting risk without it.", "cost": "₹100–₹7,500/yr", "time": "1–4 weeks", "severity": "critical"},
        {"item": "Legal Metrology (packaged goods) + BIS (electronics)", "why": "MRP/labelling declarations and ISI marks enforced on marketplaces.", "cost": "₹500–₹5,000 + product testing", "time": "2–6 weeks", "severity": "high"},
        {"item": "E-commerce marketplace TCS under GST", "why": "Platforms deduct TCS; your reconciliation must account for it or books drift monthly.", "cost": "Process", "time": "Monthly", "severity": "medium"},
    ],
    "health": [
        {"item": "Clinical Establishment / state medical registration", "why": "Operating diagnostics or telemedicine touches state CE Acts and NMC telemedicine guidelines 2020.", "cost": "Registration fees", "time": "State dependent", "severity": "critical"},
        {"item": "DPDP + ABDM integration norms (health data)", "why": "ABDM Health Data Management Policy requires consent-artifact handling for ABHA-linked records.", "cost": "Engineering", "time": "Design phase", "severity": "high"},
    ],
    "edu": [
        {"item": "Ed-specific advertising & fee rules", "why": "ASCI guidelines on outcome claims; some states regulate coaching-fee refunds (e.g., Maharashtra).", "cost": "Copy review", "time": "Ongoing", "severity": "medium"},
        {"item": "COPPA-equivalent: DPDP verifiable parental consent for minors", "why": "Under-18 processing needs parental consent + no tracking/targeted ads at children under DPDP.", "cost": "Product flow", "time": "Design phase", "severity": "high"},
    ],
    "saas": [
        {"item": "Export controls & cross-border data (SaaS)", "why": "Selling globally from India: RBI LUT for zero-rated exports, FEMA current-account compliance for receiving foreign investment.", "cost": "₹0 (LUT) / CA fees", "time": "Annual", "severity": "medium"},
        {"item": "Shops & Establishments 'IT/ITeS' exemption path", "why": "Karnataka/Maharashtra IT-sector exemptions still need registration paperwork; skipping both fails audits.", "cost": "Filing fees", "time": "2–4 weeks", "severity": "medium"},
    ],
    "logistics": [
        {"item": "e-Way Bill + E-invoicing thresholds", "why": "E-invoicing mandatory above ₹5cr turnover; e-way bill rules govern interstate goods movement.", "cost": "ERP/tooling", "time": "At threshold", "severity": "high"},
        {"item": "State transport permits", "why": "Contract carriage permits, National Permit ₹16.5k/yr for pan-India trucks.", "cost": "₹16.5k/vehicle/yr (NP)", "time": "Per vehicle", "severity": "high"},
    ],
}

# Expansion order heuristics for a US payroll/employer-of-record style product.
US_EXPANSION_ORDER = [
    ("Texas", "No income-tax withholding, 2.7% new-employer SUI, simple final-pay."),
    ("Florida", "No income tax, low registration friction, large employer base."),
    ("Georgia", "Low rates, no extra mandates, follows TX/FL pattern in most engines."),
    ("Arizona", "2.0% SUI, minimal local complexity."),
    ("North Carolina", "Flat 2.5% SUI-ish new rate, clean rules."),
    ("Colorado / Washington / Illinois", "Mid-complexity: FAMLI/WA Cares/Paid Leave add payroll-line engines."),
    ("New York", "High SUI + wage-notice + NYC local rules — build once engine is battle-tested."),
    ("California", "Last: ABC test, SDI, itemized wage statements, highest engineering + audit cost."),
]


def landmines_for(sector: str, geography: str) -> list[Item]:
    out: list[Item] = []
    if geography in ("us", "global"):
        out += US_FEDERAL
        out += US_SECTOR.get(sector, US_SECTOR["saas"])
    if geography in ("india", "global"):
        out += INDIA_CENTRAL
        out += INDIA_SECTOR.get(sector, INDIA_SECTOR["saas"])
    return out
