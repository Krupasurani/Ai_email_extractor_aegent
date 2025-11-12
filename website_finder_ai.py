
# #!/usr/bin/env python3
# """
# Official Website Selector – shows Top 5 candidates for each firm.
# """

# import os, re, json, logging, asyncio, hashlib, socket
# import pandas as pd
# from ddgs import DDGS

# # --------------------------------------------------------------------
# logging.basicConfig(level=logging.INFO, format="%(message)s")
# logger = logging.getLogger(__name__)

# CACHE_DIR = "search_cache"
# os.makedirs(CACHE_DIR, exist_ok=True)
# ddgs = DDGS()

# # --------------------------------------------------------------------
# def cached_search(query: str, max_results: int = 15):
#     """Cache DuckDuckGo search results to avoid repeat queries."""
#     key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
#     cache_file = os.path.join(CACHE_DIR, f"{key}.json")
#     if os.path.exists(cache_file):
#         return json.load(open(cache_file, "r", encoding="utf-8"))
#     results = list(ddgs.text(query, max_results=max_results))
#     json.dump(results, open(cache_file, "w", encoding="utf-8"), indent=2)
#     return results

# # --------------------------------------------------------------------
# def simple_score(firm_name, address, r):
#     """Base scoring fallback."""
#     url = r.get("href", "").lower()
#     title = r.get("title", "").lower()
#     body = r.get("body", "").lower()
#     domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
#     score = 0

#     firm_tokens = [t for t in re.split(r"[^a-z]", firm_name.lower()) if len(t) > 2]
#     for t in firm_tokens:
#         if t in domain: score += 6
#         elif t in title: score += 3
#         elif t in body: score += 1

#     if len(domain.split(".")) <= 3: score += 5
#     if domain.endswith((".com", ".law", ".legal")): score += 5
#     if any(k in domain for k in ["law", "llp", "attorney", "legal"]): score += 4
#     if any(k in title for k in ["law", "llp", "attorney", "legal"]): score += 3

#     blacklist = [
#         "linkedin","justia","bloomberg","martindale","findlaw","law360",
#         "zoominfo","crunchbase","usnews","wikipedia","glassdoor","indeed",
#         "mapquest","neverbounce","panjiva","superlawyers","lawinfo","drugs.com",
#         "microsoft","tennis","wilsoncombat","wilson.edu","lawyers.com","directory",
#         "profile","bizstanding","media-index","10times"
#     ]
#     if any(b in domain for b in blacklist):
#         score -= 60

#     if url.startswith("https://") and url.count("/") <= 3: score += 3
#     if re.search(r"\.(ru|cn|jp|info|xyz|top|click|site|biz|io)\b", domain): score -= 15

#     return score

# # --------------------------------------------------------------------
# def pick_best_url(firm_name, results):
#     """Stage 1: return ranked top 5 candidates."""
#     scored = [(simple_score(firm_name, "", r), r.get("href")) for r in results]
#     scored.sort(key=lambda x: x[0], reverse=True)
#     top5 = scored[:5]
#     return top5

# # --------------------------------------------------------------------
# def try_direct_domain(firm_name):
#     """Try smart domain guesses for multi-word firm names."""
#     name = firm_name.lower()
#     name = re.sub(r"[,;&]", " ", name)
#     name = re.sub(r"\b(llp|llc|law|attorneys?|firm|group|partners?|co|company)\b", "", name)
#     tokens = [t for t in re.split(r"[^a-z]", name) if t]

#     candidates = set()
#     if tokens:
#         candidates.add(tokens[0])
#     if len(tokens) >= 2:
#         candidates.add(tokens[0] + tokens[1])
#     if len(tokens) > 1:
#         acronym = "".join(t[0] for t in tokens if t)
#         if len(acronym) >= 3:
#             candidates.add(acronym)

#     final_domains = []
#     for base in candidates:
#         for suffix in [".com", "law.com", "llp.com", ".law"]:
#             final_domains.append(f"https://{base}{suffix}")

#     for c in final_domains:
#         try:
#             host = re.sub(r"https?://", "", c).split("/")[0]
#             socket.gethostbyname(host)
#             return c
#         except Exception:
#             continue
#     return None

# # --------------------------------------------------------------------
# async def website_selector(firm_name, address=""):
#     """Main selector logic – always show top 5 search results."""
#     # Still try direct guess, but don't return immediately
#     direct = try_direct_domain(firm_name)
#     if direct:
#         logger.info(f"✅ Direct domain guess: {direct}")
#     else:
#         logger.info(f"⚠️ No direct domain guess resolved.")

#     # --- Always run a web search anyway ---
#     query = f"{firm_name} {address} official website"
#     logger.info(f"\n🔍 Searching: {query}")
#     results = cached_search(query, max_results=15)
#     if not results:
#         logger.warning("No results found.")
#         return None

#     # Compute top 5
#     top5 = pick_best_url(firm_name, results)
#     logger.info("🔝 Top 5 website candidates:")
#     for rank, (score, url) in enumerate(top5, 1):
#         logger.info(f"  {rank}. {url} (score {score})")

#     best = top5[0][1] if top5 else None
#     logger.info(f"✅ Selected: {best}\n")
#     return best

# # --------------------------------------------------------------------
# async def process_excel(path):
#     df = pd.read_excel(path)
#     print(f"\nLoaded {len(df)} rows from Excel.")

#     for i, row in df.iterrows():
#         firm_name = str(row.get("Representative") or "").strip()
#         address = str(row.get("Representative address") or "").strip()

#         if not firm_name:
#             print(f"[{i+1}] ⚠️ Skipped empty firm name.")
#             continue

#         print(f"\n[{i+1}] 🔍 Searching for: {firm_name} | {address}")
#         await website_selector(firm_name, address)

# # --------------------------------------------------------------------
# if __name__ == "__main__":
#     file_path = input("\n📁 Enter Excel file path: ").strip()
#     if not os.path.exists(file_path):
#         print("❌ File not found.")
#     else:
#         asyncio.run(process_excel(file_path))




