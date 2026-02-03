# Fix: JSON Field Rendering as Plain Text

## Problem Explanation

### Why JSON Was Rendering as Plain Text

The JSON field was displaying as plain text because:

1. **Default Widget Behavior**: The view XML was using `widget="text"`, which is Odoo's default text field widget. This widget simply renders the field value as a `<span>` element with no special formatting.

2. **Missing Custom Widget**: The custom `json_tree_viewer` widget was created but not being used in the view XML.

3. **Field Widget Not Applied**: Odoo only applies custom widgets when explicitly specified in the view XML using the `widget="widget_name"` attribute.

### What Was Happening

```xml
<!-- BEFORE (Wrong) -->
<field name="json_data" widget="text" nolabel="1" readonly="1" class="json-tree-viewer"/>
```

This rendered as:
```html
<div class="o_field_widget o_field_text json-tree-viewer">
  <span>{ ... large JSON ... }</span>
</div>
```

The `class="json-tree-viewer"` attribute was ignored because:
- CSS classes don't change widget behavior
- The `widget="text"` attribute tells Odoo to use the default text widget
- No JavaScript component was being loaded to transform the JSON

## Solution

### 1. Fixed View XML

Changed from `widget="text"` to `widget="json_tree_viewer"`:

```xml
<!-- AFTER (Correct) -->
<field name="json_data" widget="json_tree_viewer" nolabel="1" readonly="1"/>
```

### 2. Fixed Field Widget Implementation

The field widget now:
- Properly extends `Component` with `standardFieldProps`
- Reads field value from `this.props.record.data[this.props.name]`
- Parses JSON string safely
- Renders interactive tree using OWL components

### 3. How It Works Now

1. **View XML** specifies `widget="json_tree_viewer"`
2. **Odoo Field System** loads the registered widget component
3. **JsonTreeViewerField** component receives:
   - `props.record` - The record object
   - `props.name` - The field name ("json_data")
4. **Component** reads value from `record.data[name]`
5. **JSON Parsing** converts string to object/array
6. **Tree Rendering** uses recursive `JsonTreeNode` components
7. **Interactive UI** with expand/collapse functionality

## Technical Details

### Field Widget Registration

```javascript
registry.category("fields").add("json_tree_viewer", {
    component: JsonTreeViewerField,
    supportedTypes: ["text", "char"],
});
```

### Field Widget Props

The widget receives standard field props:
- `record` - The record object containing field data
- `name` - The field name (e.g., "json_data")
- `readonly` - Whether field is readonly
- `required` - Whether field is required
- etc.

### Data Flow

```
Python Model
    ↓
Field Value (JSON string)
    ↓
View XML: widget="json_tree_viewer"
    ↓
Odoo Field System
    ↓
JsonTreeViewerField Component
    ↓
Read: record.data[name]
    ↓
Parse: JSON.parse(fieldValue)
    ↓
Render: JsonTreeNode (recursive)
    ↓
Interactive JSON Tree UI
```

## Files Modified

1. **View XML**: `wizard/salla_order_json_viewer.xml`
   - Changed `widget="text"` → `widget="json_tree_viewer"`

2. **Field Widget**: `static/src/components/json_tree_viewer/json_tree_viewer.js`
   - Fixed to extend Component with standardFieldProps
   - Properly reads field value from record
   - Handles JSON parsing safely

## Result

The JSON field now renders as an interactive tree viewer with:
- ✅ Expandable/collapsible nodes
- ✅ ▶ / ▼ toggle arrows
- ✅ Nested object/array support
- ✅ Type-aware value formatting
- ✅ Clean, developer-friendly UI
- ✅ Read-only (no editing)

## Usage

Simply use the widget in any view:

```xml
<field name="json_data" widget="json_tree_viewer" nolabel="1" readonly="1"/>
```

The field must contain a valid JSON string, which will be automatically parsed and rendered as an interactive tree.
