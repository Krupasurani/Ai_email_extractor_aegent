# import os
# import json
# import asyncio
# from typing import List
# from pydantic import BaseModel, EmailStr, field_validator
# from urllib.parse import urlparse
# from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMExtractionStrategy, LLMConfig
# from groq import Groq
# from dotenv import load_dotenv  # New import for .env loading
# import argparse

# # Load .env file early (searches current dir and parents)
# load_dotenv()

# # Pydantic models for structured output
# class EmailInfo(BaseModel):
#     email: EmailStr
#     context: str
#     source_url: str

#     @field_validator('email', mode='before')
#     @classmethod
#     def validate_email(cls, v):
#         return v.lower() if v else v

# class ExtractionResult(BaseModel):
#     emails: List[EmailInfo]
#     total_pages_crawled: int

# async def get_relevant_links_llm(content: str, domain: str, target: str = None, api_key: str = None) -> List[str]:
#     """Use LLM to suggest relevant subpages for crawling."""
#     client = Groq(api_key=api_key)
#     prompt = f"""
#     From the webpage content below, extract up to 5 internal links (full URLs starting with {domain}) 
#     that are most relevant for finding professional emails, such as contact, team, about, or profiles pages.
#     Prioritize mentions of '{target}' if provided.
#     Return ONLY a JSON list of URLs: {{"links": ["url1", "url2"]}}

#     Content: {content[:3000]}
#     """
#     completion = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.2,
#         max_tokens=300
#     )
#     try:
#         result = json.loads(completion.choices[0].message.content.strip())
#         return result.get("links", [])
#     except:
#         return []

# def create_email_extraction_strategy(target: str = None, api_key: str = None) -> LLMExtractionStrategy:
#     """Create LLM strategy for email extraction."""
#     schema = {
#         "type": "object",
#         "properties": {
#             "emails": {
#                 "type": "array",
#                 "items": {
#                     "type": "object",
#                     "properties": {
#                         "email": {"type": "string", "format": "email"},
#                         "context": {"type": "string"},
#                         "source": {"type": "string"}
#                     },
#                     "required": ["email", "context", "source"]
#                 }
#             }
#         },
#         "required": ["emails"]
#     }
#     instruction = f"""
#     Extract all professional email addresses from the content. 
#     For each, include: email (e.g., name@domain.com), context (surrounding sentence), source (section like 'Contact').
#     Focus on '{target}' if mentioned. Ignore personal or spam emails.
#     """
#     llm_config = LLMConfig(
#         provider="groq",
#         api_token=api_key,
#         model="llama-3.1-8b-instant"
#     )
#     extra_args = {"temperature": 0.1}
#     return LLMExtractionStrategy(
#         schema=schema,
#         instruction=instruction,
#         llm_config=llm_config,
#         extraction_type="schema",
#         extra_args=extra_args
#     )

# async def create_crawler() -> AsyncWebCrawler:
#     """Configure the AI crawler asynchronously."""
#     browser_config = BrowserConfig(headless=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
#     crawler = AsyncWebCrawler(config=browser_config)
#     return crawler

# async def ai_email_finder(start_url: str, target: str = None, max_pages: int = 10, api_key: str = None) -> ExtractionResult:
#     """Main AI-powered finder function (async)."""
#     domain = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
    
#     crawler = await create_crawler()
#     extraction_strategy = create_email_extraction_strategy(target, api_key)
#     all_emails = []
#     pages_crawled = 0
#     urls_to_crawl = [start_url]
#     visited = set()
    
#     while urls_to_crawl and pages_crawled < max_pages:
#         url = urls_to_crawl.pop(0)
#         if url in visited:
#             continue
#         visited.add(url)
        
#         try:
#             run_config = CrawlerRunConfig(extraction_strategy=extraction_strategy)
#             result = await crawler.arun(url=url, config=run_config)
#             pages_crawled += 1
            
#             # Parse extracted emails
#             if result.extracted_content:
#                 data = json.loads(result.extracted_content)
#                 for item in data.get("emails", []):
#                     all_emails.append(EmailInfo(
#                         email=item["email"],
#                         context=item["context"],
#                         source_url=url
#                     ))
            
#             # AI-suggested next links
#             if pages_crawled < max_pages:
#                 links = await get_relevant_links_llm(result.cleaned_html, domain, target, api_key)
#                 urls_to_crawl.extend([link for link in links if link not in visited and link.startswith(domain)])
                
#         except Exception as e:
#             print(f"Error crawling {url}: {e}")
    
#     await crawler.close()  # Clean up
#     return ExtractionResult(emails=all_emails, total_pages_crawled=pages_crawled)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="AI-Powered Email Finder")
#     parser.add_argument("url", help="Starting URL")
#     parser.add_argument("--target", help="Optional target name")
#     parser.add_argument("--max-pages", type=int, default=10, help="Max pages to crawl")
#     parser.add_argument("--groq-api-key", help="Groq API Key (optional if .env is set)")
#     args = parser.parse_args()
    
#     # Determine API key: CLI override or from .env
#     api_key = args.groq_api_key or os.environ.get('GROQ_API_KEY')
#     if not api_key:
#         raise ValueError("No Groq API key found. Set it in .env as GROQ_API_KEY=your_key or use --groq-api-key.")
    
#     # Run async main
#     result = asyncio.run(ai_email_finder(args.url, args.target, args.max_pages, api_key))
#     print(result.json(indent=2))












# #!/usr/bin/env python3
# """
# Smart Email Scraper (Full Website Crawl)
# --------------------------------------------
# Usage:
#     python smart_email_scraper.py https://example.com
# """

# import re
# import sys
# import scrapy
# from scrapy.crawler import CrawlerProcess
# from urllib.parse import urljoin


# class SmartEmailSpider(scrapy.Spider):
#     name = "smart_email_spider"

#     def __init__(self, start_url, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.start_urls = [start_url]
#         self.domain = start_url.split("//")[1].split("/")[0]
#         self.visited_urls = set()
#         self.emails = set()

#     def parse(self, response):
#         # Skip already visited URLs
#         if response.url in self.visited_urls:
#             return
#         self.visited_urls.add(response.url)

#         # Skip non-text responses (like PDFs, ZIPs, images)
#         content_type = response.headers.get(b'Content-Type', b'').decode('utf-8').lower()
#         if not any(ct in content_type for ct in ["text/html", "application/xhtml+xml"]):
#             self.logger.debug(f"Skipping non-HTML content: {response.url}")
#             return

#         # Extract emails safely
#         text = response.text
#         found_emails = set(
#             re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
#         )
#         if found_emails:
#             self.emails.update(found_emails)
#             self.logger.info(f"📧 Found {len(found_emails)} on {response.url}")

#         # Crawl internal links recursively
#         for href in response.css("a::attr(href)").getall():
#             next_url = urljoin(response.url, href)
#             if (
#                 self.domain in next_url
#                 and next_url not in self.visited_urls
#                 and not any(next_url.lower().endswith(ext) for ext in [".pdf", ".jpg", ".png", ".zip", ".doc", ".docx"])
#             ):
#                 yield scrapy.Request(next_url, callback=self.parse, errback=self.handle_error)

#     def handle_error(self, failure):
#         """Handle network errors gracefully (e.g., 429s, timeouts)."""
#         self.logger.warning(f"⚠️ Request failed: {failure.request.url} | Reason: {failure.value}")

#     def closed(self, reason):
#         print("\n==============================")
#         print("📧 UNIQUE EMAILS FOUND")
#         print("==============================")
#         if self.emails:
#             for email in sorted(self.emails):
#                 print(email)
#         else:
#             print("❌ No emails found.")
#         print("==============================\n")


# def run_scraper(target_url):
#     process = CrawlerProcess(settings={
#         "USER_AGENT": "Mozilla/5.0 (compatible; SmartEmailBot/1.0; +https://example.com)",
#         "LOG_LEVEL": "INFO",
#         "DOWNLOAD_DELAY": 1.5,  # Slow down to avoid 429
#         "AUTOTHROTTLE_ENABLED": True,
#         "AUTOTHROTTLE_START_DELAY": 1.0,
#         "AUTOTHROTTLE_MAX_DELAY": 10.0,
#         "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
#         "ROBOTSTXT_OBEY": False,
#         "FEED_EXPORT_ENCODING": "utf-8",
#         "RETRY_TIMES": 3,
#         "RETRY_HTTP_CODES": [429, 500, 502, 503, 504],
#     })
#     process.crawl(SmartEmailSpider, start_url=target_url)
#     process.start()


# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python smart_email_scraper.py https://example.com")
#         sys.exit(1)

#     target = sys.argv[1].strip()
#     run_scraper(target)






















# #!/usr/bin/env python3
# """
# smart_email_finder_v4.0.py

# AI Strategy Engine + robust crawling for extracting emails from
# professional directories and matching a person name to the correct email.

# Usage:
#     python smart_email_finder_v4.0.py https://www.finnegan.com "Anthony J. Lombardi"

# Options:
#     --no-ai         disable Groq/LLaMA usage
#     --no-playwright disable Playwright fallback
#     --workers N     set parallel HTTP workers (default 12)
# """
# import os, re, time, json, csv, string, argparse
# from urllib.parse import urljoin, urlparse
# from concurrent.futures import ThreadPoolExecutor, as_completed

