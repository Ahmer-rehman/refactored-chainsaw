# Code Duplication Reduction Plan

**Current Status:**
- Total Lines of Code: 248,546
- Duplicated Lines: 18,261 (7.3% duplication rate)
- **TARGET: ZERO DUPLICATION (0 lines)**
- **Goal: Eliminate all 18,261 duplicated lines**

## Strategy Overview

### Phase 1: Identification & Analysis

#### 1.1 Use SonarQube to Identify Duplications
```bash
# SonarQube will show:
# - Exact duplicate code blocks
# - Similar code blocks (>70% similarity)
# - Files with most duplication
```

#### 1.2 Common Duplication Patterns in Synapse

Based on codebase analysis, common patterns include:

1. **Error Handling Patterns**
   - Repeated try-except blocks with similar error handling
   - Similar error message formatting
   - Common exception wrapping logic

2. **Validation Logic**
   - User ID validation
   - Room ID validation
   - Parameter validation
   - JSON schema validation

3. **Database Query Patterns**
   - Similar SELECT queries with slight variations
   - Common WHERE clause patterns
   - Repeated pagination logic

4. **API Response Formatting**
   - Similar JSON response construction
   - Common pagination response formats
   - Error response formatting

5. **Logging Patterns**
   - Repeated log message formatting
   - Similar debug/info/error logging patterns

### Phase 2: Refactoring Strategies

#### 2.1 Extract Utility Functions

**Target Areas:**
- `synapse/util/` - Add shared utilities
- `synapse/api/utils.py` - API-specific utilities
- `synapse/storage/util.py` - Database utilities

**Examples:**

**Before (Duplicated):**
```python
# In multiple files
if not user_id or not isinstance(user_id, str):
    raise SynapseError(400, "Invalid user ID")
if not user_id.startswith("@") or ":" not in user_id:
    raise SynapseError(400, "Invalid user ID format")
```

**After (Refactored):**
```python
# In synapse/util/validation.py
def validate_user_id(user_id: str) -> UserID:
    """Validate and return UserID object."""
    if not user_id or not isinstance(user_id, str):
        raise SynapseError(400, "Invalid user ID")
    try:
        return UserID.from_string(user_id)
    except Exception:
        raise SynapseError(400, "Invalid user ID format")
```

#### 2.2 Create Decorators for Common Patterns

**Error Handling Decorator:**
```python
# synapse/util/decorators.py
from functools import wraps
from synapse.api.errors import SynapseError

def handle_api_errors(default_code: int = 500):
    """Decorator to handle common API errors."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SynapseError:
                raise
            except Exception as e:
                logger.exception("Unexpected error in %s", func.__name__)
                raise SynapseError(default_code, str(e))
        return wrapper
    return decorator
```

#### 2.3 Extract Base Classes

**For Similar REST Endpoints:**
```python
# synapse/rest/base.py
class BaseRestServlet(RestServlet):
    """Base class with common REST patterns."""
    
    def parse_json_object_from_request(self, request):
        # Common JSON parsing logic
        pass
    
    def respond_with_json(self, request, response, code=200):
        # Common JSON response logic
        pass
```

#### 2.4 Create Shared Query Builders

**Database Query Patterns:**
```python
# synapse/storage/query_builder.py
class QueryBuilder:
    """Builder for common database query patterns."""
    
    @staticmethod
    def select_from_table(table: str, columns: List[str]):
        # Common SELECT pattern
        pass
    
    @staticmethod
    def paginate_query(query: str, limit: int, offset: int):
        # Common pagination pattern
        pass
```

### Phase 3: Implementation Plan

#### Priority 1: High-Impact Areas (Estimated 40% reduction)

1. **Error Handling** (~3,000 lines)
   - Extract common error handling patterns
   - Create error handler utilities
   - Standardize error responses

2. **Validation Logic** (~2,500 lines)
   - Create validation utility module
   - Extract all validation functions
   - Standardize validation error messages

3. **Database Patterns** (~2,000 lines)
   - Create query builder utilities
   - Extract common query patterns
   - Standardize pagination logic

#### Priority 2: Medium-Impact Areas (Estimated 35% reduction)

4. **API Response Formatting** (~2,000 lines)
   - Extract response formatting functions
   - Standardize pagination responses
   - Create response builder utilities

5. **Logging Patterns** (~1,500 lines)
   - Extract logging utilities
   - Standardize log message formats
   - Create structured logging helpers