# #!/usr/bin/env python3
# """
# Official Website Selector (DDGS + Bing hybrid) – shows Top 5 candidates per firm.
# """

# import os, re, json, logging, asyncio, hashlib, socket, aiohttp
# import pandas as pd
# from ddgs import DDGS

# # --------------------------------------------------------------------
# logging.basicConfig(level=logging.INFO, format="%(message)s")
# logger = logging.getLogger(__name__)

# CACHE_DIR = "search_cache_ddgs_bing"
# os.makedirs(CACHE_DIR, exist_ok=True)

# # --------------------------------------------------------------------
# async def bing_fallback(query, max_results=10):
#     """Free Bing search fallback (via public Bing HTML)."""
#     url = f"https://www.bing.com/search?q={query}"
#     headers = {"User-Agent": "Mozilla/5.0"}
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, headers=headers, timeout=10) as resp:
#             text = await resp.text()
#     # Extract links manually
#     links = re.findall(r'<a href="(https://[^"]+)" h="ID=', text)
#     results = [{"title": "", "href": l, "body": ""} for l in links[:max_results]]
#     return results

# # --------------------------------------------------------------------
# def cached_search(query: str, max_results: int = 15):
#     key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
#     cache_file = os.path.join(CACHE_DIR, f"{key}.json")
#     if os.path.exists(cache_file):
#         return json.load(open(cache_file, "r", encoding="utf-8"))

#     ddgs = DDGS()
#     results = list(ddgs.text(query, max_results=max_results))
#     if not results:
#         logger.warning("⚠️ DDG empty — using Bing fallback")
#         results = asyncio.run(bing_fallback(query, max_results))
#     json.dump(results, open(cache_file, "w", encoding="utf-8"), indent=2)
#     return results

# # --------------------------------------------------------------------
# def simple_score(firm_name, r):
#     url = (r.get("href") or "").lower()
#     title = (r.get("title") or "").lower()
#     domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
#     score = 0
#     tokens = [t for t in re.split(r"[^a-z]", firm_name.lower()) if len(t) > 2]
#     for t in tokens:
#         if t in domain: score += 6
#         elif t in title: score += 3
#     if domain.endswith((".com", ".law", ".llp")): score += 5
#     if any(k in domain for k in ["law", "legal", "attorney"]): score += 4
#     blacklist = [
#         "linkedin", "bloomberg", "martindale", "findlaw", "usnews",
#         "wikipedia", "indeed", "glassdoor", "directory", "lawyers.com",
#         "justia", "zoominfo", "neverbounce", "bizstanding"
#     ]
#     if any(b in domain for b in blacklist): score -= 40
#     return score

# def pick_best_url(firm_name, results):
#     scored = [(simple_score(firm_name, r), r.get("href")) for r in results if r.get("href")]
#     scored.sort(key=lambda x: x[0], reverse=True)
#     return scored[:20]

# def try_direct_domain(firm_name):
#     name = re.sub(r"[,;&]", " ", firm_name.lower())
#     name = re.sub(r"\b(llp|llc|law|firm|group|partners?|co|company)\b", "", name)
#     tokens = [t for t in re.split(r"[^a-z]", name) if t]
#     candidates = set()
#     if tokens: candidates.add(tokens[0])
#     if len(tokens) >= 2: candidates.add(tokens[0] + tokens[1])
#     if len(tokens) > 1:
#         ac = "".join(t[0] for t in tokens if t)
#         if len(ac) >= 3: candidates.add(ac)
#     for base in candidates:
#         for suffix in [".com", "law.com", ".law"]:
#             url = f"https://{base}{suffix}"
#             try:
#                 socket.gethostbyname(url.replace("https://", ""))
#                 return url
#             except:
#                 continue
#     return None

# # --------------------------------------------------------------------
# async def website_selector(firm_name, address=""):
#     direct = try_direct_domain(firm_name)
#     if direct:
#         logger.info(f"✅ Direct domain guess: {direct}")
#     query = f"{firm_name} {address} official website"
#     logger.info(f"\n🔍 Searching: {query}")
#     results = cached_search(query, max_results=15)
#     if not results:
#         logger.warning("No results found.")
#         return None
#     top5 = pick_best_url(firm_name, results)
#     logger.info("🔝 Top 5 website candidates:")
#     for i, (s, u) in enumerate(top5, 1):
#         logger.info(f"  {i}. {u} (score {s})")
#     best = top5[0][1] if top5 else None
#     logger.info(f"✅ Selected: {best}\n")
#     return best

# # --------------------------------------------------------------------
# async def process_excel(path):
#     df = pd.read_excel(path)
#     print(f"\nLoaded {len(df)} rows from Excel.")
#     for i, row in df.iterrows():
#         firm = str(row.get("Representative") or "").strip()
#         addr = str(row.get("Representative address") or "").strip()
#         if not firm:
#             continue
#         print(f"\n[{i+1}] 🔍 Searching for: {firm} | {addr}")
#         await website_selector(firm, addr)

# if __name__ == "__main__":
#     fp = input("\n📁 Enter Excel file path: ").strip()
#     if os.path.exists(fp):
#         asyncio.run(process_excel(fp))
#     else:
#         print("❌ File not found.")



# #!/usr/bin/env python3
# """
# AI Website Finder (DDG + Bing + Google hybrid)
# - Reads Excel (Representative + Address)
# - Searches via DuckDuckGo, Bing, and Google
# - Scores & ranks top 5 websites per firm
# - Saves to Website_Results.xlsx
# """

# import os, re, json, logging, asyncio, hashlib, socket, aiohttp, time
# import pandas as pd
# from ddgs import DDGS
# from googlesearch import search as google_search

# # --------------------------------------------------------------------
# logging.basicConfig(level=logging.INFO, format="%(message)s")
# logger = logging.getLogger(__name__)

# CACHE_DIR = "search_cache_hybrid"
# os.makedirs(CACHE_DIR, exist_ok=True)