# import requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from rapidfuzz import fuzz

# # Optional integrations
# try:
#     from groq import Groq
#     HAS_GROQ = True
# except Exception:
#     HAS_GROQ = False

# try:
#     from playwright.sync_api import sync_playwright
#     HAS_PLAYWRIGHT = True
# except Exception:
#     HAS_PLAYWRIGHT = False

# # ---------- config ----------
# load_dotenv()
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# groq_client = Groq(api_key=GROQ_API_KEY) if (HAS_GROQ and GROQ_API_KEY) else None
# MODEL = "llama-3.1-8b-instant"
# UA = "SmartEmailFinder/4.0"
# TIMEOUT = 12
# ALPHABET = string.ascii_lowercase
# DEFAULT_WORKERS = 12
# MAX_PROFILES = 10000
# EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)
# # ---------------------------

# def safe_json(resp):
#     try: return resp.json()
#     except Exception: return None

# def fetch_html(url, timeout=TIMEOUT):
#     try:
#         r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
#         if r.status_code == 200 and "text/html" in r.headers.get("Content-Type",""):
#             return r.text
#     except Exception:
#         pass
#     return None

# def extract_emails_from_text(text):
#     return sorted(set(EMAIL_RE.findall(text or "")))

# def normalize_domain(url):
#     p = urlparse(url)
#     return f"{p.scheme}://{p.netloc}"

# # ---------- AI helpers ----------
# def groq_chat(prompt, temp=0.0, max_tokens=600):
#     if not groq_client: return ""
#     try:
#         res = groq_client.chat.completions.create(
#             model=MODEL,
#             messages=[{"role":"system","content":"You are a web structure and extraction strategist."},
#                       {"role":"user","content":prompt}],
#             temperature=temp, max_tokens=max_tokens
#         )
#         return res.choices[0].message.content
#     except Exception as e:
#         print("⚠️ Groq error:", e)
#         return ""

# def ai_inspect_directory(html_snippet, url):
#     """
#     LLM decides which extraction strategy to use. Returns JSON-like dict:
#     { method: "aem_json_api"|"paged_html"|"javascript_scroll"|"static_links"|"hybrid"|"unknown",
#       endpoint: optional string,
#       pagination: optional dict,
#       keyword_hint: optional string,
#       notes: optional string }
#     """
#     if not groq_client or not html_snippet:
#         return {"method":"unknown"}
#     prompt = (
#         "You are an expert web engineer. Inspect this HTML snippet of a professionals/team directory and "
#         "decide the best extraction strategy to collect all profile pages. "
#         "Choose one method: aem_json_api, paged_html, javascript_scroll, static_links, hybrid, unknown. "
#         "If you detect an endpoint, include it. Return JSON only with keys: method, endpoint, pagination, keyword_hint, notes.\n\n"
#         f"URL: {url}\nHTML_SNIPPET:\n{html_snippet[:8000]}"
#     )
#     out = groq_chat(prompt)
#     if not out:
#         return {"method":"unknown"}
#     try:
#         m = re.search(r"\{.*\}", out, re.S)
#         return json.loads(m.group(0)) if m else {"method":"unknown"}
#     except Exception:
#         return {"method":"unknown"}

# def ai_normalize_name(name):
#     if not groq_client:
#         return name
#     prompt = (
#         "Expand or normalize a possibly abbreviated name. Return only the normalized name.\n\n"
#         f"Input: {name}"
#     )
#     out = groq_chat(prompt, temp=0.1, max_tokens=80).strip()
#     if not out:
#         return name
#     cleaned = re.sub(r"[^A-Za-z.\s'\-]", "", out).strip()
#     if len(cleaned.split()) >= 2 and len(cleaned) < 80:
#         return cleaned
#     return name

# def ai_validate_email_candidate(email, profile_text, person_name):
#     if not groq_client:
#         return None
#     prompt = (
#         "You are a verifier. Given a profile snippet and an email, return JSON {\"vote\":\"yes\"|\"no\",\"confidence\":0..1}.\n"
#         f"Person: {person_name}\nEmail: {email}\nProfile snippet:\n{profile_text[:2500]}\nReturn JSON only."
#     )
#     out = groq_chat(prompt, temp=0.0, max_tokens=200)
#     if not out:
#         return None
#     try:
#         m = re.search(r"\{.*\}", out, re.S)
#         j = json.loads(m.group(0)) if m else None
#         if j and "confidence" in j:
#             return float(j.get("confidence", 0))
#     except Exception:
#         pass
#     return None

# # ---------- AEM JSON alphabet fetch ----------
# def aem_alphabet_fetch(base):
#     """
#     Fetch A–Z professionals from Adobe AEM law-firm directories like Finnegan.
#     Tries POST (preferred) and falls back to GET.
#     """
#     api = urljoin(base, "/en/professionals/_jcr_content.search.json")
#     headers = {
#         "User-Agent": UA,
#         "Accept": "application/json, text/plain, */*",
#         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
#         "Referer": base,
#     }
#     all_profiles = set()

#     for ch in ALPHABET:
#         start = 0
#         while True:
#             params = {"keyword": ch, "start": start, "limit": 100}
#             try:
#                 # try POST first
#                 r = requests.post(api, data=params, headers=headers, timeout=TIMEOUT)
#                 if r.status_code != 200:
#                     # fallback GET
#                     r = requests.get(api, params=params, headers=headers, timeout=TIMEOUT)
#                 if r.status_code != 200:
#                     break

#                 j = safe_json(r)
#                 if not j or not j.get("results"):
#                     break

#                 results = j["results"]
#                 for it in results:
#                     link = None
#                     if isinstance(it, dict):
#                         link = (it.get("link") or {}).get("url") if isinstance(it.get("link"), dict) else (
#                             it.get("url") or it.get("path") or it.get("href")
#                         )
#                     if link:
#                         full = link if link.startswith("http") else urljoin(base, link)
#                         all_profiles.add(full.split("?")[0])

#                 start += 100
#                 time.sleep(0.1)
#             except Exception as e:
#                 # print("AEM fetch error:", e)
#                 break

#     print(f"   ✅ AEM POST/GET loop collected {len(all_profiles)} profiles total.")
#     return all_profiles


# # ---------- Playwright infinite-scroll collector ----------
# def playwright_deep_collect(directory_url, max_profiles=5000):
#     if not HAS_PLAYWRIGHT:
#         return set()
#     profiles = set()
#     parsed = urlparse(directory_url)
#     base = f"{parsed.scheme}://{parsed.netloc}"
#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             ctx = browser.new_context(user_agent=UA)
#             page = ctx.new_page()
#             page.goto(directory_url, timeout=60000)
#             time.sleep(1.0)
#             for _ in range(200):
#                 try:
#                     btns = page.locator("button:has-text('Load more'), button:has-text('Load More'), button:has-text('Show more')")
#                     if btns.count() > 0:
#                         try:
#                             btns.first.click(timeout=2000)
#                         except Exception:
#                             pass
#                 except Exception:
#                     pass
#                 try:
#                     page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
#                 except Exception:
#                     pass
#                 time.sleep(0.35)
#             html = page.content()
#             browser.close()
#             soup = BeautifulSoup(html, "html.parser")
#             for a in soup.select("a[href]"):
#                 href = a.get("href")
#                 if not href:
#                     continue
#                 if any(k in href for k in ("/professionals/","/people/","/team/")):
#                     full = href if href.startswith("http") else urljoin(base, href.split("#")[0])
#                     if urlparse(full).netloc == parsed.netloc:
#                         profiles.add(full.split("?")[0])
#     except Exception as e:
#         print("⚠️ Playwright error:", e)
#     return profiles

# # ---------- Paged HTML loop ----------
# def loop_paginated_directory(base_dir_url, step_values=(0,50,100,150,200,250)):
#     profiles = set()
#     for start in step_values:
#         paged = f"{base_dir_url}?start={start}"
#         html = fetch_html(paged)
#         if not html:
#             # try page param
#             paged2 = f"{base_dir_url}?page={start//50+1}"
#             html = fetch_html(paged2)
#             if not html:
#                 break
#         soup = BeautifulSoup(html, "html.parser")
#         found_any = False
#         for a in soup.select("a[href]"):
#             href = a.get("href")
#             if href and any(k in href for k in ("/professionals/","/people/")):
#                 profiles.add(urljoin(base_dir_url, href.split("#")[0]).split("?")[0])
#                 found_any = True
#         if not found_any:
#             break
#         time.sleep(0.08)
#     return profiles

# # ---------- Endpoint detection & probing ----------
# def detect_endpoints_in_html(base_url, html):
#     if not html:
#         return []
#     parsed = urlparse(base_url)
#     base = f"{parsed.scheme}://{parsed.netloc}"
#     candidates = set()
#     for m in re.finditer(r'https?://[^\s"\']+\.json', html, re.I):
#         candidates.add(m.group(0))
#     for m in re.finditer(r'["\'](/[^"\']*(?:search|people|profiles|professionals|api|graphql)[^"\']*)["\']', html, re.I):
#         candidates.add(base + m.group(1))
#     for m in re.finditer(r'fetch\(\s*["\']([^"\']+)["\']', html, re.I):
#         u = m.group(1)
#         candidates.add(u if u.startswith("http") else base + u)
#     for m in re.finditer(r'["\'](/graphql[^\s"\']*)["\']', html, re.I):
#         candidates.add(base + m.group(1))
#     return list(candidates)

