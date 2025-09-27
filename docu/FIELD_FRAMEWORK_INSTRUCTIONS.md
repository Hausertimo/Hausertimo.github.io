# Field Framework Instructions

## What It Does
Adds dynamic content blocks with alternating backgrounds under "Try Normscout" section after initial form submission. Mix markdown, input fields, and custom HTML.

## Quick Start

### 1. Import in app.py
```python
from field_framework import FieldRenderer, FieldBlock, MarkdownField, InputField, CustomHTMLField
```

### 2. Create Blocks (after user submits initial form)
```python
# In your existing endpoint, after analysis:
global field_renderer
field_renderer = FieldRenderer()

# Create a block
block = field_renderer.create_block("block_id", "Optional Title")
block.add_field(MarkdownField("md1", "## Some markdown text"))
block.add_field(InputField("input1", "Label", "placeholder"))
block.add_field(MarkdownField("md2", "More text"))
block.add_field(CustomHTMLField("html1", "<div>Custom HTML</div>"))
# Add as many fields as you want in any order
```

### 3. Add Container to HTML
Add this where you want fields to appear (e.g., end of demo section):
```html
<div id="dynamic-fields-container"></div>
```

### 4. Load Fields in JavaScript
After showing initial results:
```javascript
loadFieldBlocks();  // Fetches and displays your blocks
```

## Field Types

**MarkdownField**: `MarkdownField("id", "## Markdown content")`
**InputField**: `InputField("id", "Label", "Placeholder")`
**CustomHTMLField**: `CustomHTMLField("id", "<any>HTML</any>")`

## Capturing Input

When user clicks send button, data goes to `/api/fields/submit`:
```python
@app.route("/api/fields/submit", methods=["POST"])
def submit_field_data():
    data = request.get_json()
    block_id = data.get("block_id")
    fields = data.get("fields")  # Dict of field values
    # Process as needed
```

## Notes
- Blocks automatically alternate between light/dark backgrounds
- Only blocks with InputFields show send buttons
- Field IDs must be unique
- Custom button text: `block.set_button_text("Custom Text")`

That's it. The framework handles rendering, styling, and data capture.