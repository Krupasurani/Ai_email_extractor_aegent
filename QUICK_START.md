# 🚀 QUICK START GUIDE

## Complete Email Extraction System

---

## ✅ Setup (One Time)

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Add your API key to .env
echo "GROQ_API_KEY=your_api_key_here" > .env
```

---

## 🎯 How to Run the COMPLETE System

### **Option 1: Single Person (Recommended)**

Just provide company name and person name - the system finds everything automatically!

```bash
python complete_email_extractor.py "Sullivan & Cromwell" "Robert Giuffra"
```

**With location for better results:**
```bash
python complete_email_extractor.py "DLA Piper" "New York" "John Smith"
```

**What it does:**
1. 🔍 Finds the official website automatically
2. 📋 Locates the people/attorneys directory
3. 🎯 Extracts the person's email
4. ✅ Returns email + profile URL

---

### **Option 2: Batch Processing (Multiple People)**

Create a CSV file:

**`my_list.csv`:**
```csv
firm_name,address,person_name
Sullivan & Cromwell,New York,Robert Giuffra
DLA Piper,Chicago,John Smith
Skadden,Boston,Jane Doe
```

Run batch:
```bash
python batch_complete_extractor.py my_list.csv
```

**Outputs:**
- `batch_complete_results.csv` - All results in CSV
- `batch_complete_results.json` - All results in JSON

---

### **Option 3: When You Already Have the URL**

If you know the people directory URL:

```bash
python universal_email_agent_v5.py "https://www.sullcrom.com/lawyers" "Robert Giuffra"
```

---

## 📊 What You Get

### **Single Extraction:**
```
✅ PIPELINE SUCCESS
📧 Email: robert.giuffra@sullcrom.com
ℹ️ Profile: https://www.sullcrom.com/lawyers/robert-giuffra
ℹ️ Confidence: 95
```

### **Batch Results CSV:**
| firm_name | person_name | email | confidence |
|-----------|-------------|-------|------------|
| Sullivan & Cromwell | Robert Giuffra | robert.giuffra@sullcrom.com | 95 |
| DLA Piper | John Smith | john.smith@dlapiper.com | 87 |

---

## 🎬 Complete Example

```bash
# 1. Create test input
cat > test.csv << 'EOF'
firm_name,address,person_name
Sullivan & Cromwell,New York,Robert Giuffra
DLA Piper,Chicago,John Smith
Skadden,Boston,Jane Doe
EOF

# 2. Run batch extraction
python batch_complete_extractor.py test.csv

# 3. View results
cat batch_complete_results.csv
```

---

## 🔧 Common Commands

```bash
# Test single extraction
python complete_email_extractor.py "Firm Name" "Person Name"

# Run batch
python batch_complete_extractor.py input.csv

# Check if setup is correct
python complete_email_extractor.py --help

# View results
cat batch_complete_results.csv
```

---

## ⚡ The Complete Flow

```
You provide:
  Company Name: "Sullivan & Cromwell"
  Person Name: "Robert Giuffra"

System automatically:
  1. 🔍 Searches Google/DuckDuckGo for company website
  2. 🤖 Uses AI to pick the official website
  3. 🌐 Finds the people/attorneys directory page
  4. 🎭 Opens page with real browser (Playwright)
  5. ❌ Dismisses cookie popups
  6. 🔎 Finds the search input using AI
  7. ⌨️ Types the person's name
  8. 📋 Analyzes search results
  9. 🔗 Visits candidate profile pages
  10. ✅ Verifies correct person using AI
  11. 📧 Extracts email address
  12. ✔️ Validates email domain

You get:
  📧 Email: robert.giuffra@sullcrom.com
  🔗 Profile: https://www.sullcrom.com/lawyers/robert-giuffra
  📊 Confidence: 95%
```

---

## 🐛 Troubleshooting

**Problem: "No GROQ_API_KEY"**
```bash
# Solution: Add to .env file
echo "GROQ_API_KEY=your_key_here" > .env
```

**Problem: "Playwright not installed"**
```bash
playwright install chromium
```

**Problem: "Module not found"**
```bash
pip install -r requirements.txt
```

---

## 📖 Need More Help?

See `USAGE_GUIDE.md` for detailed documentation!

---

**That's it! You're ready to extract emails! 🎉**