# def probe_endpoint_for_profiles(api_url, base_domain, try_keyword_loop=False, limit=100, sample_limit=5000):
#     found_profiles = set()
#     headers = {"User-Agent": UA, "Accept":"application/json, text/plain, */*"}
#     base_dom = base_domain.rstrip("/")
#     def extract_urls_from_json(j):
#         res=set()
#         if not isinstance(j, (dict,list)):
#             return res
#         items=[]
#         if isinstance(j, dict):
#             for k in ("results","items","hits","nodes","profiles","people","data"):
#                 if isinstance(j.get(k), list):
#                     items.extend(j.get(k))
#             for v in j.values():
#                 if isinstance(v, list):
#                     items.extend(v)
#         elif isinstance(j, list):
#             items = j
#         for it in items:
#             if isinstance(it, dict):
#                 for key in ("link","url","path","href","profileUrl","profile"):
#                     v = it.get(key)
#                     if isinstance(v, dict) and v.get("url"):
#                         u = v.get("url")
#                         if u.startswith("/"):
#                             res.add(base_dom + u)
#                         elif u.startswith("http"):
#                             res.add(u)
#                     elif isinstance(v, str):
#                         if v.startswith("/"):
#                             res.add(base_dom + v)
#                         elif v.startswith("http"):
#                             res.add(v)
#             elif isinstance(it, str):
#                 for mm in re.finditer(r'https?://[^\s"\']+/[^\s"\']*professionals[^\s"\']*\.html', it, re.I):
#                     res.add(mm.group(0))
#         return res

#     if try_keyword_loop:
#         for ch in ALPHABET:
#             start=0
#             while True:
#                 params={"keyword":ch,"start":start,"limit":limit}
#                 try:
#                     r = requests.get(api_url, params=params, headers=headers, timeout=TIMEOUT)
#                     if r.status_code != 200:
#                         break
#                     j = safe_json(r)
#                     if not j:
#                         break
#                     found = extract_urls_from_json(j)
#                     if not found:
#                         break
#                     for u in found:
#                         found_profiles.add(u.split("?")[0])
#                     start += limit
#                     time.sleep(0.07)
#                     if len(found_profiles)>=sample_limit:
#                         return found_profiles
#                 except Exception:
#                     break
#         return found_profiles

#     # offset pagination
#     start=0
#     while True:
#         params={"start":start,"limit":limit}
#         try:
#             r = requests.get(api_url, params=params, headers=headers, timeout=TIMEOUT)
#             if r.status_code != 200:
#                 break
#             j = safe_json(r)
#             if not j:
#                 for mm in re.finditer(r'https?://[^\s"\']+/[^\s"\']*professionals[^\s"\']*\.html', r.text, re.I):
#                     found_profiles.add(mm.group(0))
#                 break
#             found = extract_urls_from_json(j)
#             if not found:
#                 break
#             for u in found: found_profiles.add(u.split("?")[0])
#             start += limit
#             time.sleep(0.07)
#             if len(found_profiles)>=sample_limit:
#                 break
#         except Exception:
#             break
#     return found_profiles

# # ---------- Recursive/AI-driven discovery ----------
# def discover_all_profiles(base_site, use_ai=True, use_playwright=True):
#     base = normalize_domain(base_site)
#     print("🔎 Finding directory candidates...")

#     candidates = [urljoin(base, p) for p in (
#         "/en/professionals/", "/professionals/", "/people/",
#         "/team/", "/our-team/", "/en/people/"
#     )]

#     homepage = fetch_html(base)
#     if homepage:
#         for m in re.finditer(r'href=["\']([^"\']+)["\']', homepage, re.I):
#             href = m.group(1)
#             if any(k in href.lower() for k in ("profession", "people", "team", "attorney", "our-people")):
#                 candidates.append(urljoin(base, href.split("#")[0]))
#     seen=set(); candidates=[c for c in candidates if c and (c not in seen and not seen.add(c))]

#     all_profiles=set()

#     # --- 1️⃣ FORCE AEM JSON STRATEGY FOR LAW-FIRM-LIKE DOMAINS ---
#     possible_api = urljoin(base, "/en/professionals/_jcr_content.search.json")
#     print(f"  ⚙️ Testing for hidden AEM endpoint: {possible_api}")
#     try:
#         headers={"User-Agent":UA,"Accept":"application/json, text/plain, */*"}
#         test = requests.get(possible_api, params={"keyword":"a","start":0,"limit":1}, headers=headers, timeout=8)
#         if test.ok and (test.text.strip().startswith("{") or "json" in test.headers.get("Content-Type","").lower()):
#             print("   ✅ Hidden AEM JSON endpoint confirmed! Fetching full A–Z directory...")
#             all_profiles.update(aem_alphabet_fetch(base))
#             print(f"   -> Collected {len(all_profiles)} profiles from AEM API.")
#             if all_profiles:
#                 return all_profiles
#         else:
#             # 👇 If it's a /professionals/ page but JSON not directly visible, still assume AEM.
#             if any("/professionals" in c for c in candidates):
#                 print("   ⚙️ No direct JSON response, but /professionals/ structure found — assuming AEM anyway.")
#                 all_profiles.update(aem_alphabet_fetch(base))
#                 print(f"   -> Fetched {len(all_profiles)} profiles from heuristic AEM fetch.")
#                 if all_profiles:
#                     return all_profiles
#     except Exception:
#         pass

#     # iterate candidates and let AI decide strategy
#     for d in candidates:
#         print("Probing:", d)
#         html = fetch_html(d)
#         ai_plan = {}
#         if use_ai and groq_client and html:
#             ai_plan = ai_inspect_directory(html, d) or {}
#             print("  AI hint:", ai_plan)
#         method = ai_plan.get("method")

#         # If AI suggests explicit endpoint (aem_json_api), honor it
#         if method == "aem_json_api" or (ai_plan.get("endpoint") and "search.json" in (ai_plan.get("endpoint") or "")):
#             endpoint = ai_plan.get("endpoint") or "/en/professionals/_jcr_content.search.json"
#             api_full = urljoin(base, endpoint)
#             print("   ⚙️ AI-chosen AEM endpoint ->", api_full)
#             try:
#                 found = probe_endpoint_for_profiles(api_full, base, try_keyword_loop=True)
#                 if found:
#                     print(f"   -> Found {len(found)} profiles via AI-suggested endpoint.")
#                     all_profiles.update(found)
#                     if len(all_profiles) >= MAX_PROFILES: return all_profiles
#                     continue
#             except Exception:
#                 pass

#         # paged_html
#         if method == "paged_html":
#             print("   ⚙️ AI chosen paged_html")
#             found = loop_paginated_directory(d)
#             if found:
#                 all_profiles.update(found)
#                 continue

#         # javascript_scroll -> detect hidden endpoints inside scripts, else Playwright
#         if method == "javascript_scroll":
#             print("   ⚙️ AI chosen javascript_scroll")
#             # look for hidden AEM pattern in html content too
#             if html and "/_jcr_content.search.json" in html:
#                 api_candidate = urljoin(base, "/en/professionals/_jcr_content.search.json")
#                 print("   ⚙️ Found AEM pattern in script; probing", api_candidate)
#                 try:
#                     found = probe_endpoint_for_profiles(api_candidate, base, try_keyword_loop=True)
#                     if found:
#                         all_profiles.update(found)
#                         if len(all_profiles) >= MAX_PROFILES: return all_profiles
#                         continue
#                 except Exception:
#                     pass
#             # detect endpoints via extract
#             endpoints = detect_endpoints_in_html(d, html or "")
#             for ep in (endpoints or [])[:6]:
#                 found = probe_endpoint_for_profiles(ep, base, try_keyword_loop=True)
#                 if found:
#                     all_profiles.update(found)
#                     if len(all_profiles) >= MAX_PROFILES: return all_profiles
#                     break
#             # if still empty try Playwright
#             if use_playwright:
#                 p = playwright_deep_collect(d)
#                 if p:
#                     all_profiles.update(p)
#                     continue

#         # hybrid
#         if method == "hybrid":
#             print("   ⚙️ AI chosen hybrid (scroll then probe)")
#             if use_playwright:
#                 p = playwright_deep_collect(d)
#                 if p:
#                     all_profiles.update(p)
#             # then try probing endpoints discovered
#             endpoints = detect_endpoints_in_html(d, html or "")
#             for ep in (endpoints or [])[:6]:
#                 found = probe_endpoint_for_profiles(ep, base, try_keyword_loop=True)
#                 if found: all_profiles.update(found)
#             continue

#         # static_links or unknown -> parse anchors
#         if not method or method in ("static_links","unknown"):
#             if html:
#                 soup = BeautifulSoup(html, "html.parser")
#                 for a in soup.select("a[href]"):
#                     href = a.get("href")
#                     if not href: continue
#                     if any(k in href for k in ("/professionals/","/people/","/team/")):
#                         full = href if href.startswith("http") else urljoin(base, href.split("#")[0])
#                         if urlparse(full).netloc == urlparse(base).netloc:
#                             all_profiles.add(full.split("?")[0])
#     return all_profiles

