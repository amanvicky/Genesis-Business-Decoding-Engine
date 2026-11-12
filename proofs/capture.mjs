// Real screenshot capture for the proofs folder.
// Drives the LIVE app in headless Edge (puppeteer-core, no browser download):
//   node capture.mjs <outDir> <subject> <landingCapturesDir>
// Requires: npm i puppeteer-core  (in any scratch dir) + Edge + the stack running.
// Writes the 14-shot proofs tour to <outDir> AND refreshes the landing page's
// static captures (frontend/public/captures) from the same decode, then reloads
// the landing so 01 shows the fresh hero.
import puppeteer from "puppeteer-core";

const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const OUT = process.argv[2] || ".";
const SUBJECT = process.argv[3] || "Notion";
const CAPS = process.argv[4] || "../frontend/public/captures";

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: true,
  args: ["--window-size=1440,1000", "--hide-scrollbars"],
  defaultViewport: { width: 1440, height: 1000, deviceScaleFactor: 2 },
});
const page = await browser.newPage();
await page.setCacheEnabled(false); // the landing must serve the captures we just re-shot
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shot = (name, dir = OUT) => page.screenshot({ path: `${dir}/${name}.png` });

// 01 comes last — start the decode, catch the console mid-stream
await page.goto("http://localhost:3000", { waitUntil: "networkidle2", timeout: 60000 });
await sleep(1800);
await page.type("textarea", SUBJECT, { delay: 10 });
await page.evaluate(() => document.querySelector("form").requestSubmit());
await sleep(15000); // mid-recon: the console has real depth by now
await shot("02_agent_console_live");

// wait for the full decode: all 13 tab buttons exist in the report rail
await page.waitForFunction(
  `(() => {
    const re = /^(◈|▦|⚖|☠|◷|∑|⚡|◉|☯|▲|❖|§|⚔)\\s*\\d+$/;
    return [...document.querySelectorAll("button")].filter((b) => re.test((b.textContent || "").replace(/\\s+/g, " ").trim())).length >= 13;
  })()`,
  { timeout: 600000, polling: 2500 },
);
await sleep(1500);

// click a tab by its number and shoot it
const clickTab = async (n) => {
  await page.evaluate((nn) => {
    const tabs = [...document.querySelectorAll("button")].filter(
      (b) => /^(◈|▦|⚖|☠|◷|∑|⚡|◉|☯|▲|❖|§|⚔)\s*\d+$/.test((b.textContent || "").replace(/\s+/g, " ").trim()),
    );
    const btn = tabs.find((b) => parseInt((b.textContent || "").replace(/\D+/g, ""), 10) === nn);
    if (btn) btn.click();
    return tabs.length;
  }, n);
  await sleep(900);
};

const tabsShot = {
  "03_report_structural": 1,
  "04_feature_binary_roadmap": 2,
  "05_compliance_matrix": 3,
  "06_premortem_post_mortems": 4,
  "07_pricing_observed": 6,
  "08_product_dna": 9,
  "09_stock_performance": 10,
  "10_public_record": 12,
  "11_adversary_redteam": 13,
};
for (const [name, n] of Object.entries(tabsShot)) {
  await clickTab(n);
  await shot(name);
}

// refresh the landing page's static captures (hero panel + "the brief, tab by tab" strip)
for (const [n, name] of [[1, "tab_structural"], [3, "tab_compliance"], [9, "tab_dna"], [10, "tab_markets"], [11, "tab_deepdive"]]) {
  await clickTab(n);
  await shot(name, CAPS);
}
await shot("report_deepdive", CAPS); // still on tab 11

// 12 — the advisor, asked a real research question
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Ask Genesis"));
  if (btn) btn.click();
});
await sleep(800);
await page.type('input[placeholder*="What kills companies"]', "what kills companies like this?", { delay: 5 });
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").trim() === "Ask");
  if (btn) btn.click();
});
await sleep(4000);
await shot("12_ask_genesis_advisor");
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => b.getAttribute("aria-label") === "Close advisor");
  if (btn) btn.click();
});
await sleep(500);

// 13 — verdict protocol v2: two research gates computed from the evidence, no quiz
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").trim() === "Verdict");
  if (btn) btn.click();
});
await sleep(800);
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Compute verdict"));
  if (btn) btn.click();
});
await sleep(2500);
await shot("13_verdict_protocol");

// 01 — the fresh landing (serving the captures we just re-shot)
await page.goto("http://localhost:3000", { waitUntil: "networkidle2", timeout: 60000 });
await sleep(1800);
await shot("01_landing_input_panel");

// 14 — the battle: a raw idea against the incumbent, by URL
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Battle ideas"));
  if (btn) btn.click();
});
await sleep(500);
let slots = await page.$$("form input");
await slots[0].type("AI meeting notes for sales teams", { delay: 5 });
await page.evaluate(() => {
  const chips = [...document.querySelectorAll("button")].filter((b) => (b.textContent || "").trim() === "URL");
  if (chips[1]) chips[1].click(); // slot B becomes the incumbent's URL
});
await sleep(400);
slots = await page.$$("form input");
await slots[1].type("https://fireflies.ai", { delay: 5 });
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Run the battle"));
  if (btn) btn.click();
});
// two full sequential decodes, then the matrix posts its verdict line
// (the heading renders CSS-uppercased — innerText is the transformed text)
await page.waitForFunction(() => document.body.innerText.toUpperCase().includes("VERDICT —"), {
  timeout: 1500000,
  polling: 5000,
});
await sleep(1500);
await shot("14_battle_matrix");

await browser.close();
console.log("captured 14 proofs + 7 landing captures");
