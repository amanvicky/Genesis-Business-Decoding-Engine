// Real screenshot capture for the proofs folder.
// Drives the LIVE app in headless Edge (puppeteer-core, no browser download):
//   node capture.mjs <outDir> <subject>
// Requires: npm i puppeteer-core  (in any scratch dir) + Edge + the stack running.
import puppeteer from "puppeteer-core";

const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const OUT = process.argv[2] || ".";
const SUBJECT = process.argv[3] || "Apple";

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: true,
  args: ["--window-size=1440,1000", "--hide-scrollbars"],
  defaultViewport: { width: 1440, height: 1000 },
});
const page = await browser.newPage();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shot = (name) => page.screenshot({ path: `${OUT}/${name}.png` });

// 01 — landing
await page.goto("http://localhost:3000", { waitUntil: "networkidle2", timeout: 60000 });
await sleep(1800);
await shot("01_landing_input_panel");

// start the decode, catch the console mid-stream
await page.type("textarea", SUBJECT, { delay: 10 });
await page.evaluate(() => document.querySelector("form").requestSubmit());
await sleep(4500);
await shot("02_agent_console_live");

// wait for the full decode
await page.waitForFunction(
  () => document.body.innerText.match(/1[0-9]\/1[0-9]/) !== null && document.body.innerText.includes("sections,"),
  { timeout: 420000, polling: 2500 },
);
await sleep(1500);

// click a tab by its number and shoot it
const clickTab = async (n) => {
  await page.evaluate((nn) => {
    const tabs = [...document.querySelectorAll("button")].filter((b) =>
      /^(◈|▦|⚖|☠|◷|∑|⚡|▮|⇄|⌘|◉|➤|◎|☯|✦|▲|⚔)\s*\d+$/.test((b.textContent || "").replace(/\s+/g, " ").trim()),
    );
    // textContent is like "◈1" (icon and number concatenated) - parse the digits
    const btn = tabs.find((b) => parseInt((b.textContent || "").replace(/\D+/g, ""), 10) === nn);
    if (btn) btn.click();
    return tabs.length;
  }, n);
  await sleep(900);
};

const tabsShot = { "03_report_structural": 1, "04_feature_binary_roadmap": 2, "05_compliance_matrix": 3,
  "06_pricing_sandbox": 6, "07_burn_calculator": 8, "09_market_sizing": 13,
  "10_product_dna": 14, "12_founder_school": 15, "11_stock_performance": 16, "08_adversary_redteam": 17 };
for (const [name, n] of Object.entries(tabsShot)) {
  await clickTab(n);
  await shot(name);
}

// 13 — the advisor, asked a real question
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Ask Genesis"));
  if (btn) btn.click();
});
await sleep(800);
await page.type('input[placeholder*="Should I raise"]', "what is churn?", { delay: 5 });
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").trim() === "Ask");
  if (btn) btn.click();
});
await sleep(4000);
await shot("13_ask_genesis_advisor");
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => b.getAttribute("aria-label") === "Close advisor");
  if (btn) btn.click();
});
await sleep(500);

// 14 — the verdict protocol, answered and computed
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Verdict"));
  if (btn) btn.click();
});
await sleep(800);
await page.evaluate(() => {
  const all = [...document.querySelectorAll("button")];
  const yes = all.filter((b) => (b.textContent || "").trim() === "yes");
  const no = all.filter((b) => (b.textContent || "").trim() === "no");
  [0, 1, 2].forEach((i) => yes[i] && yes[i].click());
  [3, 4].forEach((i) => no[i] && no[i].click());
  if (yes[5]) yes[5].click();
});
await sleep(500);
await page.evaluate(() => {
  const btn = [...document.querySelectorAll("button")].find((b) => (b.textContent || "").includes("Compute verdict"));
  if (btn) btn.click();
});
await sleep(2500);
await shot("14_verdict_protocol");

await browser.close();
console.log("captured 14 screenshots to", OUT);
