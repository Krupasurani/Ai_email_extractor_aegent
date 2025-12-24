# Complete Email Extraction System - Usage Guide

## 🎯 Overview

This system provides **end-to-end email extraction** from company/firm names:

1. **Input**: Company name + Person name
2. **Step 1**: Find official website URL automatically
3. **Step 2**: Extract person's email from the website
4. **Output**: Email address with confidence score

---

## 📦 Installation

### 1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set up API key in `.env`:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

---

## 🚀 Usage Methods

### **Method 1: Single Person Extraction (Complete Pipeline)**

Extract email when you only know the company and person name:

```bash
python complete_email_extractor.py "Sullivan & Cromwell" "Robert Giuffra"
```

With address for better website finding:
```bash
python complete_email_extractor.py "DLA Piper" "New York" "John Smith"
```

**Output:**
```
🚀 COMPLETE EMAIL EXTRACTION PIPELINE
======================================================================
ℹ️ Firm: Sullivan & Cromwell
ℹ️ Person: Robert Giuffra

📍 STEP 1: Finding official website for 'Sullivan & Cromwell'
🔍 Searching: Sullivan & Cromwell official website
🎯 Website found: https://www.sullcrom.com
🎯 People directory: https://www.sullcrom.com/lawyers

📍 STEP 2: Extracting email for 'Robert Giuffra' from website
[START] Universal Email Agent v5
[INFO] Target: Robert Giuffra
...
[SUCCESS] Email: robert.giuffra@sullcrom.com

======================================================================
✅ PIPELINE SUCCESS
======================================================================
📧 Email: robert.giuffra@sullcrom.com
ℹ️ Profile: https://www.sullcrom.com/lawyers/robert-giuffra
ℹ️ Confidence: 95
```

---

### **Method 2: Batch Processing (CSV Input)**

Process multiple companies/people from a CSV file:

#### Create input CSV (`input.csv`):
```csv
firm_name,address,person_name
Sullivan & Cromwell,New York,Robert Giuffra
DLA Piper,Chicago,John Smith
Skadden,Boston,Jane Doe
```

#### Run batch processing:
```bash
python batch_complete_extractor.py input.csv
```

**Output:**
- `batch_complete_results.csv` - CSV with all results
- `batch_complete_results.json` - JSON with all results
- Individual JSON files for each extraction

---

### **Method 3: Direct URL Extraction (When You Know the URL)**

If you already have the people directory URL:

```bash
python universal_email_agent_v5.py "https://www.sullcrom.com/lawyers" "Robert Giuffra"
```

Batch processing with known URLs:
```bash
# Create input.txt with: url,person_name
python batch_email.py input.txt
```

---

## 📊 Output Formats

### **Single Extraction JSON:**
```json
{
  "status": "success",
  "firm": "Sullivan & Cromwell",
  "person": "Robert Giuffra",
  "email": "robert.giuffra@sullcrom.com",
  "profile_url": "https://www.sullcrom.com/lawyers/robert-giuffra",
  "confidence": 95,
  "is_general_contact": false,
  "website_url": "https://www.sullcrom.com/lawyers"
}
```

### **Batch Results CSV:**
```csv
timestamp,firm_name,address,person_name,status,email,profile_url,website_url,confidence,is_general_contact,runtime_sec,error
2024-12-23 10:30:00,Sullivan & Cromwell,New York,Robert Giuffra,success,robert.giuffra@sullcrom.com,https://...,https://...,95,false,45.2,
```

---

## 🔧 Configuration

### **Batch Processing Settings**

Edit `batch_complete_extractor.py`:
```python
MAX_WORKERS = 2        # Parallel extractions (1-3 recommended)
TIMEOUT = 180          # Timeout per case (seconds)
OUTPUT_CSV = "results.csv"
```

### **Email Agent Settings**

Edit `universal_email_agent_v5.py`:
```python
HEADLESS: bool = True   # Set False to see browser (debugging)
MIN_CONFIDENCE: int = 65  # Minimum confidence threshold
PAGE_TIMEOUT: int = 60000  # Page load timeout (ms)
```

---

## 📁 File Structure

```
Ai_email_extractor_aegent/
├── complete_email_extractor.py      # Single complete pipeline
├── batch_complete_extractor.py      # Batch complete pipeline
├── universal_email_agent_v5.py      # Email extraction only
├── website_finder_ai.py             # Website finding only
├── batch_email.py                   # Batch email extraction (URL input)
├── example_input.csv                # Example CSV input
├── requirements.txt                 # Dependencies
└── .env                             # API keys
```

---

## 🎬 Quick Start Examples

### Example 1: Law Firm Partner
```bash
python complete_email_extractor.py "Skadden Arps" "New York" "John Doe"
```

### Example 2: Company Employee
```bash
python complete_email_extractor.py "Microsoft" "Satya Nadella"
```

### Example 3: Batch Processing
```bash
# Create test.csv
cat > test.csv << 'EOF'
firm_name,address,person_name
Sullivan & Cromwell,New York,Robert Giuffra
DLA Piper,Chicago,John Smith
EOF

# Run batch
python batch_complete_extractor.py test.csv
```

---

## 🐛 Troubleshooting

### **"No GROQ_API_KEY" error:**
```bash
# Check .env file
cat .env

# Or set temporarily
export GROQ_API_KEY="your_key_here"
```

### **Playwright browser fails:**
```bash
playwright install chromium
```

### **Timeout issues:**
- Increase `TIMEOUT` in batch scripts
- Reduce `MAX_WORKERS` to 1

### **Website not found:**
- Add more specific address/location
- Check if company name is correct
- Try with official website URL directly

### **Email not found:**
- Person might not have public email
- Name spelling might be different
- Check if general contact email was found instead

---

## 📈 Performance Tips

1. **Use specific addresses** for better website finding
2. **Run 2-3 workers max** to avoid rate limiting
3. **Check cache folders** (`search_cache_v5/`) for repeated searches
4. **Enable debug mode** for troubleshooting specific cases

---

## 🔍 How It Works

### **Complete Pipeline Flow:**

```
Input: Firm Name + Person Name
    ↓
1. Search DuckDuckGo for official website
    ↓
2. Use AI to select best candidate URL
    ↓
3. Find people/attorneys directory page
    ↓
4. Load page with Playwright
    ↓
5. Handle popups/cookies
    ↓
6. Find search input using AI
    ↓
7. Search for person's name
    ↓
8. Analyze search results (pattern + AI)
    ↓
9. Visit candidate profile pages
    ↓
10. Verify person match using AI
    ↓
11. Extract and validate email
    ↓
12. Fallback to contact page if needed
    ↓
Output: Email address
```

---

## 📝 Notes

- **General Contact Emails**: If personal email not found, system falls back to firm's general contact email
- **Confidence Score**: 65-100 = Good match, 50-64 = Uncertain match
- **Rate Limiting**: System includes delays to avoid being blocked
- **Caching**: Search results are cached to speed up repeated queries

---

## 🆘 Support

For issues or questions, check:
1. Log output for detailed error messages
2. Debug logs in `debug_logs/` folder
3. Individual result JSON files for specific cases

---

**Happy Email Hunting! 🎯📧**
