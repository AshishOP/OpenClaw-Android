# Development Execution Standard: Test-Driven Development Workflow

> **Status**: ACTIVE  
> **Source**: Claude Skills Ecosystem Analysis (Dec 2025)  
> **Trigger**: Building or implementing any code feature

---

## Philosophy

> "Write the test first. Watch it fail. Then make it pass."

TDD inverts the natural impulse to code-first. By defining success criteria upfront, implementation becomes verification-driven rather than hope-driven.

---

## Trigger Conditions

- [ ] User says "build X", "implement Y", "create Z"
- [ ] Any code generation request
- [ ] Feature development task
- [ ] Bug fix with unclear scope

---

## Structure

### Phase A: Spec Extraction

Before writing any code, extract specifications:

1. **Ask**: "What should the input be?"
2. **Ask**: "What should the output be?"
3. **Ask**: "What edge cases should be handled?"
4. **Generate**: 3-5 concrete test cases

**Output**: Test specification document.

---

### Phase B: Test Writing

Write tests FIRST:

```python
# Example structure
def test_happy_path():
    """Primary use case works correctly."""
    assert function(valid_input) == expected_output

def test_edge_case_empty():
    """Handles empty input gracefully."""
    assert function([]) == default_value

def test_edge_case_invalid():
    """Raises appropriate error for invalid input."""
    with pytest.raises(ValueError):
        function(invalid_input)

def test_boundary():
    """Handles boundary conditions."""
    assert function(max_value) == expected_boundary_output
```

---

### Phase C: Fail Confirmation

**Run tests → Confirm FAIL**

This is critical. If tests pass before implementation, either:

- Tests are wrong
- Feature already exists
- Tests are not testing what you think

**Expected output**: All tests RED.

---

### Phase D: Implementation

Write minimum code to pass tests:

1. Focus on one test at a time
2. Make it pass
3. Move to next test
4. Refactor only after all pass

**Expected output**: All tests GREEN.

---

### Phase E: Edge Case Expansion

After basic tests pass:

1. Add 2-3 more edge cases
2. Run tests → Some may FAIL
3. Iterate implementation
4. Repeat until comprehensive

---

### Phase F: Refactor

With all tests passing:

1. Clean up implementation
2. Improve readability
3. Optimize performance
4. **Run tests after each change** to ensure no regression

---

## TDD Checklist

- [ ] Spec extracted from user requirements
- [ ] Test cases written BEFORE implementation
- [ ] Tests confirmed to FAIL initially
- [ ] Implementation passes all tests
- [ ] Edge cases covered
- [ ] Refactoring complete, tests still pass

---

## Example Workflow

```
User: Build a function to validate Singapore NRIC numbers.

Phase A - Spec:
- Input: String (NRIC number)
- Output: Boolean (valid/invalid)
- Edge cases: Empty, wrong length, invalid checksum, S vs T vs F vs G prefix

Phase B - Tests:
- test_valid_nric_s_prefix → True
- test_valid_nric_t_prefix → True
- test_invalid_checksum → False
- test_wrong_length → False
- test_empty_string → False

Phase C - Fail:
→ All 5 tests FAIL (function not implemented)

Phase D - Implement:
→ Write validate_nric() function
→ 5/5 tests PASS

Phase E - Expand:
- test_lowercase_input → Should work? Add.
- test_with_spaces → Should strip? Add.
→ 2 new tests FAIL → Update implementation

Phase F - Refactor:
→ Clean up regex, add docstring
→ 7/7 tests PASS
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Code first, test later** | Tests become verification, not specification | Force test-first discipline |
| **Tests that always pass** | No validation of behavior | Confirm FAIL before implement |
| **Testing implementation, not behavior** | Brittle tests | Test outcomes, not internals |
| **Skipping edge cases** | Production bugs | Mandatory edge case phase |

---

## Integration Points

- Use with any code generation request
- Combine with [Protocol 170]() for complex implementations
- Log to session for calibration

---

## Tags

# protocol #tdd #testing #development #workflow #stealable