# # --------------------------------------------------------------------
# async def bing_search_html(query, max_results=10):
#     """Free Bing HTML fallback."""
#     url = f"https://www.bing.com/search?q={query}"
#     headers = {"User-Agent": "Mozilla/5.0"}
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, headers=headers, timeout=10) as resp:
#             text = await resp.text()
#     links = re.findall(r'<a href="(https://[^"]+)" h="ID=', text)
#     results = [{"title": "", "href": l, "body": ""} for l in links[:max_results]]
#     return results

# def cached_search(query: str, max_results: int = 15):
#     """DDG + Bing + Google hybrid search with caching."""
#     key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
#     cache_file = os.path.join(CACHE_DIR, f"{key}.json")
#     if os.path.exists(cache_file):
#         return json.load(open(cache_file, "r", encoding="utf-8"))

#     ddgs = DDGS()
#     results = list(ddgs.text(query, max_results=max_results))

#     # If DDG failed, try Bing fallback
#     if not results:
#         logger.warning("⚠️ DDG empty, switching to Bing fallback...")
#         results = asyncio.run(bing_search_html(query, max_results))

#     # Add Google results (small polite delay)
#     logger.info("🔍 Adding Google HTML results...")
#     google_results = []
#     try:
#         for url in google_search(query, num=max_results, stop=max_results, pause=2):
#             google_results.append({"href": url})
#     except Exception as e:
#         logger.warning(f"⚠️ Google fallback failed: {e}")

#     all_results = results + google_results

#     # Remove duplicates
#     seen, unique = set(), []
#     for r in all_results:
#         link = r.get("href")
#         if not link or link in seen:
#             continue
#         seen.add(link)
#         unique.append(r)

#     json.dump(unique, open(cache_file, "w", encoding="utf-8"), indent=2)
#     return unique[:max_results]

# # --------------------------------------------------------------------
# def simple_score(firm_name, r):
#     url = (r.get("href") or "").lower()
#     title = (r.get("title") or "").lower()
#     domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
#     score = 0
#     tokens = [t for t in re.split(r"[^a-z]", firm_name.lower()) if len(t) > 2]
#     for t in tokens:
#         if t in domain: score += 6
#         elif t in title: score += 3
#     if domain.endswith((".com", ".law", ".llp")): score += 5
#     if any(k in domain for k in ["law", "legal", "attorney"]): score += 4
#     blacklist = [
#         "linkedin", "bloomberg", "martindale", "findlaw", "usnews",
#         "wikipedia", "indeed", "glassdoor", "directory", "lawyers.com",
#         "justia", "zoominfo", "neverbounce", "bizstanding", "superlawyers"
#     ]
#     if any(b in domain for b in blacklist): score -= 40
#     return score

# def pick_best_urls(firm_name, results):
#     scored = [(simple_score(firm_name, r), r.get("href")) for r in results if r.get("href")]
#     scored.sort(key=lambda x: x[0], reverse=True)
#     return scored[:15]

# def try_direct_domain(firm_name):
#     name = re.sub(r"[,;&]", " ", firm_name.lower())
#     name = re.sub(r"\b(llp|llc|law|firm|group|partners?|co|company)\b", "", name)
#     tokens = [t for t in re.split(r"[^a-z]", name) if t]
#     candidates = set()
#     if tokens: candidates.add(tokens[0])
#     if len(tokens) >= 2: candidates.add(tokens[0] + tokens[1])
#     if len(tokens) > 1:
#         ac = "".join(t[0] for t in tokens if t)
#         if len(ac) >= 3: candidates.add(ac)
#     for base in candidates:
#         for suffix in [".com", "law.com", ".law"]:
#             url = f"https://{base}{suffix}"
#             try:
#                 socket.gethostbyname(url.replace("https://", ""))
#                 return url
#             except:
#                 continue
#     return None

# # --------------------------------------------------------------------
# async def website_selector(firm_name, address=""):
#     """Main selector: finds and ranks top 5 websites for a firm."""
#     direct = try_direct_domain(firm_name)
#     if direct:
#         logger.info(f"✅ Direct domain guess: {direct}")

#     query = f"{firm_name} {address} official website"
#     logger.info(f"\n🔍 Searching: {query}")

#     results = cached_search(query, max_results=15)
#     if not results:
#         logger.warning("No results found.")
#         return []

#     top5 = pick_best_urls(firm_name, results)
#     logger.info("🔝 Top 5 website candidates:")
#     for i, (s, u) in enumerate(top5, 1):
#         logger.info(f"  {i}. {u} (score {s})")

#     if top5:
#         logger.info(f"✅ Selected: {top5[0][1]}\n")
#     else:
#         logger.info("⚠️ No valid results.\n")

#     return top5

# # --------------------------------------------------------------------
# async def process_excel(path):
#     df = pd.read_excel(path)
#     print(f"\nLoaded {len(df)} rows from Excel.")
#     output_rows = []

#     for i, row in df.iterrows():
#         firm = str(row.get("Representative") or "").strip()
#         addr = str(row.get("Representative address") or "").strip()
#         if not firm:
#             continue
#         print(f"\n[{i+1}] 🔍 Searching for: {firm} | {addr}")
#         top5 = await website_selector(firm, addr)
#         for rank, (score, url) in enumerate(top5, 1):
#             output_rows.append({
#                 "Representative": firm,
#                 "Address": addr,
#                 "Rank": rank,
#                 "Score": score,
#                 "URL": url
#             })

#     # Save results
#     out_df = pd.DataFrame(output_rows)
#     out_path = "Website_Results.xlsx"
#     out_df.to_excel(out_path, index=False)
#     print(f"\n✅ All done! Saved top results to: {out_path}")

# # --------------------------------------------------------------------
# if __name__ == "__main__":
#     fp = input("\n📁 Enter Excel file path: ").strip()
#     if os.path.exists(fp):
#         asyncio.run(process_excel(fp))
#     else:
#         print("❌ File not found.")

