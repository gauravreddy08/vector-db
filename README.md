## Vector Database API 

Fast, minimal, containerized. See [`docs/API.md`](docs/API.md) for full endpoint reference.

### Features
- **Indexes**: Linear scan, IVF clustering, NSW graph
- **Filter search**: Exact-match metadata filters with any index
- **Auto-doc creation**: Creating a chunk without `document_id` auto-creates its `Document`
- **Thread-safe in-memory stores** with service/repository layers
- **RESTful FastAPI** with Pydantic schemas and clean DDD layout

### Technical Choices
This design follows Domain-Driven Design (DDD) principles with a modular, layered architecture that separates concerns cleanly. The repository pattern enables easy swapping of storage backends (currently in-memory, easily extensible to persistent stores), while the service layer encapsulates business logic independently of data access. The index implementations are pluggable and follow a common interface, making the system highly scalable for adding new vector search algorithms without changing existing code.

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
See [`docs/API.md`](docs/API.md) for all routes, bodies, and responses.

### To run
Build:
```bash
docker build -t vector-db .
```
Run:
```bash
docker run -d -p 8000:8000 -e COHERE_API_KEY="your_api_key_here" --name vector-db-container vector-db
```
Stop:
```bash
docker stop vector-db-container && docker rm vector-db-container
```
App serves at `http://localhost:8000` (Swagger at `/docs`).

### Populate Sample Data (via docker exec)
```bash
docker exec -it vector-db-container python examples/populate_db.py
```
This creates libraries for Linear/IVF/NSW, inserts chunks, and builds indexes.

### Notes
- Index params are accepted at library creation (e.g., IVF: `n_clusters`, `n_probes`; NSW knobs supported).
- Search requires `query` and `k`; optional `filters` for metadata exact matches.

> ###### AI Usage
> This project leverages AI for:
> - **Documentations**: API documentation, README, and code comments
> - **Testing**: Test case generation and validation
> - **Data Population**: Sample dataset creation and indexing

