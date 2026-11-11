# Host the cloud demo on Hugging Face Spaces (free, ~10 minutes)

One Docker container: FastAPI serves both the API and the static dashboard on
port 7860. Hugging Face hosts it free; the Space sleeps after ~48h idle and
wakes on the next visit.

> Honest expectations: this is the **evidence-thin demo**. Search engines
> rate-limit shared cloud IPs, so live-search lanes return little there. It
> exists so people can see the UI and the knowledge-base depth before
> installing locally — the real product is the installer.

## Steps

1. Create a free account at https://huggingface.co (email only).
2. Click **New → Space** → name it `genesis-demo` → SDK: **Docker** → Blank →
   Public → Create Space.
3. Clone the empty Space and pull Genesis into it (PowerShell):

```powershell
git clone https://huggingface.co/spaces/YOURNAME/genesis-demo
cd genesis-demo
git remote add gh https://github.com/amanvicky/Genesis-Business-Decoding-Engine.git
git fetch gh main
git checkout gh/main -- backend frontend README.md LICENSE
copy ..\Genesis-Business-Decoding-Engine\deploy\Dockerfile Dockerfile
copy ..\Genesis-Business-Decoding-Engine\deploy\space-README.md README.md
```

   (adjust the `..\Genesis-Business-Decoding-Engine` path to wherever your
   local copy of the repo sits — or `git clone` it next to the Space first)

4. Push (HF asks for your **username** and a **token** from
   https://huggingface.co/settings/tokens — a write token):

```powershell
git add -A
git commit -m "genesis demo"
git push
```

5. The Space builds (~5-8 minutes, first time) and then serves the dashboard
   at `https://huggingface.co/spaces/YOURNAME/genesis-demo`.

## Updating the demo later

Repeat step 3's `git fetch gh main` + `git checkout gh/main -- backend frontend`
+ `copy deploy/*` + commit + push.

## Run the same image anywhere else

```bash
docker build -f deploy/Dockerfile -t genesis-demo .
docker run -p 7860:7860 genesis-demo
# open http://localhost:7860
```

Same single-port architecture, no Hugging Face involved.
