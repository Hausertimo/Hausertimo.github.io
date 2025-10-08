# Field Framework Documentation

## Overview
A modular framework for creating dynamic, interactive field blocks with alternating backgrounds. Perfect for forms, surveys, error messages, and any dynamic content that needs to be displayed after user interactions.

## Quick Start

### 1. Import Required Components
```python
from api.field_framework import (
    FieldRenderer,
    MarkdownField,
    InputField,
    FormField,
    TextAreaField,
    ButtonField,
    CustomHTMLField
)
```

### 2. Initialize and Use in Your Endpoint
```python
# Get or create renderer instance
import api.fields as fields_module
if not hasattr(fields_module, 'field_renderer'):
    fields_module.field_renderer = FieldRenderer()
else:
    fields_module.field_renderer.clear_blocks()  # Clear previous fields

# Create blocks and add fields
block = fields_module.field_renderer.create_block("block_id", "Optional Title")
block.add_field(MarkdownField("id", "# Your Content"))
```

### 3. Return Signal to Frontend
```python
return jsonify({
    "status": "your_status",
    "show_fields": True  # This triggers loadFieldBlocks() in JS
})
```

## Field Types

### MarkdownField
Display formatted text with markdown support.
```python
MarkdownField("field_id", "## Title\n- Bullet point\n**Bold text**")
```

### InputField
Basic text input field.
```python
InputField("field_id", "Label", "Placeholder text")
```

### FormField
Enhanced input with type, value, and validation.
```python
FormField("email", "Your Email", "john@example.com",
          input_type="email",  # text, email, hidden, number, etc.
          value="prefilled@email.com",  # Pre-filled value
          required=True)
```

### TextAreaField
Multi-line text input.
```python
TextAreaField("message", "Your Message", "Type here...", rows=5)
```

### ButtonField
Clickable button with actions.
```python
ButtonField("btn_id", "Click Me", action="expand")  # action triggers JS
```

### CustomHTMLField
Raw HTML injection for complex content.
```python
CustomHTMLField("custom", "<div class='special'>Any HTML</div>")
```

## Block Properties

### Basic Block
```python
block = renderer.create_block("block_id", "Title")
block.add_field(...)  # Add any field type
```

### Hidden Block (Show with JavaScript)
```python
hidden_block = renderer.create_block("hidden_id", "", hidden=True)
```

### Custom Submit Endpoint
```python
form_block = renderer.create_block("form_id")
form_block.submit_endpoint = "/api/custom/endpoint"  # Override default
form_block.set_button_text("Custom Button Text")
```

## Complete Examples

### Example 1: Error Message with Feedback Form
```python
# Error message block
error_block = renderer.create_block("error", "")
error_block.add_field(MarkdownField("msg", "### ⚠️ Error Detected"))
error_block.add_field(MarkdownField("hint", "Please try again"))

# Button to reveal feedback form
btn_block = renderer.create_block("button_block", "")
btn_block.add_field(ButtonField("feedback_btn", "Report Issue", action="expand"))

# Hidden feedback form
form = renderer.create_block("feedback_form", "Help Us", hidden=True)
form.add_field(FormField("name", "Name", "John Doe"))
form.add_field(FormField("email", "Email", "john@example.com", input_type="email"))
form.add_field(TextAreaField("details", "Describe the issue", "", rows=4))
form.submit_endpoint = "/api/feedback/submit"
form.set_button_text("Send Report")
```

### Example 2: Multi-Step Survey
```python
# Step 1: Basic Info
step1 = renderer.create_block("step1", "Step 1: About You")
step1.add_field(FormField("name", "Full Name", "Your name"))
step1.add_field(FormField("company", "Company", "Your company"))
step1.set_button_text("Next Step")

# Step 2: Preferences (initially hidden)
step2 = renderer.create_block("step2", "Step 2: Preferences", hidden=True)
step2.add_field(MarkdownField("q1", "### What features do you need?"))
step2.add_field(CustomHTMLField("checks", """
    <label><input type="checkbox" name="features" value="api"> API Access</label>
    <label><input type="checkbox" name="features" value="support"> Premium Support</label>
"""))
```

### Example 3: Product Validation Flow
```python
# Clear any existing fields first
fields_module.field_renderer.clear_blocks()

# Check if product is valid
if not validate_product_input(product):
    # Show error
    block = renderer.create_block("error", "")
    block.add_field(MarkdownField("msg", "### Invalid Product"))

    # Add feedback option
    feedback = renderer.create_block("feedback", "", hidden=True)
    feedback.add_field(FormField("product", "", "", input_type="hidden", value=product))
    feedback.add_field(TextAreaField("why_valid", "Why is this valid?", "Explain..."))

    return jsonify({"status": "invalid", "show_fields": True})
```

