# TODO: Integrate Database-Driven Beat Management and Stock Control

## Steps to Complete

1. **Update server.py with new API endpoints**:
   - [x] Add `/api/beats` endpoint to fetch available beats from database
   - [x] Add `/api/check_stock/<beat_name>` endpoint to verify beat availability
   - [x] Add `/api/mark_sold/<beat_name>` endpoint to mark beats as sold
   - [x] Update `/api/download/<transaction_id>` endpoint to require authentication and verify ownership

2. **Update frontend to load beats dynamically**:
   - [x] Modify `index.html` to load beats from API instead of hardcoded HTML
   - [x] Update `script.js` to fetch beats from `/api/beats` and populate the track list
   - [x] Add stock checking before allowing purchase in `buyBeat` function
   - [x] Add error handling for unavailable beats

3. **Update checkout.js to load beat data from API**:
   - [x] Replace static `beatData` object with dynamic loading from `/api/beats`
   - [x] Add fallback to static data if API fails
   - [x] Update event listeners to load data asynchronously

4. **Database integration**:
   - [x] Ensure beats table exists with columns: id, name, price, genre, image_path, file_path, stock, sold, sold_date, buyer_email
   - [x] Populate database with initial beat data

5. **Verify changes**:
   - [x] Test dynamic beat loading on homepage
   - [x] Test stock checking before purchase
   - [x] Test checkout page with API-loaded data
   - [x] Test download endpoint with authentication
