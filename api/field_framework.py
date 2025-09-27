"""
Field Framework for NormScout
A modular system for creating dynamic form fields with different types
"""

import json
from typing import List, Dict, Any, Optional


class MarkdownField:
    """Field for displaying markdown formatted text"""
    def __init__(self, field_id: str, content: str):
        self.field_id = field_id
        self.field_type = "markdown"
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "field_type": self.field_type,
            "content": self.content
        }


class InputField:
    """Field for capturing user input"""
    def __init__(self, field_id: str, label: str, placeholder: str = ""):
        self.field_id = field_id
        self.field_type = "input"
        self.label = label
        self.placeholder = placeholder

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "field_type": self.field_type,
            "label": self.label,
            "placeholder": self.placeholder
        }


class CustomHTMLField:
    """Field for custom HTML content"""
    def __init__(self, field_id: str, html_content: str):
        self.field_id = field_id
        self.field_type = "custom_html"
        self.html_content = html_content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "field_type": self.field_type,
            "html_content": self.html_content
        }


class FieldBlock:
    """Container for grouping multiple fields together"""
    def __init__(self, block_id: str, title: str = "", background: str = "light"):
        self.block_id = block_id
        self.title = title
        self.background = background  # "light" or "dark" for alternating
        self.fields = []
        self.has_inputs = False
        self.submit_button_text = "Send & Continue"

    def add_field(self, field) -> None:
        """Add a field to the block"""
        self.fields.append(field)
        # Check if this field requires user input
        if isinstance(field, InputField):
            self.has_inputs = True

    def set_button_text(self, text: str) -> None:
        """Customize the submit button text"""
        self.submit_button_text = text

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for JSON serialization"""
        return {
            "block_id": self.block_id,
            "title": self.title,
            "background": self.background,
            "has_inputs": self.has_inputs,
            "submit_button_text": self.submit_button_text,
            "fields": [field.to_dict() for field in self.fields]
        }


class FieldRenderer:
    """Manages the collection and rendering of field blocks"""
    def __init__(self):
        self.blocks: List[FieldBlock] = []
        self.current_background = "light"

    def create_block(self, block_id: str, title: str = "") -> FieldBlock:
        """Create a new block with alternating background"""
        block = FieldBlock(block_id, title, self.current_background)
        self.current_background = "dark" if self.current_background == "light" else "light"
        self.blocks.append(block)
        return block

    def render_all_blocks(self) -> List[Dict[str, Any]]:
        """Render all blocks as a list of dictionaries"""
        return [block.to_dict() for block in self.blocks]