## JavaScript Integration

### Loading Fields
Fields are automatically loaded when backend returns `show_fields: True`:
```javascript
// In your response handler
if (data.show_fields) {
    loadFieldBlocks();  // Loads and renders all blocks
}
```

### Clearing Fields
```javascript
clearFieldBlocks();  // Removes all field blocks from DOM
```

### Button Actions
Buttons with `action="expand"` automatically show hidden blocks:
```javascript
// Handled automatically by handleFieldButton()
// Shows block with id "feedback_form" when button clicked
```

### Custom Form Submission
Forms with `submit_endpoint` automatically POST to that endpoint:
```javascript
// Handled automatically by submitFormData()
// Collects all inputs and sends to specified endpoint
```

## Backend Endpoints

### Field Retrieval Endpoint
```python
@app.route("/api/fields/get", methods=["GET"])
def get_fields():
    if field_renderer and field_renderer.blocks:
        return jsonify({
            "status": "success",
            "blocks": field_renderer.render_all_blocks()
        })
    return jsonify({"status": "success", "blocks": []})
```

### Custom Submit Endpoint Example
```python
@app.route("/api/feedback/submit", methods=["POST"])
def submit_feedback():
    data = request.get_json()

    # Save to file
    feedback = {
        "timestamp": datetime.now().isoformat(),
        "name": data.get("name"),
        "email": data.get("email"),
        "message": data.get("message")
    }

    with open("feedback.jsonl", "a") as f:
        f.write(json.dumps(feedback) + "\n")

    return jsonify({
        "status": "success",
        "message": "Thank you for your feedback!"
    })
```

## Styling

### Alternating Backgrounds
Blocks automatically alternate between light and dark:
- First block: `field-block-light` (white background)
- Second block: `field-block-dark` (gray background)
- Third block: `field-block-light` (white background)
- etc.

### CSS Classes
- `.field-block` - Main block container
- `.field-block-light` - Light background
- `.field-block-dark` - Dark background
- `.field-block-title` - Block title
- `.field-block-content` - Fields container
- `.field-block-actions` - Button container
- `.field-type-{type}` - Specific field type styling

## Tips & Best Practices

1. **Always Clear Fields**: Call `clear_blocks()` before creating new ones to avoid stacking
2. **Use Hidden Blocks**: Hide complex forms initially, reveal with buttons
3. **Custom Endpoints**: Use `submit_endpoint` for specialized form handling
4. **Pre-fill Values**: Use FormField with `value` parameter for better UX
5. **Validation**: Add `required=True` to FormField for browser validation
6. **Feedback Storage**: Use JSON Lines (.jsonl) format for easy appending

## Common Patterns

### Progressive Disclosure
```python
# Simple content first
intro = renderer.create_block("intro", "")
intro.add_field(MarkdownField("text", "### Welcome"))
intro.add_field(ButtonField("more", "Show More", action="expand"))

# Detailed content hidden
details = renderer.create_block("details", "", hidden=True)
details.add_field(MarkdownField("info", "Detailed information..."))
```

### Error Recovery Flow
```python
if error_occurred:
    error = renderer.create_block("error", "")
    error.add_field(MarkdownField("msg", f"### Error: {error_msg}"))

    # Offer recovery options
    options = renderer.create_block("options", "")
    options.add_field(ButtonField("retry", "Try Again", action="retry"))
    options.add_field(ButtonField("report", "Report Issue", action="expand"))
```

### Dynamic Content Based on User Input
```python
# After user submits initial data
if user_type == "business":
    block = renderer.create_block("business_fields", "Business Information")
    block.add_field(FormField("company", "Company Name", ""))
    block.add_field(FormField("vat", "VAT Number", ""))
else:
    block = renderer.create_block("personal_fields", "Personal Information")
    block.add_field(FormField("age", "Age", "", input_type="number"))
```

## Debugging

### Check if Fields are Loading
```javascript
// In browser console
fetch('/api/fields/get').then(r => r.json()).then(console.log)
```

### Verify Renderer State
```python
# In your endpoint
logger.info(f"Blocks count: {len(field_renderer.blocks)}")
logger.info(f"Blocks: {[b.block_id for b in field_renderer.blocks]}")
```

### Common Issues
- **Fields not showing**: Ensure `show_fields: True` in response
- **Fields stacking**: Call `clear_blocks()` before adding new ones
- **Form not submitting**: Check `submit_endpoint` is correct
- **Hidden blocks not showing**: Verify button `action="expand"` matches block ID

## Future Enhancements Ideas
- Add field dependencies (show field B only if field A has value X)
- Add real-time validation
- Add file upload field type
- Add date/time picker field types
- Add progress indicators for multi-step forms
- Add field animations/transitions