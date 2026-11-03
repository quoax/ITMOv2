Draft Spec: Pagination and Server-Side Sorting (Subscribers)

Context
- This draft follows the project Constitution (SpecKit). Lists must respond with JSON { items, total }, enforce query params offset, limit, sort, and ensure stable sorting with a tie-break by primary key id asc. PostgreSQL is the DB. Offset/limit is permitted when max limit is enforced.

Scope
- Feature: Add pagination and server-side sorting to GET /api/subscribers.
- Sort key: created_at with secondary tie-break by id asc to guarantee stability.

Database Algorithm
Inputs
- offset: integer, default 0, min 0.
- limit: integer, default 20, min 1, max 100.
- sort: string, one of asc|desc, default asc. Applies to created_at only.

Validation
- If offset < 0 -> 400 VALIDATION_ERROR.
- If limit < 1 or limit > 100 -> 400 VALIDATION_ERROR (message must indicate allowed range).
- If sort not in {asc, desc} -> 400 VALIDATION_ERROR.

Query Construction
- Filtering: none mandated for this feature; if filters exist elsewhere, total must reflect them. Deleted or soft-deleted rows must be excluded by existing invariants (e.g., WHERE deleted_at IS NULL) if applicable to the model.
- Count query (total):
  SELECT COUNT(*)
  FROM subscribers s
  -- optional filters
  ;

- Page query (stable ordering):
  -- Direction placeholder expands to ASC or DESC depending on sort; tie-breaker id is always ASC per Constitution
  SELECT s.id,
         s.email,
         s.created_at
  FROM subscribers s
  -- optional filters
  ORDER BY s.created_at {ASC|DESC}, s.id ASC
  LIMIT $1 OFFSET $2;

Notes
- Stability: For equal created_at, rows are further ordered by id ASC, ensuring deterministic, stable results across requests.
- Indexing: Create a composite B-Tree index to support both directions: CREATE INDEX IF NOT EXISTS idx_subscribers_created_at_id ON subscribers (created_at, id);
  PostgreSQL can scan this index in reverse for DESC without a separate index.
- Performance: Offset pagination has O(n) skip cost; acceptable under max limit and moderate offsets. For very large tables or deep pagination, consider a future enhancement to keyset pagination (SHOULD per Constitution) while preserving the API.
- Concurrency: New inserts/updates may cause page drift when using offset; clients should not rely on immutable page boundaries between requests. ETag/Last-Modified may be considered later for cache/consistency (SHOULD).
- Transactions: Each request executes read-only statements; ensure appropriate statement_timeout and use of context cancellation.

Business Rules
- Response format MUST be exactly: { "items": [...], "total": <non-negative integer> } with no extra top-level properties.
- items is an array of subscribers with the following public fields for this endpoint: id (string), email (string), created_at (RFC3339 string).
- Sorting applies to created_at; sort=asc sorts oldest to newest; sort=desc sorts newest to oldest; ties break by id asc.
- total reflects the number of rows matching filters (if any), not affected by offset/limit.
- Defaults: offset=0, limit=20, sort=asc.
- Bounds: 0 <= offset, 1 <= limit <= 100. Requests with limit > 100 MUST be rejected with 400.
- Errors follow the unified format: { "error": { "code": string, "message": string, "details": object } }. For 400, details SHOULD map to offending fields.
- HTTP status codes: 200 for success; 400 for validation errors; 500 for internal errors. Content-Type application/json; charset=utf-8.
- Backward-compatibility: none required; this is additive behavior consistent with Constitution.

OpenAPI (Swagger) YAML
```yaml
openapi: 3.0.3
info:
  title: Subscribers API
  version: 0.1.0
  description: Server-side pagination and sorting for subscribers list.
servers:
  - url: / # relative; deployment may add host/basePath
paths:
  /api/subscribers:
    get:
      operationId: listSubscribers
      tags: [Subscribers]
      summary: List subscribers with pagination and sorting
      description: >-
        Returns a paginated list of subscribers. Sorting is applied on created_at with a
        stable tie-breaker by id asc.
      parameters:
        - in: query
          name: offset
          schema:
            type: integer
            minimum: 0
            default: 0
          description: Number of rows to skip.
        - in: query
          name: limit
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
          description: Page size (max 100).
        - in: query
          name: sort
          schema:
            type: string
            enum: [asc, desc]
            default: asc
          description: Sort direction for created_at.
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListSubscribersResponse'
              examples:
                ok:
                  value:
                    items:
                      - id: "a2e8b5d1-7f3c-4c12-9f21-0f4be7c1d9a1"
                        email: user@example.com
                        created_at: '2026-10-29T12:34:56Z'
                    total: 42
        '400':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                badLimit:
                  value:
                    error:
                      code: VALIDATION_ERROR
                      message: limit must be between 1 and 100
                      details:
                        limit: must be between 1 and 100
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
              examples:
                internal:
                  value:
                    error:
                      code: INTERNAL_ERROR
                      message: unexpected server error
                      details: {}
components:
  schemas:
    Subscriber:
      type: object
      additionalProperties: false
      properties:
        id:
          type: string
          description: Subscriber primary key (UUID or string identifier)
        email:
          type: string
          format: email
        created_at:
          type: string
          format: date-time
      required: [id, email, created_at]
    ListSubscribersResponse:
      type: object
      additionalProperties: false
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Subscriber'
        total:
          type: integer
          minimum: 0
      required: [items, total]
    ErrorObject:
      type: object
      additionalProperties: false
      properties:
        code:
          type: string
          description: Machine-readable error code (e.g., VALIDATION_ERROR)
        message:
          type: string
        details:
          type: object
          additionalProperties: true
      required: [code, message]
    ErrorResponse:
      type: object
      additionalProperties: false
      properties:
        error:
          $ref: '#/components/schemas/ErrorObject'
      required: [error]
```

Notes for Implementation
- Service layer must accept context.Context and perform parameter validation before repository calls.
- Repository must use pgx or database/sql with pooled connections, propagate context for cancellation, and apply LIMIT/OFFSET exactly as validated.
- Ensure SQL time zone handling is UTC for created_at comparisons; return RFC3339 timestamps.
- Add EXPLAIN/ANALYZE during development to verify index usage on ORDER BY created_at, id.