###################################################################################################almost 90%%%%%%%#######################################################
# #!/usr/bin/env python3
# """
# AI Firm Website Finder – Hybrid Search + LLM Verification (v2)
# - Robust LLM parsing + retries
# - Self-healing validation of LLM choice
# """

# import os
# import re
# import json
# import logging
# import asyncio
# import hashlib
# import socket
# import time
# from typing import List, Optional, Dict, Any

# import pandas as pd
# from ddgs import DDGS
# from dotenv import load_dotenv

# # Optional: if you have 'groq' package installed
# try:
#     from groq import Groq
#     GROQ_AVAILABLE = True
# except Exception:
#     GROQ_AVAILABLE = False

# # --------------------------------------------------------------------
# load_dotenv()

# logging.basicConfig(level=logging.INFO, format="%(message)s")
# logger = logging.getLogger(__name__)

# CACHE_DIR = "search_cache_v2"
# os.makedirs(CACHE_DIR, exist_ok=True)
# ddgs = DDGS()

# # --------------------------------------------------------------------
# def cached_search(query: str, max_results: int = 15) -> List[Dict[str, Any]]:
#     """Cache DuckDuckGo results to avoid re-querying a lot."""
#     key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
#     cache_file = os.path.join(CACHE_DIR, f"{key}.json")
#     if os.path.exists(cache_file):
#         try:
#             return json.load(open(cache_file, "r", encoding="utf-8"))
#         except Exception:
#             pass

#     results = list(ddgs.text(query, max_results=max_results))
#     # normalize structure: ensure dicts with href/title/body keys
#     normalized = []
#     for r in results:
#         if isinstance(r, dict):
#             normalized.append({
#                 "href": r.get("href") or r.get("link") or "",
#                 "title": r.get("title") or "",
#                 "body": r.get("body") or ""
#             })
#         else:
#             normalized.append({"href": str(r), "title": "", "body": ""})

#     json.dump(normalized, open(cache_file, "w", encoding="utf-8"), indent=2)
#     return normalized[:max_results]

# # --------------------------------------------------------------------
# def domain_of(url: str) -> str:
#     if not url:
#         return ""
#     d = re.sub(r"https?://(www\.)?", "", url.lower()).split("/")[0]
#     # strip port
#     return d.split(":")[0]

# def firm_tokens_from_name(firm_name: str) -> List[str]:
#     tokens = [t for t in re.split(r"[^a-z]", firm_name.lower()) if len(t) > 2]
#     return tokens

# def simple_score(firm_name: str, r: Dict[str, Any]) -> int:
#     url = (r.get("href") or "").lower()
#     title = (r.get("title") or "").lower()
#     body = (r.get("body") or "").lower()
#     domain = domain_of(url)
#     score = 0
#     tokens = firm_tokens_from_name(firm_name)
#     for t in tokens:
#         if t in domain:
#             score += 7
#         elif t in title:
#             score += 3
#         elif t in body:
#             score += 1

#     if len(domain.split(".")) <= 3:
#         score += 4
#     if domain.endswith((".com", ".law", ".llp")):
#         score += 4
#     if any(k in domain for k in ["law", "legal", "attorney"]):
#         score += 3

#     blacklist = [
#         "linkedin","bloomberg","martindale","findlaw","usnews","wikipedia",
#         "indeed","glassdoor","mapquest","zoominfo","superlawyers","lawinfo",
#         "drugs.com","wilson.com","wilsoncombat","office.com"
#     ]
#     if any(b in domain for b in blacklist):
#         score -= 50

#     # prefer short clean paths
#     if url.startswith("https://") and url.count("/") <= 3:
#         score += 2

#     # Penalize weird TLDs
#     if re.search(r"\.(ru|cn|info|xyz|top|click|site|biz|io)\b", domain):
#         score -= 10

#     return score

# def pick_best_urls(firm_name: str, results: List[Dict[str, Any]], top_n: int = 5):
#     scored = []
#     for r in results:
#         href = r.get("href") or ""
#         if not href:
#             continue
#         scored.append((simple_score(firm_name, r), href))
#     scored.sort(key=lambda x: x[0], reverse=True)
#     return scored[:top_n]

# # --------------------------------------------------------------------
# def try_direct_domain(firm_name: str) -> Optional[str]:
#     name = re.sub(r"[,;&]", " ", firm_name.lower())
#     name = re.sub(r"\b(llp|llc|law|firm|group|partners?|co|company|attorneys?)\b", "", name)
#     tokens = [t for t in re.split(r"[^a-z]", name) if t]
#     candidates = set()
#     if tokens:
#         candidates.add(tokens[0])
#     if len(tokens) >= 2:
#         candidates.add(tokens[0] + tokens[1])
#     if len(tokens) > 1:
#         acronym = "".join(t[0] for t in tokens if t)
#         if len(acronym) >= 3:
#             candidates.add(acronym)
#     suffixes = [".com", ".law", ".law.com", ".org"]
#     for base in candidates:
#         for s in suffixes:
#             host = f"{base}{s}"
#             try:
#                 socket.gethostbyname(host)
#                 return f"https://{host}"
#             except Exception:
#                 continue
#     return None

# # --------------------------------------------------------------------
# def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
#     """Try to find JSON object in an arbitrary text and parse it."""
#     if not text:
#         return None
#     text = text.strip()
#     # direct load if pure JSON
#     try:
#         return json.loads(text)
#     except Exception:
#         pass

#     # search for first {...} block
#     m = re.search(r"(\{(?:.|\n)*\})", text)
#     if m:
#         candidate = m.group(1)
#         try:
#             return json.loads(candidate)
#         except Exception:
#             # attempt sanitized replacements (some LLMs use smart quotes)
#             candidate2 = candidate.replace("“", '"').replace("”", '"').replace("’", "'")
#             try:
#                 return json.loads(candidate2)
#             except Exception:
#                 return None
#     return None

