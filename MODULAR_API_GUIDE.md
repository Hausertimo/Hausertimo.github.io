# Modular Compliance API Guide

## Overview
The modular API framework allows you to query individual compliance fields separately, either in parallel (for speed) or chained (for context-aware queries). This provides flexibility and efficiency compared to querying everything at once.

## Architecture

### Backend (Python/Flask)
- **api_framework.py**: Core framework with field definitions and query logic
- **ComplianceFieldQuery**: Class handling individual field queries with caching
- **Endpoints**:
  - `/api/field/<field>` - Query single field
  - `/api/fields/parallel` - Query multiple fields in parallel
  - `/api/fields/chain` - Query fields sequentially with context
  - `/api/fields/available` - Get list of available fields

### Frontend (JavaScript)
- **compliance_api.js**: JavaScript client library
- **ComplianceAPI**: Main API client class with caching
- **ComplianceUI**: UI helper functions for rendering results

## Available Compliance Fields

1. **safety_standards** - Safety standards and certifications
2. **labeling_requirements** - Product labeling requirements
3. **import_documentation** - Import forms and permits
4. **testing_requirements** - Required testing and certification bodies
5. **restricted_substances** - Banned/restricted materials
6. **packaging_requirements** - Packaging and recycling rules
7. **environmental_compliance** - WEEE, RoHS, energy standards
8. **market_surveillance** - Post-market obligations

## Query Methods

### 1. Parallel Queries (Fastest)
All fields are queried simultaneously. Best for getting complete results quickly.

```javascript
const api = new ComplianceAPI();
const results = await api.queryParallel(
    ['safety_standards', 'labeling_requirements'],
    'Bluetooth Speaker',
    'eu'
);
```

**Pros:**
- Fastest for multiple fields
- All results arrive at once
- Good for initial analysis

**Cons:**
- Higher API load
- No context between fields

### 2. Progressive Loading
Fields are queried one by one with UI updates after each.

```javascript
const results = await api.queryProgressive(
    fields,
    product,
    country,
    (field, result, completed, total) => {
        // Update UI for each completed field
        updateFieldCard(field, result);
        updateProgress(completed, total);
    }
);
```

**Pros:**
- User sees results immediately
- Lower memory usage
- Good UX for slow connections

**Cons:**
- Slower overall completion
- Sequential processing

### 3. Chained Queries (Context-Aware)
Each query can use context from previous queries.

```javascript
const results = await api.queryChain(
    ['safety_standards', 'testing_requirements'],
    'Bluetooth Speaker',
    'eu'
);
```

**Pros:**
- Context-aware responses
- More intelligent results
- Avoids redundancy

**Cons:**
- Slowest method
- Sequential by nature

## Caching

The system includes a 15-minute cache on both backend and frontend:

```javascript
// Clear cache manually
api.clearCache();

// Get cache statistics
const stats = api.getCacheStats();
console.log(`Cache has ${stats.size} items`);
```

## Usage Examples

### Basic Single Field Query
```javascript
const api = new ComplianceAPI();

// Query single field
const result = await api.querySingleField(
    'safety_standards',
    'Laptop',
    'us'
);

if (result.status === 'success') {
    console.log(result.content);
} else {
    console.error(result.error);
}
```

### Complete Product Analysis
```javascript
async function analyzeProduct(product, country) {
    const api = new ComplianceAPI();

    // Get all available fields
    const available = await api.getAvailableFields();
    const allFields = available.fields;

    // Query all fields in parallel
    const results = await api.queryParallel(
        allFields,
        product,
        country
    );

    // Process results
    for (const [field, result] of Object.entries(results.results)) {
        if (result.status === 'success') {
            displayFieldResult(field, result.content);
        }
    }

    return results;
}
```

### Custom Field Selection
```javascript
// Let user select which fields to analyze
const selectedFields = [
    'safety_standards',
    'labeling_requirements',
    'import_documentation'
];

const results = await api.queryParallel(
    selectedFields,
    'Medical Device',
    'eu'
);
```

## Backend Integration

To add the modular API to your Flask app:

```python
from api_framework import register_modular_api

# In your main app.py
app = Flask(__name__)

# Register the modular API
register_modular_api(app)
```

## Testing

### Test Single Field
```bash
curl -X POST http://localhost:8080/api/field/safety_standards \
  -H "Content-Type: application/json" \
  -d '{"product":"Drone","country":"us"}'
```

### Test Parallel Query
```bash
curl -X POST http://localhost:8080/api/fields/parallel \
  -H "Content-Type: application/json" \
  -d '{
    "fields": ["safety_standards", "labeling_requirements"],
    "product": "Drone",
    "country": "us"
  }'
```

## UI Components

### Field Card
```javascript
const card = ComplianceUI.createFieldCard(
    'Safety Standards',
    {
        field: 'safety_standards',
        status: 'success',
        content: 'CE marking required...'
    }
);
document.getElementById('container').innerHTML += card;
```

### Loading Skeleton
```javascript
const skeleton = ComplianceUI.createLoadingSkeleton('Safety Standards');
```

### Progress Indicator
```javascript
const progress = ComplianceUI.createProgressIndicator(3, 8);
```

## Performance Tips

1. **Use Parallel for Multiple Fields**: When querying 3+ fields, parallel is usually fastest
2. **Cache Warming**: Pre-query common product/country combinations
3. **Field Prioritization**: Query critical fields first in progressive mode
4. **Batch Similar Products**: Query variations together to maximize cache hits

## Error Handling

```javascript
try {
    const results = await api.queryParallel(fields, product, country);
} catch (error) {
    console.error('Query failed:', error);
    // Show user-friendly error message
}

// Individual field errors
if (result.status === 'error') {
    switch (result.error) {
        case 'timeout':
            // Retry or notify user
            break;
        case 'invalid_api_key':
            // Check configuration
            break;
        default:
            // Generic error handling
    }
}
```

## Extending the Framework

### Adding New Fields

In `api_framework.py`:

```python
ComplianceFieldQuery.FIELD_PROMPTS['new_field'] = {
    "prompt": "Query prompt for {product} in {country}",
    "max_tokens": 250
}
```

In `compliance_api.js`:

```javascript
this.fields['new_field'] = 'New Field Display Name';
```

### Custom Query Logic

Extend the `ComplianceFieldQuery` class:

```python
class CustomComplianceQuery(ComplianceFieldQuery):
    @classmethod
    def query_with_regulation_lookup(cls, field, product, country):
        # Custom implementation
        pass
```

## Deployment Considerations

1. **Rate Limiting**: Implement per-user rate limits
2. **API Keys**: Store securely in environment variables
3. **Caching**: Consider Redis for production caching
4. **Monitoring**: Track query patterns and cache hit rates
5. **Scaling**: Use worker processes for parallel queries

## Future Enhancements

- WebSocket support for real-time updates
- GraphQL endpoint for flexible queries
- Batch product queries
- Webhook notifications for regulation changes
- PDF export for compliance reports
- Integration with regulatory databases

## Troubleshooting

### Slow Queries
- Check network latency
- Verify cache is working
- Reduce parallel query count
- Use progressive loading for better UX

### Missing Results
- Verify field names are correct
- Check API key validity
- Ensure product/country are supported
- Review error logs

### Cache Issues
- Clear cache if stale data appears
- Verify cache TTL settings
- Check memory usage
- Monitor cache hit rates