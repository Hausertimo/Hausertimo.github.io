/**
 * Modular Compliance API Client
 * Provides methods for querying individual compliance fields
 * Supports parallel and chained queries with caching
 */

class ComplianceAPI {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.cacheTimeout = 15 * 60 * 1000; // 15 minutes

        // Available compliance fields
        this.fields = {
            safety_standards: 'Safety Standards & Certifications',
            labeling_requirements: 'Labeling Requirements',
            import_documentation: 'Import Documentation',
            testing_requirements: 'Testing Requirements',
            restricted_substances: 'Restricted Substances',
            packaging_requirements: 'Packaging Requirements',
            environmental_compliance: 'Environmental Compliance',
            market_surveillance: 'Market Surveillance'
        };
    }

    /**
     * Generate cache key for a query
     */
    getCacheKey(field, product, country) {
        return `${field}:${product}:${country}`;
    }

    /**
     * Get cached result if available and not expired
     */
    getCachedResult(key) {
        const cached = this.cache.get(key);
        if (cached) {
            const age = Date.now() - cached.timestamp;
            if (age < this.cacheTimeout) {
                console.log(`Cache hit for ${key}`);
                return cached.data;
            } else {
                this.cache.delete(key);
            }
        }
        return null;
    }

    /**
     * Cache a result
     */
    cacheResult(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
        console.log(`Cached result for ${key}`);
    }

    /**
     * Query a single compliance field
     */
    async querySingleField(field, product, country) {
        // Check cache first
        const cacheKey = this.getCacheKey(field, product, country);
        const cached = this.getCachedResult(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/field/${field}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product, country })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Cache successful responses
            if (data.status === 'success') {
                this.cacheResult(cacheKey, data);
            }

            return data;
        } catch (error) {
            console.error(`Error querying field ${field}:`, error);
            return {
                field: field,
                status: 'error',
                error: error.message
            };
        }
    }

    /**
     * Query multiple fields in parallel
     */
    async queryParallel(fields, product, country) {
        const promises = fields.map(field =>
            this.querySingleField(field, product, country)
        );

        try {
            const results = await Promise.all(promises);
            return {
                status: 'success',
                queryType: 'parallel',
                results: results.reduce((acc, result) => {
                    acc[result.field] = result;
                    return acc;
                }, {})
            };
        } catch (error) {
            console.error('Error in parallel queries:', error);
            return {
                status: 'error',
                queryType: 'parallel',
                error: error.message
            };
        }
    }

    /**
     * Query fields in sequence (chained)
     */
    async queryChain(fields, product, country) {
        const results = {};
        const context = [];

        for (const field of fields) {
            try {
                // You can modify this to pass context to backend if needed
                const result = await this.querySingleField(field, product, country);
                results[field] = result;

                // Build context from successful queries
                if (result.status === 'success') {
                    context.push({
                        field: field,
                        summary: result.content.substring(0, 100) + '...'
                    });
                }
            } catch (error) {
                console.error(`Error in chained query for ${field}:`, error);
                results[field] = {
                    field: field,
                    status: 'error',
                    error: error.message
                };
            }
        }

        return {
            status: 'success',
            queryType: 'chain',
            results: results,
            context: context
        };
    }

    /**
     * Query fields using backend parallel endpoint
     */
    async queryParallelBackend(fields, product, country) {
        try {
            const response = await fetch(`${this.baseUrl}/api/fields/parallel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fields, product, country })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error in backend parallel query:', error);
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    /**
     * Progressive loading - query fields one by one and update UI
     */
    async queryProgressive(fields, product, country, onFieldComplete) {
        const results = {};

        for (const field of fields) {
            const result = await this.querySingleField(field, product, country);
            results[field] = result;

            // Callback for UI update
            if (onFieldComplete) {
                onFieldComplete(field, result, Object.keys(results).length, fields.length);
            }
        }

        return {
            status: 'success',
            queryType: 'progressive',
            results: results
        };
    }

    /**
     * Get all available fields
     */
    async getAvailableFields() {
        try {
            const response = await fetch(`${this.baseUrl}/api/fields/available`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching available fields:', error);
            return {
                status: 'error',
                error: error.message
            };
        }
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
        console.log('Cache cleared');
    }

    /**
     * Get cache statistics
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys()),
            memoryEstimate: JSON.stringify(Array.from(this.cache.values())).length
        };
    }
}

/**
 * UI Helper functions for displaying results
 */
class ComplianceUI {
    /**
     * Create a field result card
     */
    static createFieldCard(fieldName, result) {
        const statusClass = result.status === 'success' ? 'success' : 'error';
        const icon = result.status === 'success' ? '✓' : '✗';

        return `
            <div class="compliance-field-card ${statusClass}" data-field="${result.field}">
                <div class="field-header">
                    <span class="field-icon">${icon}</span>
                    <h3 class="field-title">${fieldName}</h3>
                </div>
                <div class="field-content">
                    ${result.status === 'success'
                        ? formatMarkdownToHTML(result.content)
                        : `<p class="error-message">Error: ${result.error}</p>`
                    }
                </div>
            </div>
        `;
    }

    /**
     * Create a loading skeleton for a field
     */
    static createLoadingSkeleton(fieldName) {
        return `
            <div class="compliance-field-card loading" data-field="${fieldName}">
                <div class="field-header">
                    <span class="field-icon spinner"></span>
                    <h3 class="field-title">${fieldName}</h3>
                </div>
                <div class="field-content">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                </div>
            </div>
        `;
    }

    /**
     * Create progress indicator
     */
    static createProgressIndicator(current, total) {
        const percentage = Math.round((current / total) * 100);
        return `
            <div class="progress-container">
                <div class="progress-bar" style="width: ${percentage}%"></div>
                <span class="progress-text">${current} / ${total} fields analyzed</span>
            </div>
        `;
    }
}

/**
 * Example usage functions
 */

// Initialize the API client
const complianceAPI = new ComplianceAPI();

// Example: Query all fields in parallel
async function analyzeProductCompliance(product, country) {
    const fields = Object.keys(complianceAPI.fields);
    const results = await complianceAPI.queryParallel(fields, product, country);
    return results;
}

// Example: Progressive loading with UI updates
async function analyzeWithProgress(product, country, containerId) {
    const container = document.getElementById(containerId);
    const fields = Object.keys(complianceAPI.fields);

    // Show loading skeletons
    container.innerHTML = fields.map(field =>
        ComplianceUI.createLoadingSkeleton(complianceAPI.fields[field])
    ).join('');

    // Query progressively
    const results = await complianceAPI.queryProgressive(
        fields,
        product,
        country,
        (field, result, completed, total) => {
            // Update the specific field card
            const card = container.querySelector(`[data-field="${field}"]`);
            if (card) {
                card.outerHTML = ComplianceUI.createFieldCard(
                    complianceAPI.fields[field],
                    result
                );
            }

            // Update progress
            const progressDiv = document.getElementById('progress-indicator');
            if (progressDiv) {
                progressDiv.innerHTML = ComplianceUI.createProgressIndicator(completed, total);
            }
        }
    );

    return results;
}

// Example: Query specific fields only
async function querySpecificFields(fields, product, country) {
    return await complianceAPI.queryParallel(fields, product, country);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ComplianceAPI, ComplianceUI };
}