---

## 🔧 Advanced Filter Operators

The vector database supports multiple filter operators for precise querying. Here are examples of all supported operators:

### Supported Operators:
- `eq` - equals (default if no operator specified)
- `ne` - not equals
- `gt` - greater than
- `gte` - greater than or equal
- `lt` - less than
- `lte` - less than or equal
- `contains` - string contains (case-insensitive)
- `in` - value in list
- `nin` - value not in list

---

## 📊 Equality Operators

### 1. Equals (eq) - Default Behavior
```json
{
  "query": "anime series",
  "k": 5,
  "filters": {
    "anime_name": "Death Note"
  }
}
```

### 2. Equals (explicit)
```json
{
  "query": "smartphone technology",
  "k": 5,
  "filters": {
    "product_name": {"eq": "iPhone 15 Pro"}
  }
}
```

### 3. Not Equals (ne)
```json
{
  "query": "AI technology",
  "k": 10,
  "filters": {
    "company": {"ne": "OpenAI"}
  }
}
```

---

## 📈 Comparison Operators

### 1. Greater Than (gt)
```json
{
  "query": "anime series",
  "k": 10,
  "filters": {
    "rating": {"gt": 8.5}
  }
}
```

### 2. Greater Than or Equal (gte)
```json
{
  "query": "Apple products",
  "k": 10,
  "filters": {
    "episodes": {"gte": 50}
  }
}
```

### 3. Less Than (lt)
```json
{
  "query": "recent anime",
  "k": 5,
  "filters": {
    "episodes": {"lt": 50}
  }
}
```

### 4. Less Than or Equal (lte)
```json
{
  "query": "completed anime",
  "k": 10,
  "filters": {
    "rating": {"lte": 9.0}
  }
}
```

---

## 📅 Date Range Filtering

### 1. After Specific Date (gt)
```json
{
  "query": "modern technology",
  "k": 10,
  "filters": {
    "release_date": {"gt": "2020-01-01"}
  }
}
```

### 2. From Specific Date (gte)
```json
{
  "query": "recent innovations",
  "k": 10,
  "filters": {
    "release_date": {"gte": "2022-01-01"}
  }
}
```

### 3. Before Specific Date (lt)
```json
{
  "query": "classic anime",
  "k": 5,
  "filters": {
    "release_date": {"lt": "2010-01-01"}
  }
}
```

### 4. Date Range Combination
```json
{
  "query": "2010s anime",
  "k": 10,
  "filters": {
    "release_date": {
      "gte": "2010-01-01",
      "lt": "2020-01-01"
    }
  }
}
```

---

## 🔍 String Operators

### 1. Contains (case-insensitive)
```json
{
  "query": "anime characters",
  "k": 10,
  "filters": {
    "genre": {"contains": "fantasy"}
  }
}
```

### 2. Studio Name Contains
```json
{
  "query": "anime production",
  "k": 5,
  "filters": {
    "studio": {"contains": "studio"}
  }
}
```

### 3. Product Name Contains
```json
{
  "query": "Apple devices",
  "k": 5,
  "filters": {
    "product_name": {"contains": "pro"}
  }
}
```

---

## 📝 List Operators

### 1. In List (in)
```json
{
  "query": "premium technology",
  "k": 10,
  "filters": {
    "company": {"in": ["OpenAI", "Anthropic", "Apple"]}
  }
}
```

### 2. Anime Genres In List
```json
{
  "query": "action anime",
  "k": 10,
  "filters": {
    "genre": {"in": ["Dark Fantasy", "Supernatural", "Adventure"]}
  }
}
```

### 3. Price Range In List
```json
{
  "query": "affordable products",
  "k": 5,
  "filters": {
    "price_range": {"in": ["budget", "mid-range"]}
  }
}
```

### 4. Not In List (nin)
```json
{
  "query": "non-Apple technology",
  "k": 10,
  "filters": {
    "company": {"nin": ["Apple"]}
  }
}
```

### 5. Exclude Specific Genres
```json
{
  "query": "anime series",
  "k": 10,
  "filters": {
    "genre": {"nin": ["Romance", "Comedy"]}
  }
}
```

---

## 🎯 Complex Multi-Operator Filters

### 1. Rating Range with Studio Filter
```json
{
  "query": "high quality anime",
  "k": 5,
  "filters": {
    "rating": {
      "gte": 8.5,
      "lte": 9.5
    },
    "studio": {"ne": "Unknown"}
  }
}
```

### 2. Recent Premium Products
```json
{
  "query": "latest technology",
  "k": 10,
  "filters": {
    "release_date": {"gte": "2022-01-01"},
    "price_range": {"in": ["premium", "ultra-premium"]},
    "company": {"ne": "Unknown"}
  }
}
```

### 3. AI Models by Company and Type
```json
{
  "query": "language models",
  "k": 5,
  "filters": {
    "company": {"in": ["OpenAI", "Anthropic"]},
    "model_type": {"eq": "Large Language Model"},
    "release_date": {"gt": "2021-01-01"}
  }
}
```

### 4. Anime Episode Count and Status
```json
{
  "query": "anime series",
  "k": 10,
  "filters": {
    "episodes": {
      "gt": 20,
      "lt": 100
    },
    "status": {"eq": "completed"},
    "rating": {"gte": 8.0}
  }
}
```