# # ---------- Parallel extraction ----------
# def extract_emails_parallel(urls, workers=DEFAULT_WORKERS):
#     results=[]
#     def worker(u):
#         try:
#             r = requests.get(u, headers={"User-Agent":UA}, timeout=TIMEOUT)
#             if r.status_code != 200:
#                 return {"url":u,"emails":[],"text":""}
#             t = r.text
#             emails = extract_emails_from_text(t)
#             return {"url":u,"emails":emails,"text":t}
#         except Exception:
#             return {"url":u,"emails":[],"text":""}
#     with ThreadPoolExecutor(max_workers=workers) as ex:
#         futures = {ex.submit(worker,u):u for u in urls}
#         for fut in as_completed(futures):
#             results.append(fut.result())
#     return results

# # ---------- name->email pattern matcher ----------
# def generate_name_patterns(full_name):
#     parts=[p for p in re.split(r"[\s.]+", full_name.strip().lower()) if p]
#     if not parts: return []
#     first, last = parts[0], parts[-1]
#     patterns = [f"{first}.{last}", f"{first}{last}", f"{first[0]}{last}", f"{first}{last[0]}", f"{last}{first}", f"{first}_{last}"]
#     seen=set(); out=[]
#     for p in patterns:
#         if p not in seen: out.append(p); seen.add(p)
#     return out

# def choose_best_email_by_patterns(name, emails, domain_hint=None, use_ai=True, profile_texts=None):
#     if not emails: return (None,0.0)
#     patterns = generate_name_patterns(name)
#     scored=[]
#     domain = domain_hint or (emails[0].split("@",1)[1] if "@" in emails[0] else None)
#     for e in emails:
#         local = e.split("@")[0].lower()
#         best = 0.0
#         for p in patterns:
#             best = max(best, fuzz.partial_ratio(local, p)/100.0)
#         if domain and e.lower().endswith("@"+domain.lower()): best += 0.08
#         best = min(best,1.0)
#         # optional light AI refinement for top-scoring items
#         ai_conf = None
#         if use_ai and groq_client and best >= 0.6:
#             # find sample text for this email if provided
#             sample_text = ""
#             if profile_texts:
#                 sample_text = profile_texts.get(e, "")[:2500]
#             ai_conf = ai_validate_email_candidate(e, sample_text, name)
#         final = best if ai_conf is None else round((best*0.45 + ai_conf*0.55),3)
#         scored.append((final,e))
#     scored.sort(reverse=True, key=lambda x:x[0])
#     return scored[0] if scored else (None,0.0)

# # ---------- main ----------
# def main():
#     parser=argparse.ArgumentParser()
#     parser.add_argument("site", help="Base site URL")
#     parser.add_argument("name", nargs="?", help="Optional person name (first last)")
#     parser.add_argument("--no-ai", action="store_true", help="Disable Groq usage")
#     parser.add_argument("--no-playwright", action="store_true", help="Disable Playwright fallback")
#     parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
#     args=parser.parse_args()

#     base = args.site.rstrip("/")
#     parsed = urlparse(base)
#     if not parsed.netloc:
#         print("Provide valid site like https://example.com"); return
#     base_domain = f"{parsed.scheme}://{parsed.netloc}"
#     use_ai = (not args.no_ai) and (groq_client is not None)
#     use_playwright = (not args.no_playwright) and HAS_PLAYWRIGHT

#     name_input = args.name
#     if name_input and use_ai:
#         try:
#             name_norm = ai_normalize_name(name_input)
#         except Exception:
#             name_norm = name_input
#     else:
#         name_norm = name_input or None
#     print(f"🔤 Normalized name: {name_norm}")

#     print("1) Discovering profiles (AI-driven)...")
#     profiles = discover_all_profiles(base_domain, use_ai=use_ai, use_playwright=use_playwright)
#     profiles_list = sorted(profiles)
#     print(f"→ Discovered {len(profiles_list)} profiles (sample {profiles_list[:6]})")
#     if not profiles_list:
#         print("No profiles discovered. Exiting."); return

#     # include the directory pages too
#     extras = {base_domain, urljoin(base_domain,"/en/professionals/"), urljoin(base_domain,"/professionals/")}
#     to_fetch = sorted(set(profiles_list) | extras)
#     print(f"2) Extracting emails from {len(to_fetch)} pages (parallel={args.workers})...")
#     records = extract_emails_parallel(to_fetch, workers=args.workers)
#     all_emails=[]
#     profile_texts={}
#     email_sources={}
#     for rec in records:
#         for e in rec.get("emails",[]):
#             el = e.lower()
#             if el not in email_sources: email_sources[el]=set()
#             email_sources[el].add(rec.get("url"))
#             if el not in all_emails:
#                 all_emails.append(el)
#             # record sample text for AI validation
#             if el not in profile_texts and rec.get("text"):
#                 profile_texts[el] = rec.get("text")

#     print(f"→ Extracted {len(all_emails)} unique emails")

#     results=[]
#     if name_norm:
#         score, best_email = choose_best_email_by_patterns(name_norm, all_emails, domain_hint=parsed.netloc, use_ai=use_ai, profile_texts=profile_texts)
#         if not best_email or score < 0.25:
#             # fuzzy fallback across locals
#             fuzzy=[]
#             for e in all_emails:
#                 local=e.split("@")[0]
#                 s=max(fuzz.token_set_ratio(name_norm, local)/100.0, fuzz.partial_ratio(name_norm.lower(), local.lower())/100.0)
#                 fuzzy.append((s,e))
#             fuzzy.sort(reverse=True, key=lambda x:x[0])
#             if fuzzy:
#                 score, best_email = fuzzy[0]
#         if best_email:
#             print(f"✅ Best email: {best_email}  confidence={score:.3f}")
#             results.append({"email":best_email,"sources":";".join(sorted(email_sources.get(best_email,[]))),"confidence":score})
#         else:
#             print("❌ No candidate email found.")
#     else:
#         for e in all_emails:
#             results.append({"email":e,"sources":";".join(sorted(email_sources.get(e,[]))),"confidence":1.0})

#     if results:
#         out="results_v4.0.csv"
#         with open(out,"w",newline="",encoding="utf-8") as f:
#             w=csv.DictWriter(f, fieldnames=["email","sources","confidence"])
#             w.writeheader()
#             for r in results: w.writerow(r)
#         print(f"Saved {len(results)} results to {out}")
#     else:
#         print("No results to save.")

# if __name__=="__main__":
#     main()





#############################################amost done##########################################################
# #!/usr/bin/env python3
# """
# smart_email_finder_v5.0.py
# Universal AI + Adaptive Strategy Email Finder

# Usage:
#     python smart_email_finder_v5.0.py <homepage_url> "<person_name>"

# Requirements:
#     pip install playwright groq requests beautifulsoup4 python-dotenv
#     playwright install chromium
# """

# import os, re, sys, json, requests, difflib
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
# from dotenv import load_dotenv
# from playwright.sync_api import sync_playwright
# from groq import Groq

# # ===== Load config =====
# load_dotenv()
# GROQ_KEY = os.getenv("GROQ_API_KEY")
# MODEL = "llama-3.1-8b-instant"
# client = Groq(api_key=GROQ_KEY)
# UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36"


# # ===== Helper functions =====
# def render_page(url):
#     """Fully render page with JS and return HTML + links."""
#     print(f"🌐 Rendering: {url}")
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page(user_agent=UA)
#         page.goto(url, wait_until="networkidle", timeout=90000)
#         html = page.content()
#         links = [urljoin(url, a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
#         browser.close()
#     return html, list(set(links))


# def extract_emails(text):
#     """Extract all email-like patterns."""
#     return list(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))


# # ===== AI functions =====
# def ai_decide_directory(home_url, links):
#     """AI + heuristic: pick the right directory page intelligently."""
#     # Prefer links with people/team indicators
#     preferred_keywords = ["people", "attorneys", "lawyers", "professionals", "our-team", "team"]
#     candidates = [l for l in links if any(k in l.lower() for k in preferred_keywords)]
#     if not candidates:
#         candidates = [l for l in links if "about" in l.lower()]

#     # Ask AI to pick the best one among candidates
#     prompt = f"""
# You are analyzing a law firm's website.
# From the following URLs, pick the ONE that most likely leads to the page listing lawyers or professionals (NOT management or contact pages).
# Return only JSON like:
# {{"directory": "<URL>"}}

# URLs:
# {candidates[:100]}
# """
#     try:
#         resp = client.chat.completions.create(
#             model=MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1,
#         )
#         content = resp.choices[0].message.content
#         result = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
#         return result.get("directory")
#     except Exception:
#         # fallback heuristic
#         for c in candidates:
#             if any(k in c.lower() for k in ["people", "attorney", "lawyer", "professional"]):
#                 return c
#         return candidates[0] if candidates else None


# def ai_pick_profile(name, urls):
#     """Ask AI to pick the URL most likely belonging to the person."""
#     prompt = f"""
# Given these profile URLs, find the one belonging to {name}.
# Return JSON only:
# {{"profile_url": "<URL>"}}

