/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * JSON Tree Node Component (Recursive)
 * Renders a single node in the JSON tree
 */
export class JsonTreeNode extends Component {
    static template = "odoo_multi_channel_sale.JsonTreeNode";
    static components = {};
    static props = {
        data: { optional: true },
        path: { type: String },
        level: { type: Number },
        expanded: { optional: true },
        onToggle: { type: Function },
    };

    /**
     * Get display name for a key from its path
     */
    getKeyDisplay() {
        const path = this.props.path;
        if (path === 'root') {
            return 'root';
        }
        if (path.includes('[')) {
            const match = path.match(/\[(\d+)\]$/);
            return match ? `[${match[1]}]` : path.split('.').pop();
        }
        return path.split('.').pop();
    }

    /**
     * Get child nodes for an object or array
     */
    getChildren() {
        const data = this.props.data;
        const parentPath = this.props.path;

        if (!data) {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                path: parentPath === 'root' ? `[${index}]` : `${parentPath}[${index}]`,
                key: `[${index}]`,
                value: item,
            }));
        } else if (typeof data === 'object' && data !== null) {
            return Object.keys(data).map((key) => ({
                path: parentPath === 'root' ? key : `${parentPath}.${key}`,
                key: key,
                value: data[key],
            }));
        }
        return [];
    }

    /**
     * Get the type of a value
     */
    getValueType() {
        const value = this.props.data;
        if (value === null || value === undefined) return 'null';
        if (Array.isArray(value)) return 'array';
        return typeof value;
    }

    /**
     * Format a value for display
     */
    formatValue() {
        const value = this.props.data;
        if (value === null || value === undefined) return 'null';
        if (typeof value === 'string') return `"${value}"`;
        return String(value);
    }

    /**
     * Check if a value is expandable
     */
    isExpandable() {
        const value = this.props.data;
        if (!value) return false;
        return (typeof value === 'object' && value !== null) || Array.isArray(value);
    }

    /**
     * Get count of items
     */
    getItemCount() {
        const value = this.props.data;
        if (!value) return 0;
        if (Array.isArray(value)) {
            return value.length;
        } else if (typeof value === 'object' && value !== null) {
            return Object.keys(value).length;
        }
        return 0;
    }

    /**
     * Check if this node is expanded
     */
    isExpanded() {
        if (!this.props.expanded || !(this.props.expanded instanceof Set)) {
            return false;
        }
        return this.props.expanded.has(this.props.path);
    }

    /**
     * Toggle this node's expanded state
     */
    onToggleClick() {
        this.props.onToggle(this.props.path);
    }
}

// Set JsonTreeNode as its own component for recursion (must be after class definition)
JsonTreeNode.components = { JsonTreeNode };

/**
 * JSON Tree Viewer Component
 * Displays JSON data in an expandable/collapsible tree format
 * Similar to Chrome DevTools JSON viewer
 */
export class JsonTreeViewer extends Component {
    static template = "odoo_multi_channel_sale.JsonTreeViewer";
    static components = { JsonTreeNode };
    static props = {
        data: { type: [String, Object, Array], optional: true },
        jsonString: { type: String, optional: true },
    };

    setup() {
        this.state = useState({
            expanded: new Set(['root']),
            parsedData: null,
            error: null,
        });

        onMounted(() => {
            this.parseJsonData();
        });
    }

    /**
     * Parse JSON data from props
     * Handles both string and object inputs
     */
    parseJsonData() {
        try {
            let data = this.props.data;
            
            // If jsonString prop is provided, use it
            if (this.props.jsonString) {
                data = JSON.parse(this.props.jsonString);
            }
            // If data is a string, parse it
            else if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            // If data is already an object/array, use it directly
            else if (data === null || data === undefined) {
                this.state.error = "No JSON data provided";
                return;
            }

            this.state.parsedData = data;
            this.state.error = null;
        } catch (e) {
            this.state.error = `Invalid JSON: ${e.message}`;
            this.state.parsedData = null;
        }
    }

    /**
     * Toggle expand/collapse state for a path
     * @param {string} path - Path to toggle
     */
    togglePath(path) {
        if (this.state.expanded.has(path)) {
            this.state.expanded.delete(path);
        } else {
            this.state.expanded.add(path);
        }
    }
}

/**
 * Field Widget Adapter for JSON Tree Viewer
 * Allows using the component as a field widget in Odoo 18 views
 * Properly extends Component with standard field props
 */
export class JsonTreeViewerField extends Component {
    static template = "odoo_multi_channel_sale.JsonTreeViewer";
    static components = { JsonTreeNode };
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            expanded: new Set(['root']),
            parsedData: null,
            error: null,
        });

        onMounted(() => {
            this.parseJsonData();
        });
    }

    /**
     * Get the field value from the record
     * @returns {string|Object|Array|null} Field value
     */
    getFieldValue() {
        if (this.props.record && this.props.name) {
            return this.props.record.data[this.props.name];
        }
        return null;
    }

    /**
     * Parse JSON data from the field value
     */
    parseJsonData() {
        try {
            const fieldValue = this.getFieldValue();
            
            if (fieldValue === null || fieldValue === undefined || fieldValue === false) {
                this.state.error = "No JSON data available";
                this.state.parsedData = null;
                return;
            }

            let data = fieldValue;
            
            // If data is a string, parse it as JSON
            if (typeof data === 'string') {
                const trimmed = data.trim();
                if (!trimmed) {
                    this.state.error = "Empty JSON string";
                    this.state.parsedData = null;
                    return;
                }
                data = JSON.parse(trimmed);
            }
            // If data is already an object/array, use it directly
            else if (typeof data === 'object') {
                // Already parsed, use as is
                data = data;
            }
            else {
                this.state.error = "Invalid data type for JSON viewer";
                this.state.parsedData = null;
                return;
            }

            this.state.parsedData = data;
            this.state.error = null;
        } catch (e) {
            this.state.error = `Invalid JSON: ${e.message}`;
            this.state.parsedData = null;
        }
    }

    /**
     * Toggle expand/collapse state for a path
     * @param {string} path - Path to toggle
     */
    togglePath(path) {
        if (this.state.expanded.has(path)) {
            this.state.expanded.delete(path);
        } else {
            this.state.expanded.add(path);
        }
    }
}

// Register as a field widget for use in views
registry.category("fields").add("json_tree_viewer", {
    component: JsonTreeViewerField,
    supportedTypes: ["text", "char"],
});
