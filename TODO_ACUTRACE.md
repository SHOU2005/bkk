# AcuTrace - Party Ledger & Fund Flow Intelligence Transformation

## Vision
Transform AcuTrace into a **party-centric money movement investigator** focused on XLS/XLSX only uploads with advanced Party Ledger and Fund Flow analysis.

---

## ✅ COMPLETED ITEMS (All Major Tasks Done!)

### Phase 1: Backend Core - COMPLETE ✅
- [x] ✅ **1.1 requirements.txt** - Already clean (No PDF/ML dependencies)
- [x] ✅ **1.2 excel_processor.py** - ENHANCED with:
  - AI party name extraction from narration using pattern matching
  - Multiple sheet handling
  - Column auto-detection
  - Spelling tolerance and normalization
  - UPI handle detection
  - Merchant pattern recognition
  - Transfer detection

- [x] ✅ **1.3 entity_normalizer.py** - ENHANCED with:
  - Advanced party name extraction
  - UPI handle detection and clustering
  - Merchant name normalization
  - Fuzzy matching for similar party names (SequenceMatcher)
  - Auto-merge similar entities
  - Cross-reference linking between parties
  - Phone number pattern matching

- [x] ✅ **1.5 main.py** - COMPLETELY UPDATED:
  - Changed from "FinSecure AI" to "AcuTrace"
  - Party ledger focus instead of fraud detection
  - New endpoints: `/api/party/{party_name}`, `/api/fund-flow/chains`, `/api/party-ledger`, `/api/relations`
  - Auto-merge similar entities feature
  - Cross-file party detection
  - Fund flow chain building

### Phase 2: Frontend - Landing Page
- [x] ✅ All 6 tasks complete (from earlier session)

### Phase 3: Frontend - Analysis Page
- [x] ✅ All 8 tasks complete (from earlier session)

### Phase 4: Frontend - Results Dashboard  
- [x] ✅ All tasks complete (from earlier session)

### Phase 5: Premium UI Components
- [x] ✅ PartyLedgerTable - Inline version in ResultsPage
- [x] ✅ FundFlowChainDisplay - Inline version in ResultsPage
- [x] ✅ FilterBar - Simplified to 4 filters in ResultsPage

### Phase 6: Cleanup - PARTIAL ✅
- [x] ✅ Fraud detection code removed from main.py
- [x] ✅ Fraud detection removed from frontend results
- [x] ✅ PDF references removed from frontend
- [x] ✅ Risk scoring removed from results

### Phase 7: Testing & Verification - READY TO TEST
- [ ] ⏳ Need to run backend and frontend to verify

---

## 📁 Updated File Structure

```
backend/
├── main.py                      # ✅ Updated API (XLS-only, party ledger focus)
├── requirements.txt             # ✅ Already clean
├── services/
│   ├── excel_processor.py       # ✅ Enhanced XLS processing + AI party extraction
│   ├── entity_normalizer.py     # ✅ Enhanced UPI clustering + fuzzy matching
│   ├── fund_flow_chain_builder.py # ✅ Already done previously
│   ├── transaction_categorizer.py # Keep as-is
│   ├── export_service.py        # Keep as-is
│   ├── pdf_processor.py         # To be removed (not imported in main.py)
│   ├── fraud_detector.py        # To be removed (not imported in main.py)
│   ├── report_generator.py      # To be removed (not imported in main.py)
│   └── file_processor.py        # To be removed (replaced by excel_processor)
└── tests/                       # Update tests for new API

frontend/
├── src/
│   ├── pages/
│   │   ├── LandingPage.jsx      # ✅ Already done
│   │   ├── AnalysisPage.jsx     # ✅ XLS upload only
│   │   └── ResultsPage.jsx      # ✅ Party ledger focus
│   ├── components/
│   │   └── CategoryChip.jsx     # Keep
│   └── utils/
│       └── transactionFilters.js # Simplified filters
└── package.json
```

---

## 🚀 API Endpoints Available

### Core Analysis
- `POST /api/analyze` - Single XLS file analysis
- `POST /api/analyze/multi` - Multiple XLS files with cross-file correlation

### Party Ledger
- `GET /api/party-ledger` - Get complete party ledger summary
- `GET /api/party/{party_name}` - Get details for specific party

### Fund Flow
- `GET /api/fund-flow/chains` - Get all fund flow chains
- `GET /api/relations` - Get party relationship mapping

### Export
- `POST /api/export/json` - Export analysis as JSON

### Utility
- `GET /` - API root
- `GET /health` - Health check
- `GET /api/report/{report_id}` - Report generation

---

## 📊 Key Features Implemented

### AI Party Detection
- Pattern matching for UPI handles (@handle, UPI/xxx)
- Merchant recognition (Amazon, Swiggy, Zomato, etc.)
- Bank transfer detection (NEFT, IMPS, RTGS)
- Fuzzy matching with similarity threshold 0.75
- Auto-merge similar entities

### Fund Flow Chains
- Cross-party credit/debit relation mapping
- Amount matching (±2 INR tolerance)
- Date proximity matching (±1 day)
- Confidence scoring for matches
- Cross-file correlation

### Party Ledger
- Auto-generated from transaction narration
- Credit/Debit totals per party
- Net flow calculation
- Transaction count
- UPI handle tracking

### Frontend UI
- XLS/XLSX only drag-drop upload
- Multi-file support (2-20+ files)
- 4-tab results: Overview, Party Ledger, Fund Flows, Transactions
- Simplified filter system (Credit, Debit, Transfer, UPI)
- Party search functionality
- QR code sharing

---

## 🔄 Remaining Cleanup Tasks (Optional)

### Files to Delete (Not Referenced in main.py Anymore)
- `backend/services/pdf_processor.py`
- `backend/services/fraud_detector.py`
- `backend/services/report_generator.py`
- `backend/services/file_processor.py`
- `frontend/src/components/FraudExplanationBox.jsx`
- `frontend/src/components/RiskIndicators.jsx`
- `frontend/src/components/CorrelationTable.jsx`
- `frontend/src/components/CorrelationChainsTable.jsx`
- `frontend/src/components/StatsGrid.jsx`
- `frontend/src/components/StatsCard.jsx`
- `frontend/src/components/FilterPills.jsx`

---

## ✅ VERIFICATION MESSAGE

After successful build/update, the system should output:

```
✅ AcuTrace Party Ledger & Fund Flow Intelligence Platform Ready!

Features:
- ✅ XLS/XLSX Only Upload (2-20+ files)
- ✅ AI Party Detection from Narration
- ✅ Cross-Party Credit/Debit Relations
- ✅ Fund Flow Chain Builder
- ✅ Auto-Generated Party Ledger
- ✅ Premium Investigation Dashboard
- ✅ JSON / PDF / QR Export
- ✅ UPI Handle Clustering
- ✅ Fuzzy Matching for Entities
- ✅ Cross-File Correlation

All transactions fetched accurately from uploaded XLS files. 
Party relations detected from narration. 
Fund flow chains built correctly. 
Only XLS upload is supported, PDF upload is removed.
```

---

## 🎯 QUICK START

1. Start Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. Start Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open http://localhost:5173
4. Upload XLS/XLSX files
5. View party ledger and fund flow analysis
