# Start Reducing Duplication - Immediate Action Plan

**Analysis Results:**
- Total duplication patterns found: **4,815**
- Database query patterns: **2,319 occurrences** (highest priority!)
- Logging patterns: **1,456 occurrences**
- Validation patterns: **295 occurrences**
- Error handling: **258 occurrences**

## 🎯 Quick Wins to Start (This Week)

### 1. Extract Common Validation Patterns (Target: -295 patterns)

**Files with most validation duplication:**
- `synapse/rest/admin/users.py`: 32 occurrences
- `synapse/rest/admin/rooms.py`: 18 occurrences
- `synapse/rest/client/register.py`: 16 occurrences
- `synapse/handlers/auth.py`: 13 occurrences

**Create:** `synapse/util/validation.py`

```python
# Common patterns to extract:
- User ID validation
- Room ID validation  
- Parameter validation (not None, not empty)
- String length validation
- Boolean validation
```

### 2. Standardize Error Responses (Target: -182 patterns)

**Files with most error duplication:**
- `synapse/handlers/auth.py`: 14 occurrences
- `synapse/handlers/e2e_keys.py`: 13 occurrences

**Create:** `synapse/util/error_handlers.py`

```python
# Common patterns:
- SynapseError(400, ...) wrappers
- Standardized error messages
- Error response formatting
```

### 3. Extract Database Query Helpers (Target: -2,319 patterns!)

**Files with most query duplication:**
- `synapse/rest/client/room.py`: 70 occurrences
- `synapse/handlers/sync.py`: 61 occurrences
- `synapse/handlers/device.py`: 54 occurrences

**Create:** `synapse/storage/util/query_helpers.py`

```python
# Common patterns:
- Pagination helpers
- Filter building
- Common WHERE clauses
- SELECT/INSERT/UPDATE wrappers
```

## 📋 Step-by-Step Implementation

### Step 1: Create Validation Utilities (TODAY)

1. Review `synapse/rest/admin/users.py` lines with validation
2. Extract repeated validation patterns to `synapse/util/validation.py`
3. Replace 32 occurrences in `users.py`
4. Apply to other files with validation duplication

### Step 2: Create Error Handler Utilities (THIS WEEK)

1. Review error patterns in `synapse/handlers/auth.py`
2. Create `synapse/util/error_handlers.py` with decorators/helpers
3. Replace repeated error handling code

### Step 3: Create Database Query Helpers (NEXT WEEK)

1. Review query patterns in `synapse/rest/client/room.py`
2. Create `synapse/storage/util/query_helpers.py`
3. Extract common query patterns
4. This will eliminate the MOST duplication (2,319 patterns!)

## 🔍 Specific Files to Refactor First

### Priority 1 (Highest Impact):
1. `synapse/rest/client/room.py` - 70 query patterns
2. `synapse/handlers/sync.py` - 61 query patterns  
3. `synapse/handlers/device.py` - 54 query patterns
4. `synapse/handlers/message.py` - 54 query patterns

### Priority 2 (Validation):
1. `synapse/rest/admin/users.py` - 32 validation patterns
2. `synapse/rest/admin/rooms.py` - 18 validation patterns
3. `synapse/rest/client/register.py` - 16 validation patterns

### Priority 3 (Error Handling):
1. `synapse/handlers/federation.py` - 11 error patterns
2. `synapse/handlers/e2e_keys.py` - 11 error patterns
3. `synapse/federation/federation_client.py` - 11 error patterns

## 📊 Expected Impact

**Week 1-2:**
- Extract validation utilities: **-295 patterns**
- Extract error handlers: **-182 patterns**
- **Total: -477 patterns (~3,000 lines)**

**Week 3-4:**
- Extract database query helpers: **-500 patterns**
- **Total: -977 patterns (~6,000 lines)**

**Week 5-8:**
- Continue database query extraction: **-1,500 patterns**
- **Total: -2,477 patterns (~15,000 lines)**

## 🚀 Next Immediate Actions

1. **Review the detailed report:**
   ```bash
   cat duplication_analysis.txt | head -200
   ```

2. **Pick ONE file to start with:**
   - Start with `synapse/rest/admin/users.py` (32 validation patterns)
   - Or start with `synapse/rest/client/room.py` (70 query patterns - bigger impact)

3. **Extract the first pattern:**
   - Identify repeated code block
   - Create utility function
   - Replace all occurrences
   - Test
   - Commit

4. **Repeat systematically**

## 💡 Key Strategy

**Focus Areas (in order):**
1. ✅ Database queries (2,319 patterns) - BIGGEST IMPACT
2. ✅ Logging patterns (1,456 patterns)
3. ✅ Validation (295 patterns) - EASIEST TO START
4. ✅ Error handling (258 patterns)

**Start Small, Build Up:**
- Don't try to fix everything at once
- Extract one pattern type at a time
- Test thoroughly after each extraction
- Track progress as you go

---

**Status:** Ready to begin
**Next File:** Choose one from Priority 1 or 2 above
**Goal:** Reduce duplication by 10% this week (1,826 lines)

