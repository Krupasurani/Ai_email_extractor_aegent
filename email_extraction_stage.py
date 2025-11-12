

########################################################################almost
#!/usr/bin/env python3
"""
smart_email_finder_failover.py

Universal email finder with a robust LLM-powered failover layer.

Usage:
    python smart_email_finder_failover.py <homepage_url> "<person_name>"

Behavior:
 - Normal flow: detect directory, choose profile, extract email (as in v5).
 - FAILOVER: If profile not found or no emails extracted, run a site-wide search:
     * Render homepage and a short list of internal pages (links),
     * Extract text + run regex,
     * Ask the LLM (strict JSON output) to find explicit emails that are actually present and tied to the person.
 - LLM is instructed NOT to guess. If it cannot find explicit emails, it returns [].

Note: Run responsibly. Respect robots.txt & site rate limits when using at scale.
"""

import os, re, sys, json, time, requests, difflib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from groq import Groq

# -------------- config --------------
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    print("Missing GROQ_API_KEY in .env")
    sys.exit(1)

MODEL = "llama-3.1-8b-instant"
client = Groq(api_key=GROQ_KEY)

UA = "SmartEmailFinder/1.0 (+https://github.com/)"
REQUEST_TIMEOUT = 15
MAX_SITE_PAGES = 25           # how many internal pages to fetch in failover
PLAYWRIGHT_SCROLL_TRIES = 12  # when scrolling dynamic directories
# ------------------------------------

# ---------- utility functions ----------
def render_page_html_and_links(url, headless=True, scroll=False, scroll_tries=5):
    """Render page with Playwright, return HTML and absolute links."""
    print(f"🌐 Render: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(user_agent=UA)
        page.goto(url, wait_until="networkidle", timeout=45000)
        
        if scroll:
            last_h = 0
            for _ in range(scroll_tries):
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(800)
                new_h = page.evaluate("document.body.scrollHeight")
                if new_h == last_h:
                    break
                last_h = new_h
        html = page.content()
        # gather links
        els = page.query_selector_all("a[href]")
        links = []
        for a in els:
            try:
                href = a.get_attribute("href")
                if href:
                    links.append(urljoin(url, href.split("#")[0]))
            except Exception:
                continue
        browser.close()
    return html, list(dict.fromkeys(links))  # preserve unique order

def simple_fetch_html_links(url):
    """Fast HTTP GET + parse links (fallback)"""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return "", []
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href")
            if href:
                links.append(urljoin(url, href.split("#")[0]))
        return r.text, list(dict.fromkeys(links))
    except Exception:
        return "", []

def extract_emails_from_text(text):
    """Return list of unique emails found via regex."""
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return list(dict.fromkeys([e.lower() for e in emails]))

def domain_only(url):
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"
    except:
        return url

# ---------- AI helpers (strict JSON) ----------
def llm_sitewide_search(name, pages): 
    """
    pages: list of dict {url, text_snippet}
    Instruct LLM to search these snippets for explicit emails belonging to `name`.
    IMPORTANT: LLM MUST return strict JSON:
      {"results": [{"email": "...", "url": "...", "context": "...", "confidence": 0.0}, ...]}
    - It must NOT invent any email.
    - If nothing found, return {"results": []}
    """
    # Build compact context (truncate each snippet)
    sample_data = []
    for p in pages:
        snippet = p["text"][:2000].replace("\n", " ")
        sample_data.append({"url": p["url"], "text": snippet})
    prompt = f"""
You are a careful web-extraction assistant. You will be given a list of page url + text snippets.
Task: Find any e-mail addresses that are explicitly present in the provided text snippets that clearly belong to the person named: "{name}".

Rules (must follow):
1) Do NOT guess or invent. Only return emails that literally appear in the supplied text snippets.
2) Return output ONLY as JSON matching exactly this schema:
   {{
     "results": [
       {{
         "email": "<email address exactly as found>",
         "url": "<page url where it appears>",
         "context": "<short text (<=200 chars) around the email>",
         "confidence": <float 0.0-1.0 — 1.0 means exact match / email shown with name nearby>
       }},
       ...
     ]
   }}
3) If you find no explicit emails in the provided snippets, return: {"results": []}
4) When deciding confidence:
   - If the snippet contains the person's full name near the email, use confidence 0.95-1.0.
   - If the snippet contains only last name or initials near the email, use 0.6-0.85.
   - If email is present but no nearby name, use 0.3-0.6.
5) For context include up to ~200 characters surrounding the email.

Here are the pages (url + snippet). Keep JSON machine-parseable only.
Pages:
{json.dumps(sample_data, ensure_ascii=False)[:38000]}
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=800,
    )
    raw = resp.choices[0].message.content.strip()
    # extract JSON object from raw
    try:
        jtext = re.search(r"\{.*\}", raw, re.S).group(0)
        data = json.loads(jtext)
        # normalize emails lower-case
        for r in data.get("results", []):
            r["email"] = r["email"].strip().lower()
            r["context"] = r.get("context","")[:300]
            r["url"] = r.get("url","")
            r["confidence"] = float(r.get("confidence", 0.0))
        return data.get("results", [])
    except Exception as e:
        print("LLM failed to return strict JSON or parsing failed:", e)
        return []

# ---------- main failover routine ----------
def sitewide_failover_search(home_url, person_name, max_pages=MAX_SITE_PAGES):
    """
    1) Render homepage, gather internal links (breadth-first up to max_pages)
    2) Render each candidate page (Playwright) and collect text snippets
    3) Run regex to gather any emails across pages
    4) If regex finds candidate emails, pass snippets+emails to LLM for final decision
    """
    base = domain_only(home_url)
    print("🔎 Failover: sitewide search starting from homepage...")

    # 1) render home quickly, collect candidate links
    html, links = render_page_html_and_links(home_url, headless=True, scroll=False)
    internal_links = [l for l in links if urlparse(l).netloc == urlparse(home_url).netloc]
    # keep order, limit
    candidate_links = internal_links[: max_pages]
    # always include home_url first
    if home_url not in candidate_links:
        candidate_links.insert(0, home_url)

    pages = []
    seen = set()
    # 2) render each candidate and extract text
    for url in candidate_links:
        if url in seen:
            continue
        seen.add(url)
        try:
            # for directories/likely dynamic pages, scroll briefly
            scroll = any(k in url.lower() for k in ("/people", "/professionals", "/team", "/about"))
            html, _ = render_page_html_and_links(url, headless=True, scroll=scroll, scroll_tries=4)
            # extract visible text
            soup = BeautifulSoup(html, "html.parser")
            for s in soup(["script","style","noscript","svg"]):
                s.decompose()
            text = soup.get_text(" ", strip=True)
            snippet = text[:5000]
            pages.append({"url": url, "text": snippet})
        except Exception as e:
            # fallback fetch
            t, _ = simple_fetch_html_links(url)
            pages.append({"url": url, "text": (t or "")[:5000]})
        # polite delay
        time.sleep(0.6)

    # 3) quick regex pass across page texts
    found_emails = {}
    for p in pages:
        es = extract_emails_from_text(p["text"])
        for e in es:
            found_emails.setdefault(e, []).append(p["url"])

    # If regex found emails, prepare pages with context for LLM; else still run LLM (on text) to search for mentions
    if found_emails:
        print(f"🔎 Regex discovered {len(found_emails)} unique email(s) across site.")
    else:
        print("🔎 Regex found 0 emails — will still run LLM to search text for explicit emails (if present).")

    # 4) Ask LLM (strict JSON) to identify which emails belong to person_name
    results = llm_sitewide_search(person_name, pages)
    # results are verified by LLM to be present in the snippets
    if results:
        # sort by confidence desc
        results_sorted = sorted(results, key=lambda r: r.get("confidence",0), reverse=True)
        return results_sorted

    # if LLM returns nothing but regex found some emails, do local heuristics:
    if found_emails:
        local_candidates = []
        for e, urls in found_emails.items():
            # compute heuristic score: presence of name in page text near email?
            score = 0.0
            candidate_context = ""
            for u in urls:
                page = next((p for p in pages if p["url"] == u), None)
                if not page: continue
                idx = page["text"].lower().find(e.lower())
                context = page["text"][max(0, idx-60): idx+len(e)+60] if idx>=0 else page["text"][:200]
                candidate_context = context.strip()
                if person_name.lower() in context.lower():
                    score = max(score, 0.95)
                elif any(part.lower() in context.lower() for part in person_name.split()):
                    score = max(score, 0.7)
                else:
                    score = max(score, 0.4)
            local_candidates.append({"email": e, "url": urls[0], "context": candidate_context, "confidence": score})
        # sort by heuristic confidence
        return sorted(local_candidates, key=lambda r: r["confidence"], reverse=True)

    # nothing found
    return []

# ---------- main agent (integrates with prior v5 flow) ----------
# For brevity, this file assumes you already have the v5 main functions:
# - ai_decide_directory, detect_structure, fetch_aem_profiles, fetch_html_profiles,
# - ai_pick_profile, ai_choose_email, etc.
# We'll include a small main that tries the usual flow and then calls failover when needed.

# Minimal re-implementations / lightweight copy of detection + selection (keeps script self-contained)
def render_page(url):
    html, links = render_page_html_and_links(url, headless=True, scroll=False, scroll_tries=3)
    return html, links

def detect_structure_quick(url):
    """Quick detect by HEAD/GET text."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
        text = (r.text or "").lower()
        if "_jcr_content.search.json" in text or "aemassets" in text:
            return "aem"
        if "wp-json" in text or "wp-content" in text:
            return "wordpress"
        if "graphql" in text or "/api/" in text:
            return "graphql"
    except:
        pass
    return "html"