# URLs:
# {urls[:100]}
# """
#     try:
#         resp = client.chat.completions.create(
#             model=MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.0,
#         )
#         data = json.loads(re.search(r"\{.*\}", resp.choices[0].message.content, re.S).group(0))
#         url = data.get("profile_url", "none")
#     except Exception:
#         url = "none"

#     # fallback fuzzy
#     if url == "none" or "http" not in url:
#         name_parts = name.lower().replace(".", "").split()
#         matches = [u for u in urls if all(part in u.lower() for part in name_parts[:2])]
#         if matches:
#             url = matches[0]
#         else:
#             best = difflib.get_close_matches(name.lower().replace(" ", "-"), urls, n=1)
#             url = best[0] if best else "none"
#     return url


# def ai_choose_email(name, emails, text):
#     """LLM picks which email belongs to the given person."""
#     if not emails:
#         return "❌ No emails found."
#     prompt = f"""
# Given these emails: {emails}
# and the following webpage text, pick the one that clearly belongs to {name}.
# Return only the email address.

# TEXT:
# {text[:2000]}
# """
#     r = client.chat.completions.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.0,
#     )
#     return r.choices[0].message.content.strip()


# # ===== Site Structure Detection =====
# def detect_structure(url):
#     """Detect if site uses AEM, WordPress, GraphQL, or static HTML."""
#     try:
#         r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
#         text = r.text.lower()
#         if "_jcr_content.search.json" in text or "aemassets" in text:
#             return "aem"
#         if "wp-json" in text or "wp-content" in text:
#             return "wordpress"
#         if "graphql" in text or "/api/" in text:
#             return "graphql"
#     except:
#         pass
#     return "html"


# # ===== Scraping strategies =====
# def fetch_aem_profiles(base_url):
#     """Paginate AEM JSON endpoints."""
#     print("⚙️ Using AEM JSON API pagination...")
#     all_profiles = set()
#     for start in range(0, 1000, 50):
#         url = urljoin(base_url, f"_jcr_content.search.json?c=professional&q=&start={start}")
#         try:
#             r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
#             data = r.json()
#             hits = data.get("hits", [])
#             if not hits:
#                 break
#             for h in hits:
#                 if "path" in h:
#                     all_profiles.add(urljoin(base_url, h["path"]))
#         except:
#             break
#     print(f"✅ Found {len(all_profiles)} profiles from AEM API.")
#     return list(all_profiles)


# def fetch_wordpress_profiles(base_url):
#     """Fetch team members from WordPress REST API."""
#     print("⚙️ Using WordPress REST API...")
#     urls = []
#     try:
#         r = requests.get(urljoin(base_url, "/wp-json/wp/v2/pages"), timeout=20)
#         if r.status_code == 200:
#             for entry in r.json():
#                 if "slug" in entry and any(k in entry["slug"] for k in ["team", "people", "attorney"]):
#                     urls.append(urljoin(base_url, entry["link"]))
#     except:
#         pass
#     print(f"✅ Found {len(urls)} team pages.")
#     return urls


# def fetch_graphql_profiles(directory_url):
#     """Scroll through React/SPA directory."""
#     print("⚙️ Using Playwright infinite scroll...")
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page(user_agent=UA)
#         page.goto(directory_url, wait_until="networkidle", timeout=90000)
#         last_height = 0
#         for _ in range(15):
#             page.mouse.wheel(0, 3000)
#             page.wait_for_timeout(1000)
#             new_height = page.evaluate("document.body.scrollHeight")
#             if new_height == last_height:
#                 break
#             last_height = new_height
#         links = [urljoin(directory_url, a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
#         browser.close()
#     profiles = [u for u in links if any(k in u.lower() for k in ["professional", "people", "team", "attorney"])]
#     print(f"✅ Found {len(profiles)} profile links via scroll.")
#     return profiles


# def fetch_html_profiles(directory_url):
#     """Enhanced: Detects load-more or scroll and captures all profiles."""
#     print("⚙️ Using HTML (hybrid) scraping...")
#     profiles = set()

#     # First, simple HTML fetch
#     try:
#         r = requests.get(directory_url, headers={"User-Agent": UA}, timeout=15)
#         soup = BeautifulSoup(r.text, "html.parser")
#         links = [urljoin(directory_url, a["href"]) for a in soup.select("a[href]")]
#         for u in links:
#             if any(k in u.lower() for k in ["professional", "people", "team", "attorney", "bio"]):
#                 profiles.add(u)
#     except:
#         pass

#     # If too few links, try Playwright scroll
#     if len(profiles) < 100:
#         print("↪️ Detected dynamic directory — switching to scroll mode...")
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             page = browser.new_page(user_agent=UA)
#             page.goto(directory_url, wait_until="networkidle", timeout=90000)
#             last_height = 0
#             for _ in range(20):
#                 page.mouse.wheel(0, 3000)
#                 page.wait_for_timeout(1500)
#                 new_height = page.evaluate("document.body.scrollHeight")
#                 if new_height == last_height:
#                     break
#                 last_height = new_height

#             links = [urljoin(directory_url, a.get_attribute("href"))
#                      for a in page.query_selector_all("a[href]")]
#             for u in links:
#                 if any(k in u.lower() for k in ["professional", "people", "team", "attorney", "bio"]):
#                     profiles.add(u)
#             browser.close()

#     print(f"✅ Found {len(profiles)} profile links after hybrid scan.")
#     return list(profiles)


# # ===== Main =====
# def main():
#     if len(sys.argv) < 3:
#         print("Usage: python smart_email_finder_v5.0.py <homepage_url> <person_name>")
#         sys.exit(1)

#     home_url, person_name = sys.argv[1], sys.argv[2]
#     print(f"🔤 Normalized name: {person_name}")

#     # Step 1: render homepage and collect links
#     home_html, home_links = render_page(home_url)

#     # Step 2: AI decides which link is team/professionals
#     directory = ai_decide_directory(home_url, home_links)
#     if not directory:
#         print("❌ Could not identify directory page.")
#         return
#     print(f"➡️ Directory chosen: {directory}")
#     if "about-us" in directory.lower() and "/people/" in home_url:
#         directory = urljoin(home_url, "/people/")

#     # Step 3: detect structure
#     structure = detect_structure(directory)
#     print(f"🧩 Detected site type: {structure}")

#     # Step 4: apply correct strategy
#     if structure == "aem":
#         profiles = fetch_aem_profiles(directory)
#     elif structure == "wordpress":
#         profiles = fetch_wordpress_profiles(home_url)
#     elif structure == "graphql":
#         profiles = fetch_graphql_profiles(directory)
#     else:
#         profiles = fetch_html_profiles(directory)

#     if not profiles:
#         print("❌ No profiles found.")
#         return

#     # Step 5: AI chooses which profile belongs to the person
#     profile = ai_pick_profile(person_name, profiles)
#     if profile == "none":
#         print("❌ Could not locate profile.")
#         return
#     print(f"➡️ Profile chosen: {profile}")

#     # Step 6: extract email from that page
#     html, _ = render_page(profile)
#     emails = extract_emails(html)
#     print(f"📧 Found {len(emails)} email(s): {emails}")

#     # Step 7: AI picks best match
#     best_email = ai_choose_email(person_name, emails, html)

#     print("\n==============================")
#     print(f"👤 {person_name}")
#     print(f"✅ Likely email: {best_email}")
#     print("==============================")


# if __name__ == "__main__":
#     main()


































# #!/usr/bin/env python3
# """
# smart_email_finder_failover.py

# Universal email finder with a robust LLM-powered failover layer.

# Usage:
#     python smart_email_finder_failover.py <homepage_url> "<person_name>"

# Behavior:
#  - Normal flow: detect directory, choose profile, extract email (as in v5).
#  - FAILOVER: If profile not found or no emails extracted, run a site-wide search:
#      * Render homepage and a short list of internal pages (links),
#      * Extract text + run regex,
#      * Ask the LLM (strict JSON output) to find explicit emails that are actually present and tied to the person.
#  - LLM is instructed NOT to guess. If it cannot find explicit emails, it returns [].

# Note: Run responsibly. Respect robots.txt & site rate limits when using at scale.
# """

# import os, re, sys, json, time, requests, difflib
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

# UA = "SmartEmailFinder/1.0 (+https://github.com/)"
# REQUEST_TIMEOUT = 15
# MAX_SITE_PAGES = 25           # how many internal pages to fetch in failover
# PLAYWRIGHT_SCROLL_TRIES = 12  # when scrolling dynamic directories
# # ------------------------------------

# # ---------- utility functions ----------
# def render_page_html_and_links(url, headless=True, scroll=False, scroll_tries=5):
#     """Render page with Playwright, return HTML and absolute links."""
#     print(f"🌐 Render: {url}")
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=headless)
#         page = browser.new_page(user_agent=UA)
#         page.goto(url, wait_until="networkidle", timeout=90000)
#         if scroll:
#             last_h = 0
#             for _ in range(scroll_tries):
#                 page.mouse.wheel(0, 3000)
#                 page.wait_for_timeout(800)
#                 new_h = page.evaluate("document.body.scrollHeight")
#                 if new_h == last_h:
#                     break
#                 last_h = new_h
#         html = page.content()
#         # gather links
#         els = page.query_selector_all("a[href]")
#         links = []
#         for a in els:
#             try:
#                 href = a.get_attribute("href")
#                 if href:
#                     links.append(urljoin(url, href.split("#")[0]))
#             except Exception:
#                 continue
#         browser.close()
#     return html, list(dict.fromkeys(links))  # preserve unique order