# # --------------------------------------------------------------------
# def validate_choice_against_tokens(choice_url: str, firm_name: str, candidates: List[str]) -> str:
#     """Return a validated URL. If LLM's choice doesn't include any firm token,
#     fallback to best candidate that does; otherwise return original."""
#     if not choice_url:
#         return candidates[0] if candidates else ""
#     dom = domain_of(choice_url)
#     tokens = firm_tokens_from_name(firm_name)
#     if any(t in dom for t in tokens):
#         return choice_url
#     # fallback: pick top candidate that contains any token
#     for u in candidates:
#         if any(t in domain_of(u) for t in tokens):
#             return u
#     # final fallback -> return top candidate
#     return candidates[0] if candidates else choice_url

# # --------------------------------------------------------------------
# def llm_verify_best_site(firm_name: str, address: str, urls: List[str]) -> Dict[str, Any]:
#     """
#     Talk to Groq LLM and request strict JSON. Retry & sanitize.
#     If Groq not available or fails, fallback to best candidate by token.
#     """
#     result = {"best_url": urls[0] if urls else None, "reason": "fallback/no-llm"}
#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key or not GROQ_AVAILABLE:
#         logger.info("⚠️ GROQ_API_KEY missing or groq package not installed -> skipping LLM step.")
#         # validate with tokens
#         validated = validate_choice_against_tokens(result["best_url"], firm_name, urls)
#         result.update({"best_url": validated, "reason": "no-llm-fallback"})
#         return result

#     client = Groq(api_key=api_key)

#     system_prompt = (
#         "You are a strict JSON responder. The user gives you a firm name, address and a list of candidate URLs.\n"
#         "Return a single JSON object EXACTLY in this format (no surrounding text):\n"
#         '{ "best_url": "https://...", "reason": "short explanation (one line)" }\n'
#         "Rules:\n"
#         "- Choose the official law firm/company website (prefer domain matching firm name tokens).\n"
#         "- Avoid directories, profiles (linkedin, justia), listings, news or unrelated domains.\n"
#         "- If multiple candidate corporate domains exist prefer the one whose domain contains the firm's tokens.\n"
#         "- Output only the JSON object, nothing else."
#     )

#     user_prompt = (
#         f"Firm: {firm_name}\nAddress: {address}\nURLs: {json.dumps(urls, indent=2)}\n"
#         "Which is the official website? Reply only with the JSON object described."
#     )

#     # try up to 3 attempts
#     last_text = None
#     for attempt in range(1, 4):
#         try:
#             resp = client.chat.completions.create(
#                 model="llama-3.1-8b-instant",
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_prompt}
#                 ],
#                 temperature=0.0,
#                 max_tokens=300
#             )
#             # get model content
#             text = ""
#             try:
#                 text = resp.choices[0].message.content.strip()
#             except Exception:
#                 # older response shape or unexpected
#                 text = str(resp)

#             last_text = text
#             parsed = extract_json_from_text(text)
#             if parsed and isinstance(parsed, dict) and parsed.get("best_url"):
#                 # validate and return
#                 chosen = parsed.get("best_url")
#                 validated = validate_choice_against_tokens(chosen, firm_name, urls)
#                 parsed["best_url"] = validated
#                 parsed.setdefault("reason", parsed.get("reason", "llm_decision"))
#                 return parsed
#             else:
#                 logger.warning(f"⚠️ LLM output not valid JSON on attempt {attempt}. Raw output:\n{text[:1000]}\n")
#         except Exception as e:
#             logger.warning(f"⚠️ LLM call exception on attempt {attempt}: {e}")

#         # wait before retry
#         time.sleep(1 + attempt)
#     # All attempts failed -> fallback to token-based selection
#     logger.warning("⚠️ LLM failed to produce valid JSON after retries. Falling back to token-based selection.")
#     fallback = validate_choice_against_tokens(urls[0] if urls else None, firm_name, urls)
#     return {"best_url": fallback, "reason": "llm_failed_fallback", "llm_raw": (last_text or "")[:200]}

# # --------------------------------------------------------------------
# async def website_selector(firm_name: str, address: str = "") -> Dict[str, Any]:
#     direct = try_direct_domain(firm_name)
#     if direct:
#         logger.info(f"✅ Direct domain guess: {direct}")
#     else:
#         logger.info("⚠️ No direct domain guess resolved.")

#     query = f"{firm_name} {address} official website"
#     logger.info(f"\n🔍 Searching: {query}")
#     results = cached_search(query, max_results=20)
#     if not results:
#         logger.warning("No results returned from search.")
#         return {"direct_guess": direct, "top5": [], "llm_best": None, "reason": "no_results"}

#     top5 = pick_best_urls(firm_name, results, top_n=15)
#     logger.info("🔝 Top 5 website candidates:")
#     for i, (s, u) in enumerate(top5, 1):
#         logger.info(f"  {i}. {u} (score {s})")

#     candidate_urls = [u for _, u in top5]
#     llm_decision = llm_verify_best_site(firm_name, address, candidate_urls)
#     final = validate_choice_against_tokens(llm_decision.get("best_url"), firm_name, candidate_urls)
#     llm_decision["best_url"] = final

#     logger.info(f"\n🤖 LLM official site (after validation): {llm_decision['best_url']}")
#     logger.info(f"Reason: {llm_decision.get('reason')}\n")
#     return {
#         "direct_guess": direct,
#         "top5": top5,
#         "llm_best": llm_decision["best_url"],
#         "reason": llm_decision.get("reason"),
#         "llm_raw_preview": llm_decision.get("llm_raw", "") if "llm_raw" in llm_decision else ""
#     }