def ai_decide_directory_quick(home_url, links):
    """Very small heuristic + LLM picking (keeps concise)."""
    # prefer anything that looks like people/team/professional/attorney
    candidates = [l for l in links if any(k in l.lower() for k in ("people","professional","team","attorney","lawyer"))]
    if not candidates:
        candidates = links[:30]
    # Ask LLM but force JSON output
    prompt = f"""
Select the ONE URL most likely to be the people/professionals directory for the site {home_url}.
Return ONLY JSON: {{ "directory": "<url or none>" }}
Candidates:
{candidates[:60]}
"""
    try:
        r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.0)
        raw = r.choices[0].message.content
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        return data.get("directory")
    except:
        return candidates[0] if candidates else None

def ai_pick_profile_quick(name, urls):
    """Ask LLM to pick profile url with strict JSON, fallback fuzzy."""
    prompt = f"""
From this list of profile URLs, pick the one that most likely belongs to '{name}'.
Return JSON only: {{ "profile_url": "<url or 'none'>" }}
URLs:
{urls[:150]}
"""
    try:
        r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.0)
        raw = r.choices[0].message.content
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        url = data.get("profile_url", "none")
    except:
        url = "none"
    if url in ("none", None) or "http" not in str(url):
        name_parts = name.lower().replace(".", "").split()
        matches = [u for u in urls if all(part in u.lower() for part in name_parts[:2])]
        if matches:
            url = matches[0]
        else:
            best = difflib.get_close_matches(name.lower().replace(" ", "-"), urls, n=1)
            url = best[0] if best else "none"
    return url

def ai_choose_email_quick(name, emails, text):
    """LLM picks email or returns nothing. Strict output not enforced here for brevity."""
    if not emails:
        return None
    prompt = f"""
Given these emails {emails} and this page text snippet, which email belongs to {name}? Return the single email or 'none'.
TEXT:
{text[:2000]}
"""
    r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.0)
    return r.choices[0].message.content.strip()

# ---------- main ----------
def main():
    if len(sys.argv) < 3:
        print("Usage: python smart_email_finder_failover.py <homepage_url> <person_name>")
        sys.exit(1)
    home_url = sys.argv[1].rstrip("/")
    person_name = sys.argv[2].strip()
    print(f"🔤 Searching for: {person_name} @ {home_url}")

    # 1) Render home and collect links
    home_html, home_links = render_page(home_url)

    # 2) Decide directory
    directory = ai_decide_directory_quick(home_url, home_links)
    if not directory:
        print("⚠️ Could not identify directory page; proceeding to sitewide failover.")
        results = sitewide_failover_search(home_url, person_name)
        if results:
            print_results(results, person_name)
            return
        print("❌ Nothing found.")
        return

    print(f"➡️ Directory: {directory}")

    # 3) detect structure and gather profile links
    structure = detect_structure_quick(directory)
    print(f"🧩 Detected: {structure}")
    profile_urls = []
    if "aem" in structure:
        # full AEM pagination (simple)
        for start in range(0,1000,50):
            api = urljoin(directory, f"_jcr_content.search.json?c=professional&q=&start={start}")
            try:
                r = requests.get(api, headers={"User-Agent":UA}, timeout=REQUEST_TIMEOUT)
                if r.status_code != 200: break
                j = r.json()
                hits = j.get("hits", [])
                if not hits: break
                for h in hits:
                    path = h.get("path") or h.get("url") or ""
                    if path:
                        profile_urls.append(urljoin(directory, path))
            except: break
    elif structure == "graphql":
        profile_urls = fetch_graphql_profiles(directory)  # use earlier defined function from v5 flow
    elif structure == "wordpress":
        profile_urls = fetch_wordpress_profiles(directory)
    else:
        profile_urls = fetch_html_profiles(directory)

    profile_urls = list(dict.fromkeys(profile_urls))
    print(f"🔎 Collected {len(profile_urls)} profile URLs")

    # 4) Ask AI to pick the person profile
    chosen = ai_pick_profile_quick(person_name, profile_urls)
    if chosen and chosen != "none":
        print(f"➡️ Chosen profile: {chosen}")
        # render and extract
        html, _ = render_page_html_and_links(chosen, headless=True, scroll=True, scroll_tries=4)
        emails = extract_emails_from_text(BeautifulSoup(html,'html.parser').get_text(" ",strip=True))
        if emails:
            # let LLM pick
            final = ai_choose_email_quick(person_name, emails, html)
            print("\nRESULT (direct):")
            print({"profile": chosen, "emails_found": emails, "llm_choice": final})
            return

    # 5) If we reach here, run failover sitewide LLM-backed search
    print("↪️ Primary profile extraction failed — running intelligent sitewide failover.")
    results = sitewide_failover_search(home_url, person_name)
    if results:
        print_results(results, person_name)
    else:
        print("❌ No explicit emails found on site.")

