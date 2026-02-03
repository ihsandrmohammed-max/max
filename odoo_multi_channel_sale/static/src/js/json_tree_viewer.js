/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

/**
 * JSON Tree Viewer
 * Renders JSON data in expandable tree format after form loads
 * Patches FormController to automatically render JSON tree viewers
 */
patch(FormController.prototype, {
    /**
     * Override onMounted to render JSON tree viewers after form is mounted
     */
    onMounted() {
        super.onMounted(...arguments);
        // Use setTimeout to ensure the form fields are fully rendered
        setTimeout(() => {
            this._renderJsonTreeViewers();
        }, 100);
    },

    /**
     * Render JSON tree viewers for all fields with json-tree-viewer class
     */
    _renderJsonTreeViewers() {
        const self = this;
        const jsonViewers = this.el.querySelectorAll('.json-tree-viewer');
        
        jsonViewers.forEach((field) => {
            if (field.classList.contains('json-tree-rendered')) {
                return;
            }
            field.classList.add('json-tree-rendered');
            
            const textarea = field.querySelector('textarea');
            const input = field.querySelector('input');
            const value = (textarea && textarea.value) || (input && input.value) || field.textContent.trim();
            
            if (!value) {
                field.innerHTML = '<div class="text-muted">No JSON data available</div>';
                return;
            }

            try {
                const jsonData = typeof value === 'string' ? JSON.parse(value) : value;
                const expanded = new Set(['root']);
                field.innerHTML = this._renderJsonTree(jsonData, expanded);
                this._attachJsonToggleHandlers(field, expanded);
            } catch (e) {
                field.innerHTML = '<div class="text-danger">Invalid JSON: ' + this._escapeHtml(e.message) + '</div>';
            }
        });
    },

    /**
     * Render JSON data as expandable tree HTML
     * @param {*} data - JSON data to render
     * @param {Set} expanded - Set of expanded paths
     * @param {string} parentPath - Parent path for nested rendering
     * @param {number} level - Current nesting level
     * @returns {string} HTML string
     */
    _renderJsonTree(data, expanded, parentPath, level) {
        parentPath = parentPath || 'root';
        level = level || 0;
        let html = '';
        const self = this;

        if (data === null || data === undefined) {
            const type = data === null ? 'null' : 'undefined';
            const value = data === null ? 'null' : 'undefined';
            const keyDisplay = parentPath === 'root' ? 'root' : this._getJsonKeyDisplay(parentPath);
            html += '<div class="json-node" style="padding-left: ' + (level * 20) + 'px;">';
            html += '<span class="json-key">' + this._escapeHtml(keyDisplay) + '</span>';
            html += '<span class="json-separator">:</span>';
            html += '<span class="json-value json-value-' + type + '">' + this._escapeHtml(value) + '</span>';
            html += '</div>';
            return html;
        }

        const valueType = typeof data;

        if (valueType === 'boolean' || valueType === 'number' || valueType === 'string') {
            const keyDisplay = parentPath === 'root' ? 'root' : this._getJsonKeyDisplay(parentPath);
            html += '<div class="json-node" style="padding-left: ' + (level * 20) + 'px;">';
            html += '<span class="json-key">' + this._escapeHtml(keyDisplay) + '</span>';
            html += '<span class="json-separator">:</span>';
            if (valueType === 'string') {
                html += '<span class="json-value json-value-string">"' + this._escapeHtml(String(data)) + '"</span>';
            } else {
                html += '<span class="json-value json-value-' + valueType + '">' + this._escapeHtml(String(data)) + '</span>';
            }
            html += '</div>';
            return html;
        }

        if (Array.isArray(data)) {
            const keyDisplay = parentPath === 'root' ? 'root' : this._getJsonKeyDisplay(parentPath);
            const isExpanded = expanded.has(parentPath);
            html += '<div class="json-node" style="padding-left: ' + (level * 20) + 'px;">';
            html += '<span class="json-toggle" data-path="' + this._escapeHtml(parentPath) + '">';
            html += '<i class="fa ' + (isExpanded ? 'fa-caret-down' : 'fa-caret-right') + '"></i>';
            html += '</span>';
            html += '<span class="json-key">' + this._escapeHtml(keyDisplay) + '</span>';
            html += '<span class="json-type">Array</span>';
            html += '<span class="json-count">(' + data.length + ')</span>';
            html += '</div>';

            if (isExpanded) {
                data.forEach((item, index) => {
                    const itemPath = parentPath + '[' + index + ']';
                    html += self._renderJsonTree(item, expanded, itemPath, level + 1);
                });
            }
            return html;
        }

        if (valueType === 'object' && data !== null) {
            const keys = Object.keys(data);
            const keyDisplay = parentPath === 'root' ? 'root' : this._getJsonKeyDisplay(parentPath);
            const isExpanded = expanded.has(parentPath);
            html += '<div class="json-node" style="padding-left: ' + (level * 20) + 'px;">';
            html += '<span class="json-toggle" data-path="' + this._escapeHtml(parentPath) + '">';
            html += '<i class="fa ' + (isExpanded ? 'fa-caret-down' : 'fa-caret-right') + '"></i>';
            html += '</span>';
            html += '<span class="json-key">' + this._escapeHtml(keyDisplay) + '</span>';
            html += '<span class="json-type">Object</span>';
            html += '<span class="json-count">(' + keys.length + ')</span>';
            html += '</div>';

            if (isExpanded) {
                keys.forEach((key) => {
                    const itemPath = parentPath === 'root' ? key : parentPath + '.' + key;
                    html += self._renderJsonTree(data[key], expanded, itemPath, level + 1);
                });
            }
            return html;
        }

        return html;
    },

    /**
     * Get display name for JSON key from path
     * @param {string} path - Full path to the key
     * @returns {string} Display name
     */
    _getJsonKeyDisplay(path) {
        if (path.includes('[')) {
            const match = path.match(/\[(\d+)\]$/);
            return match ? '[' + match[1] + ']' : path.split('.').pop();
        }
        return path.split('.').pop();
    },

    /**
     * Escape HTML special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    _escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, (m) => map[m]);
    },

    /**
     * Attach click handlers for JSON tree toggle buttons
     * @param {HTMLElement} field - Field element containing JSON tree
     * @param {Set} expanded - Set of expanded paths
     */
    _attachJsonToggleHandlers(field, expanded) {
        const self = this;
        const textarea = field.querySelector('textarea');
        const input = field.querySelector('input');
        const originalValue = (textarea && textarea.value) || (input && input.value) || field.textContent.trim();
        field.dataset.originalValue = originalValue;
        
        const toggles = field.querySelectorAll('.json-toggle');
        toggles.forEach((toggle) => {
            toggle.addEventListener('click', function() {
                const path = this.dataset.path;
                if (expanded.has(path)) {
                    expanded.delete(path);
                } else {
                    expanded.add(path);
                }
                const value = field.dataset.originalValue;
                try {
                    const jsonData = typeof value === 'string' ? JSON.parse(value) : value;
                    field.innerHTML = self._renderJsonTree(jsonData, expanded);
                    self._attachJsonToggleHandlers(field, expanded);
                } catch (e) {
                    field.innerHTML = '<div class="text-danger">Error: ' + self._escapeHtml(e.message) + '</div>';
                }
            });
        });
    }
});