# # --------------------------------------------------------------------
# async def process_excel(path: str):
#     df = pd.read_excel(path)
#     logger.info(f"\nLoaded {len(df)} rows from Excel.")
#     out_rows = []
#     for i, row in df.iterrows():
#         firm_name = str(row.get("Representative") or "").strip()
#         address = str(row.get("Representative address") or "").strip()
#         if not firm_name:
#             logger.warning(f"[{i+1}] Skipping empty firm name.")
#             continue
#         logger.info(f"\n[{i+1}] 🔍 Searching for: {firm_name} | {address}")
#         res = await website_selector(firm_name, address)
#         # write top5 rows
#         top5 = res.get("top5") or []
#         for rank, (score, url) in enumerate(top5, start=1):
#             out_rows.append({
#                 "Representative": firm_name,
#                 "Address": address,
#                 "Rank": rank,
#                 "Score": score,
#                 "Candidate URL": url,
#                 "Direct Guess": res.get("direct_guess"),
#                 "LLM Official URL": res.get("llm_best"),
#                 "Selection Reason": res.get("reason"),
#                 "LLM Raw Preview": res.get("llm_raw_preview", "")
#             })
#         # if no top5, write a row with only LLM
#         if not top5:
#             out_rows.append({
#                 "Representative": firm_name,
#                 "Address": address,
#                 "Rank": None,
#                 "Score": None,
#                 "Candidate URL": None,
#                 "Direct Guess": res.get("direct_guess"),
#                 "LLM Official URL": res.get("llm_best"),
#                 "Selection Reason": res.get("reason"),
#                 "LLM Raw Preview": res.get("llm_raw_preview", "")
#             })

#     out_df = pd.DataFrame(out_rows)
#     out_path = "Website_Results_Final_v2.xlsx"
#     out_df.to_excel(out_path, index=False)
#     logger.info(f"\n✅ Saved to: {out_path}")

# # --------------------------------------------------------------------
# if __name__ == "__main__":
#     fp = input("\n📁 Enter Excel file path: ").strip()
#     if not os.path.exists(fp):
#         print("❌ File not found.")
#     else:
#         asyncio.run(process_excel(fp))



###################################almost 98%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%######################################

# #!/usr/bin/env python3
# """
# AI Firm Website Finder – v5.2 Stable
# ------------------------------------
# ✅ Fully async + multi-threaded
# ✅ Cleans dict artifacts (only URLs)
# ✅ Domain + Location filtering
# ✅ AI reasoning with 15 candidates
# ✅ Full justification + safe type handling
# """

# import os
# import re
# import json
# import asyncio
# import hashlib
# import logging
# from typing import List, Dict, Any

# import pandas as pd
# import requests
# from bs4 import BeautifulSoup
# from ddgs import DDGS
# from dotenv import load_dotenv

# try:
#     from groq import Groq
#     GROQ_AVAILABLE = True
# except Exception:
#     GROQ_AVAILABLE = False

# # --------------------------------------------------------------------
# load_dotenv()
# logging.basicConfig(level=logging.INFO, format="%(message)s")
# logger = logging.getLogger(__name__)

# CACHE_DIR = "search_cache_v5"
# os.makedirs(CACHE_DIR, exist_ok=True)
# ddgs = DDGS()
# API_KEY = os.getenv("GROQ_API_KEY")
# HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-FirmFinder/5.2)"}

# # --------------------------------------------------------------------
# def fetch_html(url: str, limit: int = 2000) -> str:
#     """Fetch simplified text from webpage."""
#     if not isinstance(url, str) or not url.startswith("http"):
#         return ""
#     try:
#         r = requests.get(url, headers=HEADERS, timeout=10)
#         if r.status_code < 400:
#             soup = BeautifulSoup(r.text, "html.parser")
#             text = soup.get_text(" ", strip=True)
#             return text[:limit]
#     except Exception:
#         pass
#     return ""

# def cached_search(query: str, max_results: int = 15) -> List[str]:
#     """Cached DuckDuckGo search (returns clean list of URLs)."""
#     key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
#     path = os.path.join(CACHE_DIR, f"{key}.json")
#     if os.path.exists(path):
#         try:
#             data = json.load(open(path, "r", encoding="utf-8"))
#             if isinstance(data, list):
#                 return [d["href"] if isinstance(d, dict) and "href" in d else d for d in data]
#         except Exception:
#             pass

#     results = list(ddgs.text(query, max_results=max_results))
#     urls = []
#     for r in results:
#         if isinstance(r, dict) and r.get("href"):
#             urls.append(r["href"])
#         elif isinstance(r, str):
#             urls.append(r)
#     json.dump(urls, open(path, "w", encoding="utf-8"), indent=2)
#     return urls

# def extract_json(text: str) -> Dict[str, Any]:
#     """Extract JSON from AI response."""
#     if not text:
#         return {}
#     m = re.search(r"\{.*\}", text, re.S)
#     if not m:
#         return {}
#     try:
#         return json.loads(
#             m.group(0).replace("True", "true").replace("False", "false")
#         )
#     except Exception:
#         return {}

# # --------------------------------------------------------------------
# def normalize_urls(urls: List[Any]) -> List[str]:
#     """Ensure all URLs are strings (not dicts)."""
#     clean = []
#     for u in urls:
#         if isinstance(u, dict) and "href" in u:
#             clean.append(u["href"])
#         elif isinstance(u, str):
#             clean.append(u)
#     return list(dict.fromkeys(clean))  # remove duplicates

# def filter_by_domain_and_location(firm: str, address: str, urls: List[str]) -> List[str]:
#     """Keep URLs matching firm name tokens or location."""
#     urls = normalize_urls(urls)
#     tokens = [t for t in re.split(r"[^a-z]", firm.lower()) if len(t) > 2]
#     city_tokens = [t for t in re.split(r"[^a-z]", address.lower()) if len(t) > 2]

#     filtered = []
#     for u in urls:
#         if not isinstance(u, str):
#             continue
#         d = re.sub(r"https?://(www\.)?", "", u.lower()).split("/")[0]
#         if any(t in d for t in tokens):
#             filtered.append(u)
#             continue
#         if any(t in u.lower() for t in city_tokens):
#             filtered.append(u)

#     if len(filtered) < 10:
#         filtered = urls[:15]
#     return filtered[:15]

# # --------------------------------------------------------------------
# def ai_chat(prompt: str) -> str:
#     """Send prompt to Groq model."""
#     if not GROQ_AVAILABLE or not API_KEY:
#         return ""
#     try:
#         client = Groq(api_key=API_KEY)
#         resp = client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1,
#             max_tokens=1000,
#         )
#         return resp.choices[0].message.content.strip()
#     except Exception as e:
#         logger.warning(f"⚠️ AI error: {e}")
#         return ""