# def simple_fetch_html_links(url):
#     """Fast HTTP GET + parse links (fallback)"""
#     try:
#         r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
#         if r.status_code != 200:
#             return "", []
#         soup = BeautifulSoup(r.text, "html.parser")
#         links = []
#         for a in soup.select("a[href]"):
#             href = a.get("href")
#             if href:
#                 links.append(urljoin(url, href.split("#")[0]))
#         return r.text, list(dict.fromkeys(links))
#     except Exception:
#         return "", []

# def extract_emails_from_text(text):
#     """Return list of unique emails found via regex."""
#     emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
#     return list(dict.fromkeys([e.lower() for e in emails]))

# def domain_only(url):
#     try:
#         p = urlparse(url)
#         return f"{p.scheme}://{p.netloc}"
#     except:
#         return url

# # ---------- AI helpers (strict JSON) ----------
# def llm_sitewide_search(name, pages): 
#     """
#     pages: list of dict {url, text_snippet}
#     Instruct LLM to search these snippets for explicit emails belonging to `name`.
#     IMPORTANT: LLM MUST return strict JSON:
#       {"results": [{"email": "...", "url": "...", "context": "...", "confidence": 0.0}, ...]}
#     - It must NOT invent any email.
#     - If nothing found, return {"results": []}
#     """
#     # Build compact context (truncate each snippet)
#     sample_data = []
#     for p in pages:
#         snippet = p["text"][:2000].replace("\n", " ")
#         sample_data.append({"url": p["url"], "text": snippet})
#     prompt = f"""
# You are a careful web-extraction assistant. You will be given a list of page url + text snippets.
# Task: Find any e-mail addresses that are explicitly present in the provided text snippets that clearly belong to the person named: "{name}".

# Rules (must follow):
# 1) Do NOT guess or invent. Only return emails that literally appear in the supplied text snippets.
# 2) Return output ONLY as JSON matching exactly this schema:
#    {{
#      "results": [
#        {{
#          "email": "<email address exactly as found>",
#          "url": "<page url where it appears>",
#          "context": "<short text (<=200 chars) around the email>",
#          "confidence": <float 0.0-1.0 — 1.0 means exact match / email shown with name nearby>
#        }},
#        ...
#      ]
#    }}
# 3) If you find no explicit emails in the provided snippets, return: {"results": []}
# 4) When deciding confidence:
#    - If the snippet contains the person's full name near the email, use confidence 0.95-1.0.
#    - If the snippet contains only last name or initials near the email, use 0.6-0.85.
#    - If email is present but no nearby name, use 0.3-0.6.
# 5) For context include up to ~200 characters surrounding the email.

# Here are the pages (url + snippet). Keep JSON machine-parseable only.
# Pages:
# {json.dumps(sample_data, ensure_ascii=False)[:38000]}
# """
#     resp = client.chat.completions.create(
#         model=MODEL,
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.0,
#         max_tokens=800,
#     )
#     raw = resp.choices[0].message.content.strip()
#     # extract JSON object from raw
#     try:
#         jtext = re.search(r"\{.*\}", raw, re.S).group(0)
#         data = json.loads(jtext)
#         # normalize emails lower-case
#         for r in data.get("results", []):
#             r["email"] = r["email"].strip().lower()
#             r["context"] = r.get("context","")[:300]
#             r["url"] = r.get("url","")
#             r["confidence"] = float(r.get("confidence", 0.0))
#         return data.get("results", [])
#     except Exception as e:
#         print("LLM failed to return strict JSON or parsing failed:", e)
#         return []

# # ---------- main failover routine ----------
# def sitewide_failover_search(home_url, person_name, max_pages=MAX_SITE_PAGES):
#     """
#     1) Render homepage, gather internal links (breadth-first up to max_pages)
#     2) Render each candidate page (Playwright) and collect text snippets
#     3) Run regex to gather any emails across pages
#     4) If regex finds candidate emails, pass snippets+emails to LLM for final decision
#     """
#     base = domain_only(home_url)
#     print("🔎 Failover: sitewide search starting from homepage...")

#     # 1) render home quickly, collect candidate links
#     html, links = render_page_html_and_links(home_url, headless=True, scroll=False)
#     internal_links = [l for l in links if urlparse(l).netloc == urlparse(home_url).netloc]
#     # keep order, limit
#     candidate_links = internal_links[: max_pages]
#     # always include home_url first
#     if home_url not in candidate_links:
#         candidate_links.insert(0, home_url)

#     pages = []
#     seen = set()
#     # 2) render each candidate and extract text
#     for url in candidate_links:
#         if url in seen:
#             continue
#         seen.add(url)
#         try:
#             # for directories/likely dynamic pages, scroll briefly
#             scroll = any(k in url.lower() for k in ("/people", "/professionals", "/team", "/about"))
#             html, _ = render_page_html_and_links(url, headless=True, scroll=scroll, scroll_tries=4)
#             # extract visible text
#             soup = BeautifulSoup(html, "html.parser")
#             for s in soup(["script","style","noscript","svg"]):
#                 s.decompose()
#             text = soup.get_text(" ", strip=True)
#             snippet = text[:5000]
#             pages.append({"url": url, "text": snippet})
#         except Exception as e:
#             # fallback fetch
#             t, _ = simple_fetch_html_links(url)
#             pages.append({"url": url, "text": (t or "")[:5000]})
#         # polite delay
#         time.sleep(0.6)

#     # 3) quick regex pass across page texts
#     found_emails = {}
#     for p in pages:
#         es = extract_emails_from_text(p["text"])
#         for e in es:
#             found_emails.setdefault(e, []).append(p["url"])

#     # If regex found emails, prepare pages with context for LLM; else still run LLM (on text) to search for mentions
#     if found_emails:
#         print(f"🔎 Regex discovered {len(found_emails)} unique email(s) across site.")
#     else:
#         print("🔎 Regex found 0 emails — will still run LLM to search text for explicit emails (if present).")

#     # 4) Ask LLM (strict JSON) to identify which emails belong to person_name
#     results = llm_sitewide_search(person_name, pages)
#     # results are verified by LLM to be present in the snippets
#     if results:
#         # sort by confidence desc
#         results_sorted = sorted(results, key=lambda r: r.get("confidence",0), reverse=True)
#         return results_sorted

#     # if LLM returns nothing but regex found some emails, do local heuristics:
#     if found_emails:
#         local_candidates = []
#         for e, urls in found_emails.items():
#             # compute heuristic score: presence of name in page text near email?
#             score = 0.0
#             candidate_context = ""
#             for u in urls:
#                 page = next((p for p in pages if p["url"] == u), None)
#                 if not page: continue
#                 idx = page["text"].lower().find(e.lower())
#                 context = page["text"][max(0, idx-60): idx+len(e)+60] if idx>=0 else page["text"][:200]
#                 candidate_context = context.strip()
#                 if person_name.lower() in context.lower():
#                     score = max(score, 0.95)
#                 elif any(part.lower() in context.lower() for part in person_name.split()):
#                     score = max(score, 0.7)
#                 else:
#                     score = max(score, 0.4)
#             local_candidates.append({"email": e, "url": urls[0], "context": candidate_context, "confidence": score})
#         # sort by heuristic confidence
#         return sorted(local_candidates, key=lambda r: r["confidence"], reverse=True)

#     # nothing found
#     return []

# # ---------- main agent (integrates with prior v5 flow) ----------
# # For brevity, this file assumes you already have the v5 main functions:
# # - ai_decide_directory, detect_structure, fetch_aem_profiles, fetch_html_profiles,
# # - ai_pick_profile, ai_choose_email, etc.
# # We'll include a small main that tries the usual flow and then calls failover when needed.

# # Minimal re-implementations / lightweight copy of detection + selection (keeps script self-contained)
# def render_page(url):
#     html, links = render_page_html_and_links(url, headless=True, scroll=False, scroll_tries=3)
#     return html, links

# def detect_structure_quick(url):
#     """Quick detect by HEAD/GET text."""
#     try:
#         r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT)
#         text = (r.text or "").lower()
#         if "_jcr_content.search.json" in text or "aemassets" in text:
#             return "aem"
#         if "wp-json" in text or "wp-content" in text:
#             return "wordpress"
#         if "graphql" in text or "/api/" in text:
#             return "graphql"
#     except:
#         pass
#     return "html"

# def ai_decide_directory_quick(home_url, links):
#     """Very small heuristic + LLM picking (keeps concise)."""
#     # prefer anything that looks like people/team/professional/attorney
#     candidates = [l for l in links if any(k in l.lower() for k in ("people","professional","team","attorney","lawyer"))]
#     if not candidates:
#         candidates = links[:30]
#     # Ask LLM but force JSON output
#     prompt = f"""
# Select the ONE URL most likely to be the people/professionals directory for the site {home_url}.
# Return ONLY JSON: {{ "directory": "<url or none>" }}
# Candidates:
# {candidates[:60]}
# """
#     try:
#         r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.0)
#         raw = r.choices[0].message.content
#         data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
#         return data.get("directory")
#     except:
#         return candidates[0] if candidates else None

