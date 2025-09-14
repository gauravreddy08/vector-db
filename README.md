Vector Database API — Fast, minimal, containerized. See `docs/API.md` for full endpoint reference.

### Features
- **Indexes**: Linear scan, IVF clustering, NSW graph
- **Filter search**: Exact-match metadata filters with any index
- **Auto-doc creation**: Creating a chunk without `document_id` auto-creates its `Document`
- **Thread-safe in-memory stores** with service/repository layers
- **RESTful FastAPI** with Pydantic schemas and clean DDD layout

### Project Structure
- `app/domain/`: Core entities and domain models
- `app/services/`: Business logic (libraries, documents, chunks, index/search)
- `app/repositories/`: Data access (in-memory implementations)
- `app/indexes/`: Custom vector indexes (`linear`, `ivf`, `nsw`) and filters
- `app/api/`: FastAPI routers and DI wiring
- `app/schemas/`: Request/response Pydantic models
- `app/utils/`: Embedding and helpers (e.g., k-means)
- `examples/`: `populate_db.py` dataset population script
- `docs/`: `API.md` with all endpoints

### Endpoints
See `docs/API.md` for all routes, bodies, and responses.

### Docker
Build:
```bash
docker compose build
```
Run:
```bash
docker compose up -d
```
Stop:
```bash
docker compose down
```
App serves at `http://localhost:8000` (Swagger at `/docs`).

### Populate Sample Data (via docker exec)
```bash
docker compose exec vector-db python examples/populate_db.py
```
This creates libraries for Linear/IVF/NSW, inserts chunks, and builds indexes.

### Notes
- Index params are accepted at library creation (e.g., IVF: `n_clusters`, `n_probes`; NSW knobs supported).
- Search requires `query` and `k`; optional `filters` for metadata exact matches.