# # --------------------------------------------------------------------
# def ai_select_best_site(firm: str, address: str, candidates: List[str]) -> Dict[str, Any]:
#     """AI reasoning to select official site and explain why."""
#     candidates = normalize_urls(candidates)
#     snippets = {}
#     for u in candidates:
#         snippets[u] = fetch_html(u)
#     candidates = [u for u in candidates if snippets.get(u)]

#     if not candidates:
#         return {"best_url": None, "confidence": 0, "reason": "no_content"}

#     joined = "\n\n".join(
#         f"URL: {u}\nTEXT:\n{snippets[u][:1000]}"
#         for u in candidates
#     )

#     prompt = f"""
# You are a digital investigator identifying the *official website* of a firm.

# Firm: {firm}
# Address: {address}

# Below are 15 candidate URLs with their page text:
# {joined}

# Your task:
# - Identify which URL is the firm's official website (main corporate domain or homepage).
# - Consider firm name, domain match, address/location mentions.
# - Ignore LinkedIn, Wikipedia, directories, or unrelated sites.

# Return STRICT JSON:
# {{
#   "best_url": "https://...",
#   "confidence": 0–1,
#   "reason": "Why this is official (short).",
#   "summary": "Brief explanation comparing chosen URL with others (why others are less likely)."
# }}
# """

#     text = ai_chat(prompt)
#     data = extract_json(text)
#     if not data:
#         for u in candidates:
#             if re.search(rf"{re.escape(firm.split()[0].lower())}", u.lower()):
#                 return {"best_url": u, "confidence": 0.6, "reason": "token fallback", "summary": ""}
#         return {"best_url": candidates[0], "confidence": 0.5, "reason": "fallback", "summary": ""}
#     return data

# # --------------------------------------------------------------------
# async def website_selector(firm: str, address: str) -> Dict[str, Any]:
#     query = f"{firm} {address} official website"
#     logger.info(f"\n🔍 Searching: {query}")
#     urls = cached_search(query, 20)
#     if not urls:
#         return {"best_url": None, "reason": "no_candidates"}

#     urls = filter_by_domain_and_location(firm, address, urls)
#     logger.info(f"Found {len(urls)} filtered candidates.")

#     result = ai_select_best_site(firm, address, urls)
#     logger.info(f"✅ AI Selected: {result.get('best_url')}")
#     logger.info(f"Reason: {result.get('reason')}\n")
#     return result

# # --------------------------------------------------------------------
# async def process_excel(path: str, concurrent_tasks: int = 5):
#     df = pd.read_excel(path)
#     out_rows = []

#     async def handle_row(i, row):
#         firm = str(row.get("Representative") or "").strip()
#         address = str(row.get("Representative address") or "").strip()
#         if not firm:
#             return None
#         res = await website_selector(firm, address)
#         return {
#             "Firm": firm,
#             "Address": address,
#             "Official Website": res.get("best_url"),
#             "Confidence": res.get("confidence", ""),
#             "Reason": res.get("reason", ""),
#             "AI Summary": res.get("summary", ""),
#         }

#     sem = asyncio.Semaphore(concurrent_tasks)
#     tasks = [bounded_task(i, row, sem, handle_row) for i, row in df.iterrows()]
#     results = await asyncio.gather(*tasks)
#     out_rows = [r for r in results if r]

#     out_df = pd.DataFrame(out_rows)
#     out_path = "Website_Results_AI_v5.2.xlsx"
#     out_df.to_excel(out_path, index=False)
#     logger.info(f"\n✅ Saved to: {out_path}")

# async def bounded_task(i, row, sem, handler):
#     async with sem:
#         return await handler(i, row)

# # --------------------------------------------------------------------
# if __name__ == "__main__":
#     fp = input("\n📁 Enter Excel file path: ").strip()
#     if not os.path.exists(fp):
#         print("❌ File not found.")
#     else:
#         asyncio.run(process_excel(fp))



##################################100%####################################################################
#!/usr/bin/env python3
"""
AI Firm Website Finder – v5.3 (Debug Ready)
-------------------------------------------
✅ Async + multi-threaded
✅ Dict-safe DDG search results
✅ Domain + location filters
✅ AI reasoning + justification
✅ Optional debug mode to save full logs
"""

import os
import re
import json
import asyncio
import hashlib
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

# --------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

CACHE_DIR = "search_cache_v5"
DEBUG_DIR = "debug_logs"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

ddgs = DDGS()
API_KEY = os.getenv("GROQ_API_KEY")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AI-FirmFinder/5.3)"}

# --------------------------------------------------------------------
def fetch_html(url: str, limit: int = 2000) -> str:
    if not isinstance(url, str) or not url.startswith("http"):
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code < 400:
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            return text[:limit]
    except Exception:
        pass
    return ""

def cached_search(query: str, max_results: int = 15) -> List[str]:
    key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
            if isinstance(data, list):
                return [d["href"] if isinstance(d, dict) and "href" in d else d for d in data]
        except Exception:
            pass
    results = list(ddgs.text(query, max_results=max_results))
    urls = []
    for r in results:
        if isinstance(r, dict) and r.get("href"):
            urls.append(r["href"])
        elif isinstance(r, str):
            urls.append(r)
    json.dump(urls, open(path, "w", encoding="utf-8"), indent=2)
    return urls

def extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        return json.loads(
            m.group(0).replace("True", "true").replace("False", "false")
        )
    except Exception:
        return {}

def normalize_urls(urls: List[Any]) -> List[str]:
    clean = []
    for u in urls:
        if isinstance(u, dict) and "href" in u:
            clean.append(u["href"])
        elif isinstance(u, str):
            clean.append(u)
    return list(dict.fromkeys(clean))