# def ai_pick_profile_quick(name, urls):
#     """Ask LLM to pick profile url with strict JSON, fallback fuzzy."""
#     prompt = f"""
# From this list of profile URLs, pick the one that most likely belongs to '{name}'.
# Return JSON only: {{ "profile_url": "<url or 'none'>" }}
# URLs:
# {urls[:150]}
# """
#     try:
#         r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.0)
#         raw = r.choices[0].message.content
#         data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
#         url = data.get("profile_url", "none")
#     except:
#         url = "none"
#     if url in ("none", None) or "http" not in str(url):
#         name_parts = name.lower().replace(".", "").split()
#         matches = [u for u in urls if all(part in u.lower() for part in name_parts[:2])]
#         if matches:
#             url = matches[0]
#         else:
#             best = difflib.get_close_matches(name.lower().replace(" ", "-"), urls, n=1)
#             url = best[0] if best else "none"
#     return url

# def ai_choose_email_quick(name, emails, text):
#     """LLM picks email or returns nothing. Strict output not enforced here for brevity."""
#     if not emails:
#         return None
#     prompt = f"""
# Given these emails {emails} and this page text snippet, which email belongs to {name}? Return the single email or 'none'.
# TEXT:
# {text[:2000]}
# """
#     r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.0)
#     return r.choices[0].message.content.strip()

# # ---------- main ----------
# def main():
#     if len(sys.argv) < 3:
#         print("Usage: python smart_email_finder_failover.py <homepage_url> <person_name>")
#         sys.exit(1)
#     home_url = sys.argv[1].rstrip("/")
#     person_name = sys.argv[2].strip()
#     print(f"🔤 Searching for: {person_name} @ {home_url}")

#     # 1) Render home and collect links
#     home_html, home_links = render_page(home_url)

#     # 2) Decide directory
#     directory = ai_decide_directory_quick(home_url, home_links)
#     if not directory:
#         print("⚠️ Could not identify directory page; proceeding to sitewide failover.")
#         results = sitewide_failover_search(home_url, person_name)
#         if results:
#             print_results(results, person_name)
#             return
#         print("❌ Nothing found.")
#         return

#     print(f"➡️ Directory: {directory}")

#     # 3) detect structure and gather profile links
#     structure = detect_structure_quick(directory)
#     print(f"🧩 Detected: {structure}")
#     profile_urls = []
#     if "aem" in structure:
#         # full AEM pagination (simple)
#         for start in range(0,1000,50):
#             api = urljoin(directory, f"_jcr_content.search.json?c=professional&q=&start={start}")
#             try:
#                 r = requests.get(api, headers={"User-Agent":UA}, timeout=REQUEST_TIMEOUT)
#                 if r.status_code != 200: break
#                 j = r.json()
#                 hits = j.get("hits", [])
#                 if not hits: break
#                 for h in hits:
#                     path = h.get("path") or h.get("url") or ""
#                     if path:
#                         profile_urls.append(urljoin(directory, path))
#             except: break
#     elif structure == "graphql":
#         profile_urls = fetch_graphql_profiles(directory)  # use earlier defined function from v5 flow
#     elif structure == "wordpress":
#         profile_urls = fetch_wordpress_profiles(directory)
#     else:
#         profile_urls = fetch_html_profiles(directory)

#     profile_urls = list(dict.fromkeys(profile_urls))
#     print(f"🔎 Collected {len(profile_urls)} profile URLs")

#     # 4) Ask AI to pick the person profile
#     chosen = ai_pick_profile_quick(person_name, profile_urls)
#     if chosen and chosen != "none":
#         print(f"➡️ Chosen profile: {chosen}")
#         # render and extract
#         html, _ = render_page_html_and_links(chosen, headless=True, scroll=True, scroll_tries=4)
#         emails = extract_emails_from_text(BeautifulSoup(html,'html.parser').get_text(" ",strip=True))
#         if emails:
#             # let LLM pick
#             final = ai_choose_email_quick(person_name, emails, html)
#             print("\nRESULT (direct):")
#             print({"profile": chosen, "emails_found": emails, "llm_choice": final})
#             return

#     # 5) If we reach here, run failover sitewide LLM-backed search
#     print("↪️ Primary profile extraction failed — running intelligent sitewide failover.")
#     results = sitewide_failover_search(home_url, person_name)
#     if results:
#         print_results(results, person_name)
#     else:
#         print("❌ No explicit emails found on site.")

# def print_results(results, name):
#     print("\n==============================")
#     print(f"👤 {name}")
#     for r in results:
#         print(f"📧 {r['email']}  (confidence={r.get('confidence',0):.2f})")
#         print(f"🔗 {r.get('url')}")
#         print(f"✂ context: {r.get('context')[:160]}")
#         print("------------------------------")
#     print("==============================")

# # helpers from v5 reused (minimal)
# def fetch_graphql_profiles(directory_url):
#     # Playwright scroll method (kept minimal)
#     print("⚙️ Scroll-fetch (Playwright) for dynamic lists...")
#     with sync_playwright() as p:
#         browser=p.chromium.launch(headless=True)
#         page=browser.new_page(user_agent=UA)
#         page.goto(directory_url, wait_until="networkidle", timeout=90000)
#         last_h=0
#         for _ in range(PLAYWRIGHT_SCROLL_TRIES):
#             page.mouse.wheel(0,3000)
#             page.wait_for_timeout(800)
#             new_h=page.evaluate("document.body.scrollHeight")
#             if new_h==last_h: break
#             last_h=new_h
#         links=[urljoin(directory_url,a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
#         browser.close()
#     profiles=[u for u in links if any(k in u.lower() for k in ("people","professional","team","attorney","person"))]
#     return list(dict.fromkeys(profiles))

# def fetch_wordpress_profiles(base_url):
#     print("⚙️ WordPress: simple REST fallback")
#     urls=[]
#     try:
#         r = requests.get(urljoin(base_url, "/wp-json/wp/v2/pages"), headers={"User-Agent":UA}, timeout=REQUEST_TIMEOUT)
#         if r.status_code==200:
#             for e in r.json():
#                 link = e.get("link") or e.get("slug")
#                 if link and any(k in (link or "").lower() for k in ("team","people","attorney","professional")):
#                     urls.append(link if link.startswith("http") else urljoin(base_url, link))
#     except: pass
#     return list(dict.fromkeys(urls))

# def fetch_html_profiles(directory_url):
#     print("⚙️ HTML fallback: fetch & small render hybrid")
#     # first try fast GET
#     try:
#         r = requests.get(directory_url, headers={"User-Agent":UA}, timeout=REQUEST_TIMEOUT)
#         soup=BeautifulSoup(r.text,'html.parser')
#         links=[urljoin(directory_url,a['href']) for a in soup.select("a[href]")]
#         profiles=[u for u in links if any(k in u.lower() for k in ("people","professional","team","attorney","bio"))]
#         if len(profiles)>150:
#             return list(dict.fromkeys(profiles))
#     except: profiles=[]
#     # fallback to Playwright scroll + collect links
#     with sync_playwright() as p:
#         browser=p.chromium.launch(headless=True)
#         page=browser.new_page(user_agent=UA)
#         page.goto(directory_url, wait_until="networkidle", timeout=90000)
#         last_h=0
#         for _ in range(PLAYWRIGHT_SCROLL_TRIES):
#             page.mouse.wheel(0,3000)
#             page.wait_for_timeout(800)
#             new_h=page.evaluate("document.body.scrollHeight")
#             if new_h==last_h: break
#             last_h=new_h
#         links=[urljoin(directory_url,a.get_attribute("href")) for a in page.query_selector_all("a[href]")]
#         browser.close()
#     profiles=[u for u in links if any(k in u.lower() for k in ("people","professional","team","attorney","bio"))]
#     return list(dict.fromkeys(profiles))

# # ---------- run ----------
# if __name__ == "__main__":
#     main()





########################################################################almost
#!/usr/bin/env python3
"""
smart_email_finder.py - v2.0 SIMPLIFIED & INTELLIGENT
------------------------------------------------------
Handles ANY website type with intelligent fallback logic.

Flow:
1. Try to find professional profile → Extract email
2. If fails → Go to contact page → Extract general email
3. Done! (No complex site-wide searches)
"""

import os
import re
import sys
import json
import requests
import difflib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from groq import Groq

# -------------- CONFIG --------------
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    print("❌ Missing GROQ_API_KEY in .env")
    sys.exit(1)

MODEL = "llama-3.1-8b-instant"
client = Groq(api_key=GROQ_KEY)
UA = "SmartEmailFinder/2.0"

# ------------------------------------
# CORE UTILITIES
# ------------------------------------