def print_results(results, name):
    print("\n==============================")
    print(f"👤 {name}")
    for r in results:
        print(f"📧 {r['email']}  (confidence={r.get('confidence',0):.2f})")
        print(f"🔗 {r.get('url')}")
        print(f"✂ context: {r.get('context')[:160]}")
        print("------------------------------")
    print("==============================")

# helpers from v5 reused (minimal)
def fetch_graphql_profiles(directory_url):
    # Playwright scroll method (kept minimal)
    print("⚙️ Scroll-fetch (Playwright) for dynamic lists...")
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(user_agent=UA)
        page.goto(directory_url, wait_until="networkidle", timeout=45000)
        last_h=0
        for _ in range(PLAYWRIGHT_SCROLL_TRIES):
            page.mouse.wheel(0,3000)
            page.wait_for_timeout(800)
            new_h=page.evaluate("document.body.scrollHeight")
            if new_h==last_h: break
            last_h=new_h
        links=[urljoin(directory_url,a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
        browser.close()
    profiles=[u for u in links if any(k in u.lower() for k in ("people","professional","team","attorney","person"))]
    return list(dict.fromkeys(profiles))

def fetch_wordpress_profiles(base_url):
    print("⚙️ WordPress: simple REST fallback")
    urls=[]
    try:
        r = requests.get(urljoin(base_url, "/wp-json/wp/v2/pages"), headers={"User-Agent":UA}, timeout=REQUEST_TIMEOUT)
        if r.status_code==200:
            for e in r.json():
                link = e.get("link") or e.get("slug")
                if link and any(k in (link or "").lower() for k in ("team","people","attorney","professional")):
                    urls.append(link if link.startswith("http") else urljoin(base_url, link))
    except: pass
    return list(dict.fromkeys(urls))

def fetch_html_profiles(directory_url):
    print("⚙️ HTML fallback: fetch & small render hybrid")
    # first try fast GET
    try:
        r = requests.get(directory_url, headers={"User-Agent":UA}, timeout=REQUEST_TIMEOUT)
        soup=BeautifulSoup(r.text,'html.parser')
        links=[urljoin(directory_url,a['href']) for a in soup.select("a[href]")]
        profiles=[u for u in links if any(k in u.lower() for k in ("people","professional","team","attorney","bio"))]
        if len(profiles)>150:
            return list(dict.fromkeys(profiles))
    except: profiles=[]
    # fallback to Playwright scroll + collect links
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(user_agent=UA)
        page.goto(directory_url, wait_until="networkidle", timeout=45000)
        last_h=0
        for _ in range(PLAYWRIGHT_SCROLL_TRIES):
            page.mouse.wheel(0,3000)
            page.wait_for_timeout(800)
            new_h=page.evaluate("document.body.scrollHeight")
            if new_h==last_h: break
            last_h=new_h
        links=[urljoin(directory_url,a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
        browser.close()
    profiles=[u for u in links if any(k in u.lower() for k in ("people","professional","team","attorney","bio"))]
    return list(dict.fromkeys(profiles))


def find_email_from_site(home_url: str, person_name: str):
    """
    Reusable version of main() for integration with other systems.
    Runs full extraction workflow (not just failover).
    Returns a normalized result list like:
      [{'email': 'john.doe@firm.com', 'url': '...', 'context': '', 'confidence': 0.95}]
    """
    print(f"🔍 Integrated call: Searching for {person_name} @ {home_url}")

    home_html, home_links = render_page(home_url)
    directory = ai_decide_directory_quick(home_url, home_links)

    if not directory:
        print("⚠️ No directory detected, running sitewide failover...")
        return sitewide_failover_search(home_url, person_name)

    print(f"➡️ Directory: {directory}")

    structure = detect_structure_quick(directory)
    print(f"🧩 Detected: {structure}")

    # Gather profile URLs
    profile_urls = []
    if "aem" in structure:
        # AEM API style
        for start in range(0, 1000, 50):
            api = urljoin(directory, f"_jcr_content.search.json?c=professional&q=&start={start}")
            try:
                r = requests.get(api, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
                if r.status_code != 200:
                    break
                j = r.json()
                hits = j.get("hits", [])
                if not hits:
                    break
                for h in hits:
                    path = h.get("path") or h.get("url") or ""
                    if path:
                        profile_urls.append(urljoin(directory, path))
            except:
                break
    elif structure == "graphql":
        profile_urls = fetch_graphql_profiles(directory)
    elif structure == "wordpress":
        profile_urls = fetch_wordpress_profiles(directory)
    else:
        profile_urls = fetch_html_profiles(directory)

    profile_urls = list(dict.fromkeys(profile_urls))
    print(f"🔎 Collected {len(profile_urls)} profile URLs")

    # Pick the right profile
    chosen = ai_pick_profile_quick(person_name, profile_urls)
    if chosen and chosen != "none":
        print(f"➡️ Chosen profile: {chosen}")
        html, _ = render_page_html_and_links(chosen, headless=True, scroll=True, scroll_tries=4)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        emails = extract_emails_from_text(text)
        if emails:
            final = ai_choose_email_quick(person_name, emails, text)
            print(f"✅ Integrated result: {final}")
            # Normalize return
            return [{
                'email': emails[0].lower(),
                'url': chosen,
                'context': final[:200] if isinstance(final, str) else '',
                'confidence': 0.95
            }]

    # If that fails, fallback
    print("↪️ Fallback: running sitewide failover search...")
    return sitewide_failover_search(home_url, person_name)

# ---------- run ----------
if __name__ == "__main__":
    main()



# #!/usr/bin/env python3
# """
# smart_email_finder_failover.py — Universal AI-powered email finder with contact-page + fuzzy name fallback.

# Usage:
#     python smart_email_finder_failover.py <homepage_url> "<person_name>"
# """

# import os, re, sys, json, time, difflib, requests
# from urllib.parse import urljoin, urlparse
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from playwright.sync_api import sync_playwright
# from groq import Groq

# # -------------- config --------------
# load_dotenv()
# GROQ_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_KEY:
#     print("Missing GROQ_API_KEY in .env")
#     sys.exit(1)

# MODEL = "llama-3.1-8b-instant"
# client = Groq(api_key=GROQ_KEY)
# UA = "SmartEmailFinder/2.0 (+https://github.com/krupali-surani)"
# REQUEST_TIMEOUT = 15
# PLAYWRIGHT_SCROLL_TRIES = 10
# MAX_SITE_PAGES = 20
# # ------------------------------------


# # ---------- utility helpers ----------
# def domain_only(url):
#     p = urlparse(url)
#     return f"{p.scheme}://{p.netloc}"

# def extract_emails_from_text(text):
#     text = re.sub(r"\[at\]|\(at\)", "@", text, flags=re.I)
#     text = re.sub(r"\[dot\]|\(dot\)", ".", text, flags=re.I)
#     emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
#     return list(dict.fromkeys([e.lower() for e in emails]))

# def render_page_html_and_links(url, headless=True, scroll=False, scroll_tries=5):
#     print(f"🌐 Render: {url}")
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=headless)
#         page = browser.new_page(user_agent=UA)
#         page.goto(url, wait_until="networkidle", timeout=45000)
#         if scroll:
#             last_h = 0
#             for _ in range(scroll_tries):
#                 page.mouse.wheel(0, 3000)
#                 page.wait_for_timeout(700)
#                 new_h = page.evaluate("document.body.scrollHeight")
#                 if new_h == last_h:
#                     break
#                 last_h = new_h
#         html = page.content()
#         els = page.query_selector_all("a[href]")
#         links = [urljoin(url, a.get_attribute("href").split("#")[0]) for a in els if a.get_attribute("href")]
#         browser.close()
#     return html, list(dict.fromkeys(links))

# def simple_fetch_html_links(url):
#     try:
#         r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
#         if r.status_code != 200:
#             return "", []
#         soup = BeautifulSoup(r.text, "html.parser")
#         links = [urljoin(url, a["href"].split("#")[0]) for a in soup.select("a[href]")]
#         return r.text, list(dict.fromkeys(links))
#     except Exception:
#         return "", []

# def safe_render(url):
#     try:
#         return render_page_html_and_links(url, headless=True, scroll=False, scroll_tries=3)
#     except Exception:
#         return simple_fetch_html_links(url)


# # ---------- improved AI profile selection ----------
# def ai_pick_profile_quick(name, urls):
#     """
#     Improved version: uses LLM + fuzzy + directory-text scanning.
#     Works across almost all firm websites.
#     """
#     name_clean = name.lower().replace(".", "").strip()
#     name_parts = [p for p in name_clean.split() if p]
#     print(f"🤖 Locating profile for '{name}' among {len(urls)} URLs...")

#     if not urls:
#         return "none"

#     # --- Step 1: Try LLM selection
#     prompt = f"""
# You are an expert assistant for mapping profile URLs.
# From this list, select the ONE URL that most likely belongs to "{name}".
# Return only strict JSON: {{ "profile_url": "<url or 'none'>" }}
# Candidates:
# {urls[:100]}
# """
#     try:
#         r = client.chat.completions.create(
#             model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.0
#         )
#         raw = r.choices[0].message.content
#         data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
#         url = data.get("profile_url", "none")
#     except Exception:
#         url = "none"

#     # --- Step 2: Fuzzy URL fallback
#     if url in ("none", None) or "http" not in str(url):
#         print("⚙️ LLM profile match failed — fuzzy matching URLs.")
#         def normalize(s): return s.lower().replace("-", " ").replace("_", " ").replace(".", "")
#         scored = []
#         for u in urls:
#             u_norm = normalize(u)
#             score = sum(1 for part in name_parts if part in u_norm)
#             if score > 0:
#                 scored.append((score, u))
#         if scored:
#             best = sorted(scored, key=lambda x: x[0], reverse=True)[0][1]
#             print(f"✅ Fuzzy match found likely profile: {best}")
#             return best

#         # --- Step 3: Directory text scan
#         print("🔍 No URL match found — scanning directory text...")
#         for u in urls[:10]:
#             try:
#                 html, _ = simple_fetch_html_links(u)
#                 text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True).lower()
#                 if all(p in text for p in name_parts[:2]):
#                     print(f"✅ Found textual match: {u}")
#                     return u
#             except Exception:
#                 continue
#         print("❌ No profile match found.")
#         return "none"

#     print(f"✅ LLM selected profile: {url}")
#     return url


# # ---------- contact page fallback ----------
# def contact_page_fallback(home_url):
#     print("📞 Trying contact/about page...")
#     html, links = safe_render(home_url)
#     contact_links = [l for l in links if any(k in l.lower() for k in ("contact", "about", "connect", "reach", "team"))]
#     contact_links = list(dict.fromkeys(contact_links))
#     if not contact_links:
#         return []
#     results = []
#     for contact_url in contact_links[:3]:
#         try:
#             print(f"➡️ Checking contact page: {contact_url}")
#             html, _ = safe_render(contact_url)
#         except Exception:
#             continue
#         soup = BeautifulSoup(html, "html.parser")
#         for s in soup(["script", "style", "svg", "noscript"]): s.decompose()
#         text = soup.get_text(" ", strip=True)
#         text = re.sub(r"\[at\]|\(at\)", "@", text, flags=re.I)
#         text = re.sub(r"\[dot\]|\(dot\)", ".", text, flags=re.I)
#         emails = extract_emails_from_text(text)
#         for a in soup.select("a[href^=mailto]"):
#             mail = a["href"].replace("mailto:", "").split("?")[0]
#             if "@" in mail:
#                 emails.append(mail)
#         for e in list(dict.fromkeys(emails)):
#             idx = text.lower().find(e.lower())
#             ctx = text[max(0, idx-100): idx+len(e)+100] if idx >= 0 else ""
#             results.append({"email": e, "url": contact_url, "context": ctx[:150], "confidence": 0.8})
#     uniq = {r["email"]: r for r in results}
#     return list(uniq.values())


# # ---------- main workflow ----------
# def main():
#     if len(sys.argv) < 3:
#         print("Usage: python smart_email_finder_failover.py <homepage_url> \"<person_name>\"")
#         sys.exit(1)

#     home_url = sys.argv[1].rstrip("/")
#     person_name = sys.argv[2].strip()
#     print(f"🔤 Searching for: {person_name} @ {home_url}")

#     html, links = safe_render(home_url)

#     # --- Detect likely directory
#     directory_candidates = [l for l in links if any(k in l.lower() for k in (
#         "people", "professional", "team", "attorney", "lawyer", "staff", "leadership", "members", "bios", "experts"
#     ))]
#     directory = directory_candidates[0] if directory_candidates else None

#     if not directory:
#         print("⚠️ No directory detected, trying contact page...")
#         results = contact_page_fallback(home_url)
#         if results:
#             print_results(results, person_name)
#             return
#         print("📡 Contact page gave no results — sitewide failover skipped for speed.")
#         return

#     print(f"➡️ Directory page detected: {directory}")

#     # --- Collect profile links
#     dir_html, dir_links = safe_render(directory)
#     profile_urls = [l for l in dir_links if any(k in l.lower() for k in (
#         "people", "professional", "team", "attorney", "lawyer", "bio", "member", "profile"
#     ))]
#     profile_urls = list(dict.fromkeys(profile_urls))
#     print(f"🔎 Collected {len(profile_urls)} potential profile URLs")

#     # --- Choose correct profile
#     chosen = ai_pick_profile_quick(person_name, profile_urls)
#     if chosen == "none":
#         print("⚠️ Profile not found — contact page fallback...")
#         results = contact_page_fallback(home_url)
#         if results:
#             print_results(results, person_name)
#             return
#         print("❌ No results found at all.")
#         return

#     print(f"➡️ Selected profile: {chosen}")

#     # --- Extract email from profile
#     try:
#         html, _ = render_page_html_and_links(chosen, headless=True, scroll=True, scroll_tries=4)
#     except Exception:
#         html, _ = simple_fetch_html_links(chosen)

#     soup = BeautifulSoup(html, "html.parser")
#     text = soup.get_text(" ", strip=True)
#     emails = extract_emails_from_text(text)

#     if not emails:
#         print("⚠️ No direct emails found — scanning for obfuscation...")
#         text = re.sub(r"\[at\]|\(at\)", "@", text, flags=re.I)
#         text = re.sub(r"\[dot\]|\(dot\)", ".", text, flags=re.I)
#         emails = extract_emails_from_text(text)

#     if emails:
#         print("\n✅ RESULT:")
#         for e in emails:
#             print(f"📧 {e}")
#         print(f"🔗 {chosen}")
#         return
#     else:
#         print("⚠️ No email found on profile. Trying contact page fallback...")
#         results = contact_page_fallback(home_url)
#         if results:
#             print_results(results, person_name)
#         else:
#             print("❌ No explicit emails found on site.")


# def print_results(results, name):
#     print("\n==============================")
#     print(f"👤 {name}")
#     for r in results:
#         print(f"📧 {r['email']}  (confidence={r.get('confidence',0):.2f})")
#         print(f"🔗 {r.get('url')}")
#         print(f"✂ context: {r.get('context')[:120]}")
#         print("------------------------------")
#     print("==============================")


# # ---------- run ----------
# if __name__ == "__main__":
#     main()





















###########################################a-z################

# #!/usr/bin/env python3
# """
# email_extraction_stage.py

# Universal Law Firm Email Extractor (AI + Browser Rendering + Pagination)
# Author: Krupali Surani

# Usage:
#     python email_extraction_stage.py <homepage_url> "<person_name>"
# """

# import os, re, sys, json, time, requests, difflib
# from urllib.parse import urljoin, urlparse
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from playwright.sync_api import sync_playwright
# from groq import Groq

# # ========== CONFIG ==========
# load_dotenv()
# GROQ_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_KEY:
#     print("❌ Missing GROQ_API_KEY in .env")
#     sys.exit(1)

# MODEL = "llama-3.1-8b-instant"
# client = Groq(api_key=GROQ_KEY)
# UA = "SmartEmailFinder/3.0 (+https://github.com/krupali-surani)"
# REQUEST_TIMEOUT = 15
# PLAYWRIGHT_SCROLL_TRIES = 15
# MAX_SITE_PAGES = 25
# # ============================

# # ---------- Utilities ----------
# def domain_only(url):
#     try:
#         p = urlparse(url)
#         return f"{p.scheme}://{p.netloc}"
#     except:
#         return url

# def safe_render(url, headless=True, scroll=False, scroll_tries=5):
#     """Render a webpage using Playwright with fallback to requests."""
#     print(f"🌐 Render: {url}")
#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=headless)
#             page = browser.new_page(user_agent=UA)
#             page.goto(url, wait_until="networkidle", timeout=45000)
#             if scroll:
#                 last_h = 0
#                 for _ in range(scroll_tries):
#                     page.mouse.wheel(0, 3000)
#                     page.wait_for_timeout(800)
#                     new_h = page.evaluate("document.body.scrollHeight")
#                     if new_h == last_h:
#                         break
#                     last_h = new_h
#             html = page.content()
#             links = [urljoin(url, a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
#             browser.close()
#             return html, list(dict.fromkeys([l for l in links if l]))
#     except Exception:
#         try:
#             r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
#             soup = BeautifulSoup(r.text, "html.parser")
#             links = [urljoin(url, a["href"]) for a in soup.select("a[href]")]
#             return r.text, list(dict.fromkeys(links))
#         except Exception:
#             return "", []

# # ---------- Email Extraction ----------
# def extract_emails_from_text(text, html=None):
#     """Extracts emails from visible text and HTML structure."""
#     text = text or ""
#     text = re.sub(r"\[at\]|\(at\)", "@", text, flags=re.I)
#     text = re.sub(r"\[dot\]|\(dot\)", ".", text, flags=re.I)
#     emails = set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text))

#     if html:
#         soup = BeautifulSoup(html, "html.parser")
#         for a in soup.select("a[href^=mailto]"):
#             mail = a.get("href", "").replace("mailto:", "").split("?")[0]
#             if "@" in mail:
#                 emails.add(mail.lower())
#         for tag in soup.find_all(attrs=True):
#             for attr, val in tag.attrs.items():
#                 if isinstance(val, str) and "@" in val and len(val) < 100:
#                     if re.match(r"[\w\.-]+@[\w\.-]+\.\w+", val):
#                         emails.add(val.lower())
#         for script in soup.find_all("script"):
#             for e in re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", script.get_text()):
#                 emails.add(e.lower())
#     return list(emails)

# # ---------- Site Structure Detection ----------
# def detect_structure_quick(url):
#     try:
#         r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
#         text = r.text.lower()
#         if "_jcr_content.search.json" in text or "aemassets" in text:
#             return "aem"
#         if any(k in text for k in ("apollo-client", "graphql", "__next_data__", "next-data", "window.__NEXT_DATA__")):
#             return "graphql"
#         if "wp-json" in text or "wp-content" in text:
#             return "wordpress"
#     except Exception:
#         pass
#     return "html"

# # ---------- AI Directory Detection ----------
# def ai_decide_directory_quick(home_url, links):
#     """LLM selects correct directory page."""
#     candidates = [l for l in links if any(k in l.lower() for k in (
#         "people", "our-people", "professionals", "team", "directory",
#         "attorney", "lawyer", "staff", "leadership", "members", "bios", "experts"
#     ))]
#     if not candidates:
#         candidates = links[:40]

#     prompt = f"""
# Identify which URL is the firm's professionals directory.

# ❌ Skip /about/, /contact/, /news/, /insights/.
# ✅ Pick a page listing lawyers or staff.

# Return JSON only: {{ "directory": "<url or 'none'>" }}

# Candidates:
# {candidates[:80]}
# """
#     try:
#         r = client.chat.completions.create(model=MODEL,
#             messages=[{"role": "user", "content": prompt}], temperature=0.0)
#         data = json.loads(re.search(r"\{.*\}", r.choices[0].message.content, re.S).group(0))
#         if "http" in data.get("directory", ""):
#             return data["directory"]
#     except Exception:
#         pass
#     return candidates[0] if candidates else None
# def deep_people_crawl(start_url, max_depth=3, visited=None):
#     """
#     Recursively crawls through all /people-related pages (alphabet pages, pagination, etc.)
#     to collect every unique profile URL.
#     """
#     if visited is None:
#         visited = set()

#     if start_url in visited or len(visited) > 2000:
#         return visited
#     visited.add(start_url)

#     try:
#         html, _ = safe_render(start_url, scroll=True, scroll_tries=8)
#     except Exception as e:
#         print(f"⚠️ Render failed for {start_url}: {e}")
#         return visited

#     soup = BeautifulSoup(html, "html.parser")

#     # Collect all profile URLs
#     for a in soup.select("a[href]"):
#         href = a.get("href", "")
#         if not href:
#             continue
#         full_url = urljoin(start_url, href)
#         # Accept if looks like a lawyer profile
#         if re.search(r"/people/[-a-z0-9]+", href.lower()) and "starts_with" not in href:
#             visited.add(full_url)

#     # Collect next-level directory links (pagination, starts_with, etc.)
#     next_pages = []
#     for a in soup.select("a[href]"):
#         href = a.get("href", "")
#         if not href:
#             continue
#         if re.search(r"(starts_with=|page=|page/|offset=)", href) or href.rstrip("/") == start_url.rstrip("/"):
#             full_url = urljoin(start_url, href)
#             if full_url not in visited:
#                 next_pages.append(full_url)

#     # Recurse into next pages
#     for next_url in next_pages:
#         if max_depth > 0:
#             deep_people_crawl(next_url, max_depth - 1, visited)

#     return visited

# # ---------- Full Pagination Handling ----------
# def fetch_full_directory_profiles(directory_url, structure_type):
#     """
#     Universal deep crawler for law firm directories.
#     Handles:
#       - AEM JSON
#       - GraphQL / React (infinite scroll)
#       - HTML with A–Z, pagination, or multi-page
#     Verifies each collected profile link and saves to CSV.
#     """
#     print(f"⚙️ Deep crawling directory ({structure_type}) ...")
#     all_links = set()

#     # =============== Case 1️⃣ AEM JSON (e.g. Cooley, Finnegan) ===============
#     if structure_type == "aem":
#         for start in range(0, 2000, 50):
#             api = urljoin(directory_url, f"_jcr_content.search.json?c=professional&q=&start={start}")
#             try:
#                 r = requests.get(api, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
#                 if r.status_code != 200:
#                     break
#                 hits = r.json().get("hits", [])
#                 if not hits:
#                     break
#                 for h in hits:
#                     path = h.get("path") or h.get("url") or ""
#                     if path:
#                         all_links.add(urljoin(directory_url, path))
#             except Exception:
#                 break

#     # =============== Case 2️⃣ GraphQL / React (e.g. MayerBrown, Shearman) ===============
#     elif structure_type == "graphql":
#         print("🧠 Detected dynamic JS-rendered directory, scrolling deeply...")
#         try:
#             with sync_playwright() as p:
#                 browser = p.chromium.launch(headless=True)
#                 page = browser.new_page(user_agent=UA)
#                 page.goto(directory_url, wait_until="networkidle", timeout=90000)

#                 seen_links = set()
#                 stable_rounds = 0
#                 scroll_round = 0

#                 while stable_rounds < 3 and scroll_round < 40:
#                     scroll_round += 1
#                     page.mouse.wheel(0, 5000)
#                     page.wait_for_timeout(2000)
#                     anchors = page.query_selector_all("a[href]")
#                     new_links = []
#                     for a in anchors:
#                         href = a.get_attribute("href") or ""
#                         if href and any(k in href.lower() for k in ("people", "professional", "bio", "team")):
#                             full = urljoin(directory_url, href)
#                             if full not in seen_links:
#                                 seen_links.add(full)
#                                 new_links.append(full)
#                     print(f"   🔁 Scroll round {scroll_round}: total {len(seen_links)} links")
#                     if not new_links:
#                         stable_rounds += 1
#                     else:
#                         stable_rounds = 0
#                 browser.close()
#                 all_links.update(seen_links)

#             # 🔎 If still too few links, try GraphQL API sniff
#             if len(all_links) < 50:
#                 print("⚙️ Attempting GraphQL API sniff (MayerBrown style)...")
#                 api_guess = directory_url.rsplit("/", 1)[0] + "/api/graphql"
#                 try:
#                     payload = {"query": "{ people(first:1000){nodes{url name}} }"}
#                     r = requests.post(api_guess, json=payload,
#                                       headers={"User-Agent": UA, "Content-Type": "application/json"},
#                                       timeout=REQUEST_TIMEOUT)
#                     if r.status_code == 200:
#                         nodes = r.json().get("data", {}).get("people", {}).get("nodes", [])
#                         for n in nodes:
#                             u = n.get("url", "")
#                             if u.startswith("/"):
#                                 all_links.add(urljoin(directory_url, u))
#                 except Exception as e:
#                     print(f"⚠️ GraphQL sniff failed: {e}")

#         except Exception as e:
#             print(f"⚠️ GraphQL scroll error: {e}")

#     # =============== Case 3️⃣ Static HTML / A–Z / Multi-page (e.g. KSLaw) ===============
#     else:
#         print("🧭 Launching deep recursive people crawler ...")
#         all_links = deep_people_crawl(directory_url, max_depth=3)

#     # =============== Validation + Logging ===============
#     print(f"📊 Total raw profile URLs collected: {len(all_links)}")

#     # Filter out directory root or irrelevant links
#     filtered_links = [
#         u for u in all_links
#         if re.search(r"/people/[-a-z0-9]", u.lower()) and not re.search(r"starts_with=", u)
#     ]

#     # Verify URLs (HTTP 200)
#     valid_links = []
#     for u in filtered_links:
#         try:
#             r = requests.head(u, headers={"User-Agent": UA}, allow_redirects=True, timeout=5)
#             if r.status_code == 200:
#                 valid_links.append(u)
#         except Exception:
#             continue

#     print(f"✅ Verified working profile URLs: {len(valid_links)}")
#     print("🧾 Sample (first 10):")
#     for i, l in enumerate(valid_links[:10]):
#         print(f"   {i+1:02d}: {l}")

#     # Save all valid URLs
#     try:
#         import csv
#         with open("collected_profiles.csv", "w", newline="", encoding="utf-8") as f:
#             writer = csv.writer(f)
#             writer.writerow(["URL"])
#             for l in valid_links:
#                 writer.writerow([l])
#         print("💾 Saved verified profiles to collected_profiles.csv")
#     except Exception as e:
#         print(f"⚠️ Could not save CSV: {e}")

#     return valid_links


# # ---------- AI Profile Selection ----------
# def ai_pick_profile_quick(name, urls):
#     """LLM selects correct profile (not directory)."""
#     name_clean = name.lower().replace(".", "")
#     name_parts = [p for p in name_clean.split() if p]
#     if not urls:
#         return "none"

#     prompt = f"""
# Choose the URL that most likely belongs to "{name}".

# ❌ Exclude directories (/people/, /team/, /our-people/).
# ✅ Pick pages that look like an individual's bio (end with name slug).

# Return JSON: {{ "profile_url": "<url or 'none'>" }}
# URLs:
# {urls[:150]}
# """
#     try:
#         r = client.chat.completions.create(model=MODEL,
#             messages=[{"role":"user","content":prompt}], temperature=0.0)
#         raw = r.choices[0].message.content
#         data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
#         url = data.get("profile_url", "none")
#         if "http" in url:
#             return url
#     except Exception:
#         pass

#     # fallback fuzzy match
#     best = difflib.get_close_matches(name_clean.replace(" ", "-"), urls, n=1)
#     return best[0] if best else "none"

# # ---------- Contact Page Fallback ----------
# def contact_page_fallback(home_url):
#     print("📞 Trying contact/about page...")
#     html, links = safe_render(home_url)
#     candidates = [l for l in links if any(k in l.lower() for k in
#         ("contact", "about", "connect", "locations", "offices"))]
#     results = []
#     for u in candidates[:4]:
#         html, _ = safe_render(u)
#         soup = BeautifulSoup(html, "html.parser")
#         for s in soup(["script","style"]): s.decompose()
#         text = soup.get_text(" ", strip=True)
#         emails = extract_emails_from_text(text, html)
#         for e in emails:
#             results.append({"email": e, "url": u, "context": text[:200], "confidence": 0.8})
#     return results

# # ---------- Core Workflow ----------
# def find_email_from_site(home_url: str, person_name: str):
#     print(f"🔤 Searching for: {person_name} @ {home_url}")
#     html, links = safe_render(home_url)
#     directory = ai_decide_directory_quick(home_url, links)

#     if not directory:
#         print("⚠️ No directory found, checking contact...")
#         res = contact_page_fallback(home_url)
#         return res or []

#     print(f"➡️ Directory page detected: {directory}")
#     structure = detect_structure_quick(directory)
#     print(f"🧩 Detected: {structure}")

#     profile_urls = fetch_full_directory_profiles(directory, structure)
#     chosen = ai_pick_profile_quick(person_name, profile_urls)
#     if chosen == "none":
#         print("⚠️ No profile match, fallback to contact...")
#         return contact_page_fallback(home_url)

#     print(f"➡️ Selected profile: {chosen}")
#     html, _ = safe_render(chosen, scroll=True)
#     soup = BeautifulSoup(html, "html.parser")
#     for s in soup(["script", "style"]): s.decompose()
#     text = soup.get_text(" ", strip=True)
#     emails = extract_emails_from_text(text, html)
#     if not emails:
#         print("⚠️ No email found on profile, fallback to contact...")
#         return contact_page_fallback(home_url)

#     return [{"email": e, "url": chosen, "context": text[:200], "confidence": 0.95} for e in emails]

# # ---------- CLI Runner ----------
# def print_results(results, name):
#     print("\n==============================")
#     print(f"👤 {name}")
#     if not results:
#         print("❌ No explicit emails found.")
#     for r in results:
#         print(f"📧 {r['email']} (conf={r['confidence']:.2f})")
#         print(f"🔗 {r['url']}")
#         print(f"✂ {r['context'][:150]}")
#         print("------------------------------")
#     print("==============================")

# def main():
#     if len(sys.argv) < 3:
#         print("Usage: python email_extraction_stage.py <homepage_url> \"<person_name>\"")
#         sys.exit(1)
#     home_url, name = sys.argv[1].rstrip("/"), sys.argv[2].strip()
#     res = find_email_from_site(home_url, name)
#     print_results(res, name)

# if __name__ == "__main__":
#     main()




# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# AI-Fast Finder (Groq Hybrid)
# Combines fast targeted search with Groq AI structural reasoning.
# """

# import os, re, json, time, csv
# from urllib.parse import urljoin, urlparse, urldefrag
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from playwright.sync_api import sync_playwright
# from groq import Groq
# from difflib import SequenceMatcher

# # ---------------- CONFIG ----------------
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise RuntimeError("Missing GROQ_API_KEY in .env")

# groq_client = Groq(api_key=GROQ_API_KEY)

# HEADLESS = True
# PAGE_TIMEOUT = 40000
# SCROLL_PAUSE = 0.8
# NAME_MATCH_THRESHOLD = 0.74
# OUTPUT_CSV = "found_profile.csv"

# def log(*args): print(*args, flush=True)
# def normalize_url(u, base):
#     if not u: return None
#     u = urljoin(base, u); u, _ = urldefrag(u); return u
# def is_same_domain(u, base): return urlparse(u).netloc == urlparse(base).netloc
# def name_similarity(a,b): return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# # ---------------- AI STRUCTURE DETECTOR ----------------
# def ai_detect_structure(html, base_url):
#     """Ask Groq LLaMA to detect how the firm's people directory works."""
#     prompt = f"""
# Analyze this law firm website HTML and decide the best way to find professional profiles.
# Return JSON with these fields only:
# {{
#   "directory_candidates": ["/people", "/professionals", "/our-people"],
#   "search_strategy": "alphabet" | "scroll" | "search_box" | "json" | "html",
#   "profile_pattern": "/people/[a-z0-9-]+",
#   "has_search_box": true/false,
#   "has_next_data": true/false
# }}

# HTML_SNIPPET:
# {html[:6000]}
# """
#     try:
#         resp = groq_client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[{"role":"user","content":prompt}],
#             temperature=0.05,
#             max_tokens=600,
#         )
#         raw = resp.choices[0].message.content.strip()

#         # 🧠 Always try to extract only valid JSON object portion
#         m = re.search(r"\{[\s\S]*\}", raw)
#         if not m:
#             log("⚠️ AI response not JSON, falling back to default plan.")
#             return None
#         try:
#             plan = json.loads(m.group())
#             log("🤖 AI plan:", json.dumps(plan, indent=2))
#             return plan
#         except json.JSONDecodeError as e:
#             log(f"⚠️ JSON parse failed ({e}); raw response below:\n{raw}")
#             return None

#     except Exception as e:
#         log(f"⚠️ AI detect failed: {e}")
#         return None

# # ---------------- EMAIL EXTRACTOR ----------------
# def extract_email(page):
#     html = page.content()
#     pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
#     found = re.findall(pattern, html)
#     if found:
#         for e in found:
#             if not any(x in e.lower() for x in ["info@", "contact@", "noreply@", "support@"]):
#                 return e
#     # try mailto
#     try:
#         link = page.query_selector('a[href^="mailto:"]')
#         if link:
#             return link.get_attribute("href").replace("mailto:", "")
#     except: pass
#     return None

# # ---------------- PROFILE MATCHER ----------------
# def find_profile(page, target_name, base_url, pattern):
#     soup = BeautifulSoup(page.content(), "html.parser")
#     matches = []
#     for a in soup.find_all("a", href=True):
#         href = a["href"].lower()
#         if re.search(pattern, href):
#             text = a.get_text(strip=True)
#             sim = max(name_similarity(target_name, text), name_similarity(target_name, href))
#             if sim > NAME_MATCH_THRESHOLD:
#                 abs_url = normalize_url(href, base_url)
#                 if abs_url and is_same_domain(abs_url, base_url):
#                     matches.append(abs_url)
#     return list(set(matches))

# # ---------------- STRATEGIES ----------------
# def strategy_scroll(page, name, base_url, pattern):
#     log("📜 Scrolling through directory...")
#     seen = set()
#     for _ in range(20):
#         new_links = find_profile(page, name, base_url, pattern)
#         for link in new_links: seen.add(link)
#         if seen:
#             log(f"Found {len(seen)} potential profiles so far...")
#             for url in seen:
#                 if check_profile(page, url, name): return url
#         page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
#         time.sleep(SCROLL_PAUSE)
#     return None

# def strategy_alphabet(page, name, base_url, pattern):
#     log("🔤 Trying A–Z pattern search...")
#     for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
#         u = f"{page.url.split('?')[0]}?starts_with={ch}"
#         try:
#             page.goto(u, timeout=PAGE_TIMEOUT)
#             result = find_profile(page, name, base_url, pattern)
#             for url in result:
#                 if check_profile(page, url, name): return url
#         except: continue
#     return None

# def strategy_json(page, name):
#     log("📦 Checking for __NEXT_DATA__ JSON...")
#     soup = BeautifulSoup(page.content(), "html.parser")
#     s = soup.find("script", id="__NEXT_DATA__")
#     if not s or not s.string: return None
#     try:
#         data = json.loads(s.string)
#         j = json.dumps(data)
#         emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', j)
#         if emails: return emails[0]
#     except: pass
#     return None

# # ---------------- CHECK PROFILE PAGE ----------------
# def check_profile(page, url, name):
#     try:
#         page.goto(url, timeout=PAGE_TIMEOUT)
#         html = page.content().lower()
#         if name.lower().split()[0] in html:
#             email = extract_email(page)
#             if email:
#                 log(f"✅ Found profile {url}\n📧 {email}")
#                 with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
#                     csv.writer(f).writerows([["name","profile","email"], [name, url, email]])
#                 return True
#     except Exception as e:
#         log(f"⚠️ Error opening {url}: {e}")
#     return False

# # ---------------- MAIN ----------------
# def main():
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument("url")
#     parser.add_argument("person")
#     args = parser.parse_args()

#     base = args.url.strip().rstrip("/")
#     name = args.person.strip()
#     log(f"🚀 Searching {name} @ {base}")

#     with sync_playwright() as pw:
#         browser = pw.chromium.launch(headless=HEADLESS)
#         page = browser.new_page()
#         try:
#             page.goto(base, timeout=PAGE_TIMEOUT)
#         except Exception as e:
#             log("❌ Failed to open base:", e); browser.close(); return

#         html = page.content()
#         plan = ai_detect_structure(html, base)
#         if plan and isinstance(plan, dict):
#             dirs = [normalize_url(d, base) for d in plan.get("directory_candidates", ["/people"])]
#             pattern = plan.get("profile_pattern", r"/people/[a-z0-9-]+")
#         else:
#             log("⚠️ Using fallback defaults (AI plan missing or invalid).")
#             plan = {"search_strategy": "scroll"}
#             dirs = [normalize_url("/people", base)]
#             pattern = r"/people/[a-z0-9-]+"


#         found = False
#         for dir_url in dirs:
#             log(f"\n📂 Checking directory: {dir_url}")
#             try:
#                 page.goto(dir_url, timeout=PAGE_TIMEOUT)
#                 strat = plan.get("search_strategy","scroll")
#                 if strat == "json" and plan.get("has_next_data"):
#                     email = strategy_json(page, name)
#                     if email:
#                         log(f"✅ Found email in JSON: {email}")
#                         found = True; break
#                 elif strat == "alphabet":
#                     if strategy_alphabet(page, name, base, pattern): found=True; break
#                 else:
#                     if strategy_scroll(page, name, base, pattern): found=True; break
#             except Exception as e:
#                 log(f"⚠️ Directory error: {e}")
#                 continue

#         if not found:
#             log(f"❌ No profile/email found for {name}")
#         browser.close()

# if __name__ == "__main__":
#     main()


# #python email_extraction_stage.py https://www.finnegan.com "Anthony J. Lombardi"