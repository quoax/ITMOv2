# E2E Results: Pagination & Sort

## Success Scenarios

- Page1 status=200, items=2, total=6
- Page2 status=200, items=2, total=6
- Desc status=200, first=2026-11-02T11:19:18Z.., total=6

## Validation Errors

- limit>100 => 400, code=VALIDATION_ERROR details={'limit': 'must be between 1 and 100'}
- offset<0 => 400, code=VALIDATION_ERROR details={'offset': 'must be >= 0'}
- sort invalid => 400, code=VALIDATION_ERROR details={'sort': 'must be one of asc, desc'}

## Edge Conditions

- offset beyond total => 200, items=0, total=6

## Internal Error

- simulated internal error => 500, code=INTERNAL_ERROR
