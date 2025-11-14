# NormScout Norms Database Guide

This guide explains how to add, modify, and understand the norms database used by NormScout's compliance analysis system.

## Table of Contents
- [Overview](#overview)
- [Norms Database Structure](#norms-database-structure)
- [Adding New Norms](#adding-new-norms)
- [Updating Existing Norms](#updating-existing-norms)
- [Finding Official Norm URLs](#finding-official-norm-urls)
- [How the Analysis Works](#how-the-analysis-works)
- [Testing Your Changes](#testing-your-changes)

---

## Overview

NormScout uses a centralized JSON database (`data/norms.json`) containing 68+ EU compliance norms, directives, and standards. When a user describes a product, the system checks each norm in parallel using AI to determine applicability and confidence scores.

**Key Files:**
- `data/norms.json` - The norms database
- `services/norm_matcher.py` - Analysis engine
- `services/product_conversation.py` - Product description gathering
- `templates/develope.html` - Main analysis UI
- `templates/workspace.html` - Persistent workspace UI

---

## Norms Database Structure

Each norm in `data/norms.json` has the following fields:

```json
{
  "id": "EN 62368-1",
  "name": "Audio/Video, ICT and Communication Technology Equipment - Safety",
  "category": "General Product Safety",
  "applies_to": "IT equipment, AV equipment, communication equipment",
  "description": "Modern hazard-based safety standard replacing EN 60950-1...",
  "url": "https://www.en-standard.eu/EN-62368-1"
}
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ Yes | Unique identifier (e.g., `DIR-2014/35/EU`, `EN 62368-1`) |
| `name` | ✅ Yes | Human-readable name of the norm |
| `category` | ✅ Yes | Category grouping (see categories below) |
| `applies_to` | ✅ Yes | Brief description of applicable products |
| `description` | ✅ Yes | Detailed explanation of what the norm covers |
| `url` | ✅ Yes | Link to official documentation |

### Categories

Current categories in the database:

- **Horizontal Standards** - Apply to many/most products (LVD, EMC, RoHS, WEEE)
- **General Product Safety** - Broad safety standards
- **ICT & Electronics** - IT equipment, wireless, RF
- **Machinery & Automated Equipment** - Machinery directive, robotics
- **Household & Consumer Products** - Appliances, toys
- **Medical & Healthcare** - Medical devices
- **Lighting & Optics** - Lighting equipment, lasers
- **Power & Energy** - Batteries, power supplies
- **Automotive & Mobility** - Vehicles, e-bikes
- **Industrial & Hazardous** - ATEX, pressure equipment
- **Environmental & Efficiency** - Ecodesign, energy labelling
- **Materials & Packaging** - Material restrictions, packaging

---

## Adding New Norms

### Step 1: Research the Norm

Before adding a norm, verify:
1. **It's mandatory** - Not all standards are required for CE marking
2. **It's current** - Check if it's been replaced/updated
3. **It's EU-applicable** - Must apply to EU market
4. **Official URL exists** - Find the EUR-Lex or official source

### Step 2: Add to norms.json

Open `data/norms.json` and add your norm to the `"norms"` array:

```json
{
  "id": "EN 55032",
  "name": "Electromagnetic compatibility of multimedia equipment - Emission requirements",
  "category": "ICT & Electronics",
  "applies_to": "Multimedia equipment (computers, monitors, printers)",
  "description": "Specifies emission requirements for multimedia equipment in the frequency range 9 kHz to 400 GHz. Replaces EN 55013 and EN 55022.",
  "url": "https://www.en-standard.eu/EN-55032"
}
```

### Step 3: ID Naming Conventions

Follow these patterns for consistency:

| Type | Pattern | Example |
|------|---------|---------|
| EU Directive | `DIR-YYYY/NN/EU` | `DIR-2014/35/EU` |
| EU Regulation | `REG-YYYY/NNNN` | `REG-2023/1542` |
| EN Standard | `EN NNNNN-N` | `EN 62368-1` |
| EN-IEC Standard | `EN-IEC NNNNN` | `EN-IEC 63000` |
| IEC Standard | `IEC NNNNN-N` | `IEC 60601-1` |

### Step 4: Test the Addition

```bash
# 1. Verify JSON is valid
python -c "import json; json.load(open('data/norms.json'))"

# 2. Check norm count
python -c "import json; data=json.load(open('data/norms.json')); print(f'Total norms: {len(data[\"norms\"])}')"

# 3. Find your norm
python -c "import json; data=json.load(open('data/norms.json')); norm=[n for n in data['norms'] if 'EN 55032' in n['id']]; print(norm)"
```

### Step 5: Restart the Server

The norms database is loaded on server startup:

```bash
# Local testing
python app.py

# Production deployment
fly deploy
```

---

## Updating Existing Norms

### Common Updates

**Update a norm URL:**
```python
# Find and update
import json
with open('data/norms.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)
    for norm in data['norms']:
        if norm['id'] == 'EN 62368-1':
            norm['url'] = 'https://new-url.com'
    f.seek(0)
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.truncate()
```

**Update description/applies_to:**
```json
{
  "id": "DIR-2014/35/EU",
  "applies_to": "All electrical equipment 50-1000V AC or 75-1500V DC",
  "description": "Updated description with new requirements..."
}
```

**Replace obsolete norm:**
```json
// Old norm (mark as obsolete in description)
{
  "id": "EN 60950-1",
  "description": "OBSOLETE: Replaced by EN 62368-1 as of December 2020. Safety standard for IT equipment..."
}

// Add replacement
{
  "id": "EN 62368-1",
  "description": "Replaces EN 60950-1. Modern hazard-based safety standard..."
}
```

---

## Finding Official Norm URLs

### EU Directives & Regulations

**EUR-Lex** (Official EU Law Database):
```
https://eur-lex.europa.eu/
```

**URL Pattern:**
- Directives: `https://eur-lex.europa.eu/eli/dir/YYYY/NN/oj`
- Regulations: `https://eur-lex.europa.eu/eli/reg/YYYY/NNNN/oj`

**Example:**
- `DIR-2014/35/EU` → `https://eur-lex.europa.eu/eli/dir/2014/35/oj`
- `REG-2023/1542` → `https://eur-lex.europa.eu/eli/reg/2023/1542/oj`

### EN Standards

**Official Sources:**
1. **CEN (European Committee for Standardization)** - https://www.cen.eu
2. **CENELEC (Electrotechnical)** - https://www.cenelec.eu
3. **Your National Standards Body:**
   - Germany: DIN (https://www.din.de)
   - UK: BSI (https://www.bsigroup.com)
   - France: AFNOR (https://www.afnor.org)

**Note:** EN standards are copyrighted and must be purchased. Use placeholder URLs like:
```
https://www.en-standard.eu/EN-62368-1
```

You can link to official previews or summaries instead of full documents.

### Harmonized Standards Database

Check if a standard is harmonized (grants presumption of conformity):
```
https://single-market-economy.ec.europa.eu/single-market/european-standards/harmonised-standards_en
```

---

## How the Analysis Works

### Workflow Overview

```
1. User describes product → gather_product_info()
   ↓
2. AI asks follow-up questions → build_product_summary()
   ↓
3. Technical description created
   ↓
4. Load all 68 norms from norms.json
   ↓
5. For each norm in parallel (10 workers):
   - Call check_norm_applies(norm, product_description)
   - LLM returns: APPLIES (yes/no), CONFIDENCE (0-100), REASONING
   ↓
6. Filter norms with confidence > 50%
   ↓
7. Display results with clickable links
```

### AI Prompt (norm_matcher.py)

Each norm is checked with this prompt:

```python
f"""Analyze if this EU compliance norm applies to the product.

NORM:
ID: {norm['id']}
Name: {norm['name']}
Applies to: {norm['applies_to']}
Description: {norm['description']}

PRODUCT:
{product_description}

Respond in this format:
APPLIES: yes/no
CONFIDENCE: 0-100
REASONING: [brief explanation]"""
```

### Confidence Scoring

| Score | Meaning | Badge Color |
|-------|---------|-------------|
| 80-100% | Highly likely to apply | Green (high) |
| 60-79% | Likely to apply | Yellow (medium) |
| 50-59% | Possibly applies | Orange (medium) |
| 0-49% | Does not apply | Not shown |

### Returned Data Structure

```python
{
  "norm_id": "EN 62368-1",
  "norm_name": "Audio/Video, ICT...",
  "applies": True,
  "confidence": 95,
  "reasoning": "Product is USB-powered LED lamp classified as IT equipment...",
  "url": "https://www.en-standard.eu/EN-62368-1"
}
```

---

## Testing Your Changes

### 1. JSON Validation

```bash
# Check syntax
python -c "import json; json.load(open('data/norms.json'))" && echo "✓ Valid JSON"

# Pretty print
python -c "import json; print(json.dumps(json.load(open('data/norms.json')), indent=2))" | less
```

### 2. Test with Real Product

1. Start local server:
   ```bash
   python app.py
   ```

2. Navigate to `http://192.168.76.251:8080/develope`

3. Describe a test product:
   ```
   USB-C powered LED desk lamp, 5V 3A input, adjustable brightness,
   plastic housing, for office use
   ```

4. Run analysis and verify:
   - Your new norm appears (if applicable)
   - Confidence score is reasonable
   - URL link works when clicked
   - Reasoning makes sense

### 3. Check Specific Norm

```python
import json
from services.norm_loader import load_norms
from services.norm_matcher import check_norm_applies

# Load norms
norms = load_norms()

# Find specific norm
norm = next(n for n in norms if n['id'] == 'EN 62368-1')

# Test against product
product = "USB-powered LED desk lamp"
result = check_norm_applies(norm, product)

print(f"Applies: {result['applies']}")
print(f"Confidence: {result['confidence']}%")
print(f"Reasoning: {result['reasoning']}")
print(f"URL: {result['url']}")
```

### 4. Performance Test

```python
# Time analysis for 68 norms
import time
from services.norm_matcher import match_norms_streaming

product = "USB-C powered LED desk lamp, 5V 3A"

start = time.time()
for event_type, *data in match_norms_streaming(product):
    if event_type == 'complete':
        matched, all_results = data
        elapsed = time.time() - start
        print(f"✓ Analyzed {len(all_results)} norms in {elapsed:.1f}s")
        print(f"  Matched: {len(matched)}")
```

Expected: ~30-60 seconds for 68 norms (parallel processing with 10 workers)

---

## Common Scenarios

### Scenario 1: EU Updates a Directive

```json
// 1. Mark old directive as updated
{
  "id": "DIR-2014/35/EU",
  "description": "UPDATED: See Amendment (EU) 2024/XXX. Original LVD requirements..."
}

// 2. Add amendment as new norm
{
  "id": "DIR-2024/XXX/EU",
  "name": "Amendment to Low Voltage Directive",
  "category": "Horizontal Standards",
  "applies_to": "All electrical equipment (amendment)",
  "description": "Updates LVD with new safety requirements for...",
  "url": "https://eur-lex.europa.eu/eli/dir/2024/XXX/oj"
}
```

### Scenario 2: Standard Gets Replaced

```python
# Update script
import json

with open('data/norms.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)

    # Find old standard
    for norm in data['norms']:
        if norm['id'] == 'EN 60950-1':
            norm['description'] = f"OBSOLETE (Dec 2020): Replaced by EN 62368-1. {norm['description']}"
            norm['applies_to'] = "IT equipment (LEGACY - use EN 62368-1)"

    # Ensure replacement exists
    if not any(n['id'] == 'EN 62368-1' for n in data['norms']):
        data['norms'].append({
            "id": "EN 62368-1",
            "name": "Audio/Video, ICT and Communication Technology Equipment - Safety",
            "category": "General Product Safety",
            "applies_to": "IT equipment, AV equipment, communication equipment",
            "description": "Replaces EN 60950-1 (obsolete Dec 2020). Modern hazard-based safety standard...",
            "url": "https://www.en-standard.eu/EN-62368-1"
        })

    f.seek(0)
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.truncate()
```

### Scenario 3: Add Product-Specific Standard

```json
{
  "id": "EN 60598-1",
  "name": "Luminaires - General Requirements and Tests",
  "category": "Lighting & Optics",
  "applies_to": "All luminaires (lighting fixtures)",
  "description": "Safety requirements for luminaires including electrical, mechanical, thermal, and photobiological hazards. Covers LED, incandescent, fluorescent lighting.",
  "url": "https://www.en-standard.eu/EN-60598-1"
}
```

---

## Advanced: Bulk URL Updates

If you need to add URLs to multiple norms at once:

```python
import json

def generate_url(norm_id):
    """Generate URL based on norm ID pattern"""
    if norm_id.startswith('DIR-'):
        year, num = norm_id.replace('DIR-', '').split('/')[:2]
        return f'https://eur-lex.europa.eu/eli/dir/{year}/{num}/oj'

    if norm_id.startswith('REG-'):
        year, num = norm_id.replace('REG-', '').split('/')[:2]
        return f'https://eur-lex.europa.eu/eli/reg/{year}/{num}/oj'

    if norm_id.startswith('EN'):
        clean_id = norm_id.replace(' ', '-').replace('/', '-')
        return f'https://www.en-standard.eu/{clean_id}'

    # Default: EUR-Lex search
    return f'https://eur-lex.europa.eu/search.html?q={norm_id.replace(" ", "+")}'

# Update all norms
with open('data/norms.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)

    for norm in data['norms']:
        if 'url' not in norm or not norm['url']:
            norm['url'] = generate_url(norm['id'])
            print(f"Added URL for {norm['id']}")

    f.seek(0)
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.truncate()

print(f"✓ Updated {len(data['norms'])} norms")
```

---

## Troubleshooting

### "Norm not appearing in results"

1. **Check confidence threshold:**
   ```python
   # In norm_matcher.py, check:
   if result["applies"] and result["confidence"] > 50:
   ```

2. **Test norm individually:**
   ```python
   norm = next(n for n in load_norms() if n['id'] == 'YOUR-NORM-ID')
   result = check_norm_applies(norm, "your product description")
   print(result)
   ```

3. **Check description quality:**
   - Is `applies_to` specific enough?
   - Does `description` explain when it applies?

### "All norms showing low confidence"

- Product description may be too vague
- AI needs more details (voltage, certifications, features)
- Try asking more follow-up questions in conversation phase

### "Analysis taking too long"

```python
# Check worker count in norm_matcher.py
def match_norms_streaming(product_description: str, max_workers: int = 10):
    #                                                             ^^^ Increase to 15-20
```

**Warning:** Too many workers can hit API rate limits!

---

## Resources

- **EUR-Lex:** https://eur-lex.europa.eu/
- **EU Single Market Standards:** https://single-market-economy.ec.europa.eu/
- **CEN Standards:** https://www.cen.eu
- **CENELEC:** https://www.cenelec.eu
- **NormScout Docs:** [/docs](/docs)
- **Implementation Guide:** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)

---

## Questions?

If you need help or have questions about managing norms:

1. Check this guide first
2. Review example norms in `data/norms.json`
3. Test changes locally before deploying
4. Open an issue or contact the development team

**Last Updated:** 2025-01-04
