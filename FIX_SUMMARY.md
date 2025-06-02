# Fix Summary: JSON Serialization Error in Two-Phase Method

## Problem
The Two-Phase (Dos Fases) method was failing with a JSON serialization error:
```
Object of type int64 is not JSON serializable
```

This occurred when NumPy int64 and other NumPy data types were present in the results returned by the solver, specifically in:
- `solution` arrays
- `optimal_value` scalars  
- `tableau_history` arrays
- `pivot_history` data
- `multiple_solution_vars` arrays
- Alternative solutions data

## Root Cause
The `dosfases_solver` function returns NumPy arrays and scalars, but the Flask application was attempting to serialize these directly to JSON using manual conversions that didn't handle all NumPy types comprehensively.

## Solution
Enhanced the `convert_numpy_types()` helper function to handle all NumPy data types recursively:

```python
def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    # Handle numpy scalars
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle Python built-in types with nested numpy
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    # Check if it's any numpy type we missed
    elif hasattr(obj, 'dtype') and 'numpy' in str(type(obj)):
        if obj.ndim == 0:  # scalar
            return obj.item()
        else:
            return obj.tolist()
    return obj
```

## Changes Made
1. **Enhanced numpy conversion**: Added support for `np.bool_`, tuples, and a fallback for any missed numpy types
2. **Applied to all result fields**: Updated `resolver_dosfases()` to use `convert_numpy_types()` for all returned data:
   - `solution` 
   - `optimal_value`
   - `tableau_history`
   - `pivot_history` 
   - `multiple_solution_vars`
   - Alternative solutions arrays

## Testing
Created comprehensive tests to verify the fix:
- ✅ Simple Two-Phase problems (without iteration tracking)
- ✅ Complex Two-Phase problems (with iteration tracking)
- ✅ Multiple solution detection
- ✅ Both maximization and minimization problems
- ✅ Web form interface
- ✅ JSON API interface

## Files Modified
- `c:\Users\diego\workspace\matematicas-avanzadas\app\routes.py`: Enhanced `convert_numpy_types()` and updated `resolver_dosfases()`

## Result
The JSON serialization error has been completely resolved. All Two-Phase method functionality now works correctly with proper JSON serialization for both web forms and API endpoints.