def filter_by_domain_and_location(firm: str, address: str, urls: List[str]) -> List[str]:
    urls = normalize_urls(urls)
    tokens = [t for t in re.split(r"[^a-z]", firm.lower()) if len(t) > 2]
    city_tokens = [t for t in re.split(r"[^a-z]", address.lower()) if len(t) > 2]

    filtered = []
    for u in urls:
        if not isinstance(u, str):
            continue
        d = re.sub(r"https?://(www\.)?", "", u.lower()).split("/")[0]
        if any(t in d for t in tokens) or any(t in u.lower() for t in city_tokens):
            filtered.append(u)

    if len(filtered) < 10:
        filtered = urls[:15]
    return filtered[:15]

# --------------------------------------------------------------------
def ai_chat(prompt: str) -> str:
    if not GROQ_AVAILABLE or not API_KEY:
        return ""
    try:
        client = Groq(api_key=API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"⚠️ AI error: {e}")
        return ""

# --------------------------------------------------------------------
def ai_select_best_site(firm: str, address: str, candidates: List[str], debug: bool=False) -> Dict[str, Any]:
    candidates = normalize_urls(candidates)
    snippets = {}
    for u in candidates:
        snippets[u] = fetch_html(u)
    candidates = [u for u in candidates if snippets.get(u)]

    if not candidates:
        return {"best_url": None, "confidence": 0, "reason": "no_content"}

    joined = "\n\n".join(
        f"URL: {u}\nTEXT:\n{snippets[u][:1000]}"
        for u in candidates
    )

    prompt = f"""
You are a digital investigator identifying the *official website* of a firm.

Firm: {firm}
Address: {address}

Below are 15 candidate URLs with their page text:
{joined}

Your task:
- Identify which URL is the firm's official website (main corporate domain or homepage).
- Consider firm name, domain match, and address/location mentions.
- Ignore LinkedIn, Wikipedia, directories, or unrelated sites.

Return STRICT JSON:
{{
  "best_url": "https://...",
  "confidence": 0–1,
  "reason": "Why this is official (short).",
  "summary": "Brief explanation comparing chosen URL with others (why others are less likely)."
}}
"""

    text = ai_chat(prompt)
    data = extract_json(text)
    if not data:
        for u in candidates:
            if re.search(rf"{re.escape(firm.split()[0].lower())}", u.lower()):
                data = {"best_url": u, "confidence": 0.6, "reason": "token fallback", "summary": ""}
                break
        else:
            data = {"best_url": candidates[0], "confidence": 0.5, "reason": "fallback", "summary": ""}

    # Save debug info if requested
    if debug:
        debug_log = {
            "timestamp": datetime.now().isoformat(),
            "firm": firm,
            "address": address,
            "candidates": candidates,
            "snippets": {u: snippets[u][:400] for u in candidates},
            "ai_output": data,
            "raw_ai_text": text,
        }
        with open(os.path.join(DEBUG_DIR, "debug_logs.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(debug_log, ensure_ascii=False) + "\n")

    return data

# --------------------------------------------------------------------
async def website_selector(firm: str, address: str, debug: bool=False) -> Dict[str, Any]:
    query = f"{firm} {address} official website"
    logger.info(f"\n🔍 Searching: {query}")
    urls = cached_search(query, 20)
    if not urls:
        return {"best_url": None, "reason": "no_candidates"}

    urls = filter_by_domain_and_location(firm, address, urls)
    logger.info(f"Found {len(urls)} filtered candidates.")

    result = ai_select_best_site(firm, address, urls, debug)
    logger.info(f"✅ AI Selected: {result.get('best_url')}")
    logger.info(f"Reason: {result.get('reason')}\n")
    return result

# --------------------------------------------------------------------
async def process_excel(path: str, concurrent_tasks: int = 5, debug: bool=False):
    df = pd.read_excel(path)
    out_rows = []

    async def handle_row(i, row):
        firm = str(row.get("Representative") or "").strip()
        address = str(row.get("Representative address") or "").strip()
        if not firm:
            return None
        res = await website_selector(firm, address, debug)
        return {
            "Firm": firm,
            "Address": address,
            "Official Website": res.get("best_url"),
            "Confidence": res.get("confidence", ""),
            "Reason": res.get("reason", ""),
            "AI Summary": res.get("summary", ""),
        }

    sem = asyncio.Semaphore(concurrent_tasks)
    async def bounded_task(i, row):
        async with sem:
            return await handle_row(i, row)

    tasks = [bounded_task(i, row) for i, row in df.iterrows()]
    results = await asyncio.gather(*tasks)
    out_rows = [r for r in results if r]

    out_df = pd.DataFrame(out_rows)
    out_path = "Website_Results_AI_v5.3.xlsx"
    out_df.to_excel(out_path, index=False)
    logger.info(f"\n✅ Saved to: {out_path}")
    if debug:
        logger.info(f"🐞 Debug logs written to: {DEBUG_DIR}/debug_logs.jsonl")



# --------------------------------------------------------------------
def find_official_website(firm: str, address: str, debug: bool = False) -> Dict[str, Any]:
    """
    Public API wrapper to allow main.py to call website_finder_ai as a module.
    Handles caching, filtering, and AI scoring synchronously.
    """
    try:
        urls = cached_search(f"{firm} {address} official website", 20)
        if not urls:
            return {"best_url": None, "reason": "no_candidates"}

        urls = filter_by_domain_and_location(firm, address, urls)
        result = ai_select_best_site(firm, address, urls, debug)
        return {
            "best_url": result.get("best_url"),
            "confidence": result.get("confidence", 0),
            "reason": result.get("reason", ""),
            "summary": result.get("summary", "")
        }
    except Exception as e:
        logger.error(f"Website finder failed for {firm}: {e}")
        return {"best_url": None, "reason": str(e), "confidence": 0}


# --------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (saves all AI reasoning)")
    args = parser.parse_args()

    fp = input("\n📁 Enter Excel file path: ").strip()
    if not os.path.exists(fp):
        print("❌ File not found.")
    else:
        asyncio.run(process_excel(fp, debug=args.debug))