---

## 🔄 Combining Multiple Field Filters

### 1. Product Features and Specs
```json
{
  "query": "advanced smartphone",
  "k": 5,
  "filters": {
    "product_type": {"eq": "smartphone"},
    "chip": {"contains": "pro"},
    "price_range": {"ne": "budget"},
    "release_date": {"gte": "2023-01-01"}
  }
}
```

### 2. Anime by Multiple Criteria
```json
{
  "query": "popular anime",
  "k": 10,
  "filters": {
    "rating": {"gte": 8.5},
    "episodes": {"lte": 50},
    "status": {"eq": "completed"},
    "genre": {"nin": ["Comedy", "Romance"]},
    "studio": {"contains": "studio"}
  }
}
```

### 3. AI Technology Filtering
```json
{
  "query": "AI assistants",
  "k": 5,
  "filters": {
    "model_type": {"in": ["Large Language Model", "Code Generation"]},
    "company": {"ne": "Unknown"},
    "release_date": {"gt": "2020-01-01"},
    "chunk_type": {"contains": "overview"}
  }
}
```

---

## 🎨 Chunk Type Specific Filters

### 1. Overview Chunks Only
```json
{
  "query": "technology overview",
  "k": 10,
  "filters": {
    "chunk_type": {"eq": "overview"}
  }
}
```

### 2. Technical Feature Chunks
```json
{
  "query": "product features",
  "k": 5,
  "filters": {
    "chunk_type": {"contains": "features"}
  }
}
```

### 3. Exclude Specific Chunk Types
```json
{
  "query": "product information",
  "k": 10,
  "filters": {
    "chunk_type": {"nin": ["overview", "specifications"]}
  }
}
```

---

## 📊 Numeric Range Examples

### 1. Episode Count Ranges
```json
{
  "query": "anime series length",
  "k": 10,
  "filters": {
    "episodes": {
      "gte": 12,
      "lte": 26
    }
  }
}
```

### 2. Rating Thresholds
```json
{
  "query": "highly rated content",
  "k": 5,
  "filters": {
    "rating": {"gt": 9.0}
  }
}
```

---

## 🔍 Text Search with Precise Filters

### 1. Case-Insensitive Studio Search
```json
{
  "query": "anime production quality",
  "k": 5,
  "filters": {
    "studio": {"contains": "STUDIO"}
  }
}
```

### 2. Product Name Partial Match
```json
{
  "query": "Apple laptops",
  "k": 5,
  "filters": {
    "product_name": {"contains": "macbook"}
  }
}
```

### 3. AI Model Architecture
```json
{
  "query": "AI technology",
  "k": 5,
  "filters": {
    "architecture": {"contains": "transformer"}
  }
}
```

---

## 📋 Filter Operator Summary

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `eq` | Equals (default) | `"field": "value"` | Exact matches |
| `ne` | Not equals | `"field": {"ne": "value"}` | Exclusions |
| `gt` | Greater than | `"rating": {"gt": 8.0}` | Minimum thresholds |
| `gte` | Greater than or equal | `"episodes": {"gte": 12}` | Inclusive minimums |
| `lt` | Less than | `"episodes": {"lt": 100}` | Maximum limits |
| `lte` | Less than or equal | `"rating": {"lte": 9.0}` | Inclusive maximums |
| `contains` | String contains | `"genre": {"contains": "fantasy"}` | Partial text matching |
| `in` | Value in list | `"company": {"in": ["Apple", "Google"]}` | Multiple options |
| `nin` | Value not in list | `"status": {"nin": ["cancelled"]}` | Multiple exclusions |

---

## 🚀 Testing Different Index Performance

Use the same query across all three libraries to compare performance:

### Performance Test Query
```json
{
  "query": "advanced artificial intelligence technology",
  "k": 10
}
```

**Test this query against:**
1. Linear Index Library: `2c39bf37-4ff7-450b-8cca-45593c2ade97`
2. IVF Index Library: `c5485513-2d30-49f1-93ad-b744251e42cd`
3. NSW Index Library: `5dae5fa9-363a-412e-ad6a-74092f73dbfc`

**Measure:**
- Response time
- Result relevance
- Result ordering
- Memory usage

---

## 📝 Usage Tips

1. **Replace library_id** in the URL with the actual library ID you want to test
2. **Adjust k values** to test different result set sizes
3. **Mix and match filters** to test complex queries
4. **Compare results** across different index types for the same query
5. **Time the requests** to measure performance differences
6. **Test edge cases** like k=1 vs k=30 to see index behavior
7. **Use multiple operators** on the same field for range queries
8. **Combine different operators** across multiple fields for complex filtering

## 🎯 Expected Results

- **Death Note queries** should return 3 chunks about the anime
- **iPhone 15 Pro queries** should return 4 chunks about the device
- **ChatGPT queries** should return 3 chunks about the AI model
- **Cross-topic searches** should return relevant chunks from multiple categories
- **Filtered searches** should only return chunks matching the filter criteria
- **Range filters** should return chunks within the specified numeric/date ranges
- **String contains** should match partial text regardless of case
- **List operators** should include/exclude multiple values as specified

Happy testing! 🚀