#### Priority 3: Low-Impact Areas (Estimated 25% reduction)

6. **Configuration Parsing** (~1,500 lines)
   - Extract common config parsing patterns
   - Create config validation utilities

7. **File I/O Operations** (~1,000 lines)
   - Extract file reading/writing utilities
   - Standardize file handling patterns

### Phase 4: Tools & Automation

#### 4.1 Code Analysis Tools

```bash
# Install code duplication detection tools
pip install pymetrics
pip install clone_digger

# Run analysis
pymetrics synapse/
clone_digger --lang python synapse/
```

#### 4.2 SonarQube Configuration

Update `sonar-project.properties`:
```properties
# Enable duplication detection
sonar.cpd.python.minimumtokens=50
sonar.cpd.exclusions=**/*test*.py,**/*__pycache__/**
```

#### 4.3 Automated Refactoring Tools

- **Rope**: Python refactoring library
- **Bowler**: Safe refactoring tool by Facebook
- **Autoflake**: Remove unused imports/variables

### Phase 5: Execution Steps

#### Step 1: Baseline Measurement (Week 1)
1. Run SonarQube analysis to get detailed duplication report
2. Identify top 20 files with most duplication
3. Create prioritized list of duplication blocks

#### Step 2: Quick Wins (Weeks 2-3)
1. Extract obvious utility functions (validation, formatting)
2. Create shared error handlers
3. Extract common constants/enums
4. **Target: Reduce by 3,000-4,000 lines**

#### Step 3: Systematic Refactoring (Weeks 4-8)
1. Refactor error handling patterns
2. Extract validation logic
3. Standardize database query patterns
4. **Target: Reduce by 6,000-8,000 lines**

#### Step 4: Advanced Refactoring (Weeks 9-12)
1. Create base classes for similar components
2. Extract decorators for common patterns
3. Refactor API response patterns
4. **Target: Reduce by 4,000-5,000 lines**

#### Step 5: Final Cleanup (Week 13-14)
1. Remove remaining small duplications
2. Verify all tests pass
3. Update documentation
4. **Target: Reduce by 1,000-2,000 lines**

### Phase 6: Best Practices

#### 6.1 Preventing Future Duplication

1. **Code Review Guidelines:**
   - Check for similar patterns before merging
   - Suggest extraction of repeated code
   - Use shared utilities when available

2. **Linting Rules:**
   - Add duplication checks to CI/CD
   - Set SonarQube quality gate for duplication
   - Review duplication metrics in PRs

3. **Documentation:**
   - Document available utility functions
   - Create examples of common patterns
   - Maintain utility function index

#### 6.2 Refactoring Guidelines

1. **Always:**
   - Write tests before refactoring
   - Ensure backward compatibility
   - Update related documentation
   - Run full test suite after changes

2. **Avoid:**
   - Over-abstracting (premature optimization)
   - Creating too many abstraction layers
   - Breaking existing APIs
   - Refactoring without tests

### Expected Outcomes

**Short-term (3 months):**
- Reduce duplication from 18,261 to ~6,000 lines (67% reduction)
- Extract all common utilities
- Establish zero-duplication patterns

**Medium-term (6 months):**
- Reduce duplication to <1,000 lines (95% reduction)
- Eliminate all major duplication blocks
- Refactor remaining small duplications

**Long-term (12 months):**
- **ACHIEVE ZERO DUPLICATION (0 lines)**
- All code follows DRY (Don't Repeat Yourself) principle
- Comprehensive utility library for all common patterns

### Monitoring & Metrics

1. **Weekly Metrics:**
   - Total duplicated lines
   - Duplication percentage
   - Number of duplication blocks
   - Files with highest duplication

2. **Quality Gates:**
   - No new duplication >100 lines
   - Overall duplication <5%
   - All utilities have tests
   - Documentation up to date

## Next Steps

1. **Immediate Actions:**
   - [ ] Run SonarQube detailed duplication analysis
   - [ ] Identify top 10 files with most duplication
   - [ ] Create utility module structure
   - [ ] Set up duplication tracking in CI/CD

2. **This Week:**
   - [ ] Extract validation utilities
   - [ ] Create error handler utilities
   - [ ] Refactor 3-5 highest duplication files

3. **This Month:**
   - [ ] Complete Priority 1 refactoring
   - [ ] Reduce duplication by 30%+
   - [ ] Establish refactoring patterns

---

**Last Updated:** 2025-01-27
**Status:** Planning Phase

