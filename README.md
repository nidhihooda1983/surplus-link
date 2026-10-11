# SurplusLink Hyperlocal Lead Generation Engine

Automated B2B lead generation engine for the **SurplusLink** platform. Continuously discovers nearby commercial buyers for surplus inventory using Supabase and SerpApi Google Local.

---

## Workflow Execution Loop

```
┌────────────────────────────────────────────────────────┐
│ 1. Monitor Supabase 'listings' table                   │
│    (Filters rows where status = 'Available')           │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Extract Listing Metadata                            │
│    ('item_name', 'category', 'location_lat', 'lng')    │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Formulate Targeted Google Local Query               │
│    (Determines high-conversion commercial buyer types) │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. Execute SerpApi Google Local Search                 │
│    (Computes Haversine distance, ranks top 3 < 5km)    │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 5. Insert Discovered Leads into 'scraped_leads'        │
│    (Linked via 'listing_id', lead_status='Discovered') │
└────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
SurplusLink-Engine/
├── index.html            # Standalone B2B Frontend Dashboard (Tailwind + Leaflet OSM)
├── .env                  # Live environment variables & credentials
├── .env.example          # Template environment file
├── requirements.txt      # Python dependencies
├── schema.sql            # Supabase SQL table definitions & indices
├── config.py             # Config loader & placeholder validator
├── query_formulator.py   # Rule-based commercial buyer query generator
├── search_service.py     # SerpApi Google Local search & distance ranker
├── db_service.py         # Supabase client & fallback simulator
├── engine.py             # Main workflow loop orchestrator
├── main.py               # CLI entrypoint
└── tests/                # Automated pytest suite
    ├── test_query_formulator.py
    ├── test_search_service.py
    └── test_engine.py
```

---

## Setup & Configuration

### 1. Database Setup in Supabase
Run the provided [`schema.sql`](schema.sql) in your **Supabase Dashboard -> SQL Editor**:
- Creates `listings` table (item details, coordinates, status).
- Creates `scraped_leads` table (business name, address, phone, lat/lng, `lead_status = 'Discovered'`).
- Sets up foreign keys and performance indices.

### 2. Configure Credentials in `.env`
Edit the `.env` file with your real tokens:

```ini
# Supabase Project URL & Key (Dashboard -> Settings -> API)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-service-role-or-anon-key

# SerpApi Key (https://serpapi.com/manage-api-key)
SERPAPI_KEY=your_serpapi_api_key

# Engine Settings
SEARCH_RADIUS_KM=5.0
MAX_LEADS_PER_LISTING=3
POLL_INTERVAL_SECONDS=5
```

> **Note:** If `.env` contains placeholder brackets (e.g. `[Your SerpApi Token]`), the engine automatically runs in **simulation / mock mode**, allowing you to test the complete pipeline safely without consuming API credits or erroring out.

---

## Running the Web Frontend Dashboard

The project includes a standalone, zero-dependency B2B user interface ([`index.html`](index.html)) built with Tailwind CSS and an interactive OpenStreetMap component layer.

To run it locally:
```powershell
# Open directly in browser, or serve locally with Python:
python -m http.server 8080
```
Open **`http://localhost:8080`** in your browser.

- **Post Surplus Items:** Use the Seller Form to submit inventory. Drag the pin or click on the OpenStreetMap layer to set coordinates.
- **Direct Supabase Integration:** Uses standard browser `fetch()` to push to Supabase REST endpoints (`/rest/v1/listings`) and continuously polls for new buyer leads (`/rest/v1/scraped_leads`).
- **Buyer Outreach:** Click "Call Commercial Buyer" (`tel:`) or toggle status to "Contacted" (`PATCH` request).
- **Configure Credentials:** Click **Supabase Live Connection** in the header to update your live Supabase URL and Anon key without changing code.

---

## Running the Python Lead Generation Engine

### Run the Continuous Monitoring Loop (Live Daemon)
```bash
python main.py
```

### Run a Single Iteration (For Test or Cron)
```bash
python main.py --once
```

### Insert a Sample Test Listing
```bash
python main.py --seed-test --once
```

### Inspect Configuration Status
```bash
python main.py --status
```

### Run the Test Suite
```bash
python -m pytest -v
```