def render_page(url, scroll=False, timeout=30000):
    """Render page with Playwright - handles dynamic content."""
    print(f"🌐 Rendering: {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=UA)
            page.goto(url, wait_until="networkidle", timeout=timeout)
            
            if scroll:
                for _ in range(3):
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(500)
            
            html = page.content()
            
            # Extract links
            links = []
            for a in page.query_selector_all("a[href]"):
                try:
                    href = a.get_attribute("href")
                    if href:
                        links.append(urljoin(url, href.split("#")[0]))
                except:
                    continue
            
            browser.close()
            return html, list(dict.fromkeys(links))
    except Exception as e:
        print(f"⚠️ Playwright failed: {e}, trying simple fetch")
        return simple_fetch(url)


def simple_fetch(url):
    """Simple HTTP GET - fallback for when Playwright fails."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        if r.status_code >= 400:
            return "", []
        
        soup = BeautifulSoup(r.text, "html.parser")
        links = [urljoin(url, a.get("href", "")) for a in soup.find_all("a", href=True)]
        return r.text, list(dict.fromkeys(links))
    except:
        return "", []


def extract_emails_from_text(text):
    """Extract all emails from text using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    # Filter out obvious junk
    valid_emails = [
        e.lower() for e in emails 
        if len(e) < 100 
        and not any(x in e.lower() for x in ["noreply", "no-reply", "example", "test"])
    ]
    return list(dict.fromkeys(valid_emails))


def extract_text_from_html(html):
    """Extract clean text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        element.decompose()
    return soup.get_text(" ", strip=True)


# ------------------------------------
# AI HELPERS
# ------------------------------------

def ai_find_directory(home_url, links):
    """AI finds the professionals directory URL."""
    # Filter to likely candidates
    candidates = [
        l for l in links 
        if any(k in l.lower() for k in ["people", "professional", "team", "attorney", "lawyer", "our-people"])
        and not any(x in l.lower() for x in ["news", "blog", "event", "career", "job"])
    ]
    
    if not candidates:
        candidates = links[:20]
    
    if not candidates:
        return None
    
    prompt = f"""
Find the professionals/people directory URL for this law firm website.

Homepage: {home_url}
Candidate URLs: {json.dumps(candidates[:30])}

Return ONLY JSON: {{"directory": "<url>"}}
If none found, return: {{"directory": null}}
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200
        )
        text = resp.choices[0].message.content.strip()
        data = json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0))
        return data.get("directory")
    except:
        return candidates[0] if candidates else None


def ai_pick_profile(person_name, profile_urls):
    """AI picks the most likely profile URL for the person."""
    if not profile_urls:
        return None
    
    # Try fuzzy matching first
    name_parts = person_name.lower().replace(".", "").split()
    matches = [u for u in profile_urls if all(part in u.lower() for part in name_parts[:2])]
    
    if len(matches) == 1:
        return matches[0]
    
    # If multiple or none, ask AI
    prompt = f"""
Pick the profile URL that most likely belongs to: "{person_name}"

URLs: {json.dumps((matches or profile_urls)[:50])}

Return ONLY JSON: {{"profile_url": "<url>"}}
If uncertain, return: {{"profile_url": null}}
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200
        )
        text = resp.choices[0].message.content.strip()
        data = json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0))
        return data.get("profile_url")
    except:
        return matches[0] if matches else None


def ai_validate_email(email, person_name, page_text):
    """AI validates if email belongs to person."""
    prompt = f"""
Does this email belong to this person based on the page content?

Email: {email}
Person: {person_name}
Page text: {page_text[:1000]}

Consider:
1. Username matches name (e.g., "john.smith" matches "John Smith")
2. Email appears near person's name in text
3. Not a general email (info@, contact@)

Return ONLY JSON: {{"valid": true/false, "confidence": 0.0-1.0}}
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=150
        )
        text = resp.choices[0].message.content.strip()
        data = json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0))
        return data
    except:
        return {"valid": True, "confidence": 0.5}


# ------------------------------------
# MAIN EXTRACTION LOGIC
# ------------------------------------

def extract_from_contact_page(home_url):
    """Extract general contact email from contact page."""
    print("📧 Searching contact page for general email...")
    
    # Common contact page URLs
    contact_urls = [
        urljoin(home_url, "/contact"),
        urljoin(home_url, "/contact-us"),
        urljoin(home_url, "/contact-us/"),
        urljoin(home_url, "/en/contact"),
        urljoin(home_url, "/en/contact-us"),
        home_url
    ]
    
    for url in contact_urls:
        try:
            html, _ = simple_fetch(url)
            if not html:
                continue
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for mailto links
            for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
                email = a["href"].replace("mailto:", "").replace("MAILTO:", "").split("?")[0].strip()
                if email and "@" in email:
                    print(f"✅ Found contact email: {email}")
                    return email.lower()
            
            # Look for emails in text
            text = soup.get_text()
            emails = extract_emails_from_text(text)
            
            if emails:
                # Prefer contact/info emails
                priority = [e for e in emails if any(x in e for x in ["contact", "info", "general"])]
                email = priority[0] if priority else emails[0]
                print(f"✅ Found contact email: {email}")
                return email.lower()
        
        except Exception as e:
            print(f"⚠️ Error on {url}: {e}")
            continue
    
    print("❌ No contact email found")
    return None


def find_email_from_site(home_url: str, person_name: str):
    """
    Main function - Find email for a person on a law firm website.
    
    Returns list of dicts: [{'email': '...', 'url': '...', 'confidence': 0.95}]
    """
    print(f"\n🔍 SEARCHING: {person_name} @ {home_url}")
    print("=" * 70)
    
    try:
        # STEP 1: Render homepage and get links
        home_html, home_links = render_page(home_url)
        
        # STEP 2: Find professionals directory
        directory = ai_find_directory(home_url, home_links)
        
        if not directory:
            print("⚠️ No professionals directory found")
            print("↪️ Going to contact page for general email")
            general_email = extract_from_contact_page(home_url)
            if general_email:
                return [{"email": general_email, "url": home_url, "confidence": 0.6, "context": "General contact"}]
            return []
        
        print(f"✅ Directory: {directory}")
        
        # STEP 3: Get all profile links from directory
        print("🔎 Collecting profile links...")
        dir_html, dir_links = render_page(directory, scroll=True)
        
        # Filter to actual profile links
        profile_urls = [
            l for l in dir_links
            if any(k in l.lower() for k in ["/people/", "/professional/", "/attorney/", "/team/", "/bio/", "/person/"])
            and l != directory  # Don't include directory itself
            and not any(x in l.lower() for x in ["search", "filter", "sort", "page=", "?"])
        ]
        
        profile_urls = list(dict.fromkeys(profile_urls))[:100]  # Limit to 100
        print(f"✅ Found {len(profile_urls)} profile URLs")
        
        if not profile_urls:
            print("⚠️ No profile links found")
            print("↪️ Going to contact page for general email")
            general_email = extract_from_contact_page(home_url)
            if general_email:
                return [{"email": general_email, "url": home_url, "confidence": 0.6, "context": "General contact"}]
            return []
        
        # STEP 4: Pick the right profile
        profile_url = ai_pick_profile(person_name, profile_urls)
        
        if not profile_url:
            print("⚠️ Could not identify profile")
            print("↪️ Going to contact page for general email")
            general_email = extract_from_contact_page(home_url)
            if general_email:
                return [{"email": general_email, "url": home_url, "confidence": 0.6, "context": "General contact"}]
            return []
        
        print(f"✅ Profile: {profile_url}")
        
        # STEP 5: Extract email from profile
        profile_html, _ = render_page(profile_url, scroll=True)
        profile_text = extract_text_from_html(profile_html)
        emails = extract_emails_from_text(profile_text)
        
        if not emails:
            print("⚠️ No emails on profile page")
            print("↪️ Going to contact page for general email")
            general_email = extract_from_contact_page(home_url)
            if general_email:
                return [{"email": general_email, "url": home_url, "confidence": 0.6, "context": "General contact"}]
            return []
        
        # STEP 6: Validate emails with AI
        results = []
        for email in emails:
            validation = ai_validate_email(email, person_name, profile_text)
            if validation.get("valid", False):
                results.append({
                    "email": email,
                    "url": profile_url,
                    "confidence": validation.get("confidence", 0.8),
                    "context": f"Found on {person_name}'s profile"
                })
        
        if results:
            # Sort by confidence
            results.sort(key=lambda x: x["confidence"], reverse=True)
            print(f"✅ Found {len(results)} valid email(s)")
            for r in results:
                print(f"   📧 {r['email']} (confidence: {r['confidence']:.2f})")
            return results
        
        # No valid emails found - fallback to contact
        print("⚠️ No valid professional emails found")
        print("↪️ Going to contact page for general email")
        general_email = extract_from_contact_page(home_url)
        if general_email:
            return [{"email": general_email, "url": home_url, "confidence": 0.6, "context": "General contact"}]
        
        return []
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("↪️ Trying contact page as fallback")
        general_email = extract_from_contact_page(home_url)
        if general_email:
            return [{"email": general_email, "url": home_url, "confidence": 0.5, "context": "Fallback contact"}]
        return []


# ------------------------------------
# CLI INTERFACE
# ------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: python smart_email_finder.py <website_url> '<person_name>'")
        print("Example: python smart_email_finder.py https://www.finnegan.com 'Anthony J. Lombardi'")
        sys.exit(1)
    
    website = sys.argv[1].rstrip("/")
    person = sys.argv[2].strip()
    
    results = find_email_from_site(website, person)
    
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    
    if results:
        for r in results:
            print(f"📧 {r['email']}")
            print(f"🔗 {r['url']}")
            print(f"📊 Confidence: {r['confidence']:.2f}")
            print(f"💬 {r.get('context', 'N/A')}")
            print("-" * 70)
    else:
        print("❌ No emails found")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
