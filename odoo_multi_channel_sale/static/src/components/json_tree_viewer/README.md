# JSON Tree Viewer Component

A reusable OWL component for displaying JSON data in an expandable/collapsible tree format, similar to Chrome DevTools JSON viewer.

## Features

- ✅ Expandable/collapsible tree structure
- ✅ Support for nested objects and arrays
- ✅ Type-aware value formatting
- ✅ Clean, developer-friendly UI
- ✅ Read-only viewer
- ✅ Handles large JSON safely
- ✅ Odoo 18 OWL component architecture

## Usage

### Method 1: As a Field Widget

In your view XML, use the `json_tree_viewer` widget on a Text field:

```xml
<field name="json_data" widget="json_tree_viewer" nolabel="1" readonly="1"/>
```

The field should contain a JSON string.

### Method 2: As a Standalone Component

You can also use the component directly in custom views:

```xml
<JsonTreeViewer jsonString="'{\"key\": \"value\"}'"/>
```

Or with data from context:

```xml
<JsonTreeViewer data="context.get('json_data')"/>
```

## Python Example

### Passing JSON from Python to View

```python
from odoo import fields, models
import json

class MyModel(models.Model):
    _name = 'my.model'
    
    json_data = fields.Text(string='JSON Data', readonly=True)
    
    def action_view_json(self):
        # Prepare JSON data
        data = {
            'order_id': self.id,
            'items': [{'name': 'Item 1', 'qty': 10}],
            'status': 'active'
        }
        
        # Convert to JSON string
        json_string = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Create wizard or update record
        wizard = self.env['my.wizard'].create({
            'json_data': json_string
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'JSON Viewer',
            'res_model': 'my.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
```

## Component Props

- `data` (optional): Object, Array, or String - JSON data to display
- `jsonString` (optional): String - JSON string to parse and display

## Styling

The component uses CSS classes that can be customized:
- `.json-tree-viewer-container` - Main container
- `.json-tree-viewer` - Tree viewer area
- `.json-node` - Individual node
- `.json-toggle` - Expand/collapse toggle
- `.json-key` - Object/array key
- `.json-value` - Value display
- `.json-type` - Type indicator (Object/Array)
- `.json-count` - Item count

## Architecture

- **Component**: `JsonTreeViewer` - Main component
- **Sub-component**: `JsonTreeNode` - Recursive node component
- **Template**: QWeb template with recursive rendering
- **State Management**: OWL useState for expand/collapse state

## Files

- `json_tree_viewer.js` - Component implementation
- `json_tree_viewer.xml` - QWeb templates
- `json_tree_viewer.css` - Styling (already in assets)
