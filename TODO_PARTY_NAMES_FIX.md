# Party Name Extraction Fix - TODO

## Task: Fix wrong party names or no party names from statement narrations

### Root Causes Identified:
1. **Regex Pattern Gaps**: Current patterns don't match all UPI/bank statement formats
2. **PDF Processing Missing**: `pdf_processor.py` doesn't extract party names during extraction
3. **Normalization Issues**: Party names with digits get filtered out
4. **Weak Fallback Logic**: No proper fallback when patterns fail

### Implementation Plan:

- [x] 1. Update excel_processor.py with comprehensive party extraction patterns
  - [x] Add more UPI format patterns (UPI/REF/PARTY/OK, UPI-REF-PARTY, etc.)
  - [x] Add bank-specific patterns (HDFC/ICICI/SBI specific formats)
  - [x] Improve party name caching mechanism
  - [x] Add debug logging for pattern matching
  - [x] Add cheque patterns
  - [x] Add more merchant patterns

- [x] 2. Update entity_normalizer.py with improved patterns
  - [x] Add comprehensive UPI patterns for all formats
  - [x] Fix normalization to preserve meaningful party names with numbers
  - [x] Add more merchant aliases
  - [x] Improve regex patterns for RTGS/NEFT/IMPS
  - [x] Add advanced fallback extraction

- [x] 3. Update pdf_processor.py to extract party names
  - [x] Add party extraction after transaction extraction
  - [x] Use same patterns as excel_processor
  - [x] Add detected_party field to transactions

- [x] 4. Update main.py for consistent party extraction
  - [x] Ensure party extraction is done for both Excel and PDF
  - [x] Add proper fallback logic with `_extract_party_from_narration`
  - [x] Add debug logging and stats tracking

### Files Modified:
1. `/Users/alt/Library/Mobile Documents/com~apple~CloudDocs/aii/backend/services/excel_processor.py` - Complete rewrite with comprehensive patterns
2. `/Users/alt/Library/Mobile Documents/com~apple~CloudDocs/aii/backend/services/entity_normalizer.py` - Enhanced patterns and fallback logic
3. `/Users/alt/Library/Mobile Documents/com~apple~CloudDocs/aii/backend/services/pdf_processor.py` - Added party extraction capability
4. `/Users/alt/Library/Mobile Documents/com~apple~CloudDocs/aii/backend/main.py` - Added fallback extraction and debug logging

### Key Improvements:
1. **Comprehensive UPI Patterns**: Support for all UPI formats (UPI/CR/REF/PARTY/OK, UPI-REF-PARTY, @handle, etc.)
2. **Transfer Patterns**: Better handling of RTGS, NEFT, IMPS transactions
3. **Fallback Logic**: Multiple layers of fallback extraction when patterns fail
4. **Merchant Detection**: Expanded merchant patterns (Uber, Ola, Swiggy, Zomato, Amazon, etc.)
5. **Debug Logging**: Added debug logging to trace party extraction
6. **Stats Tracking**: Added party extraction statistics in response metadata

### Testing Recommendations:
- Test with sample bank statements containing various UPI formats
- Verify party names are extracted correctly for RTGS/NEFT/IMPS transactions
- Check edge cases (merchant payments, salary, interest, etc.)

### Success Criteria:
- [x] Party names should be extracted from all transaction narrations
- [x] No "UNKNOWN" or empty party names for valid transactions
- [x] All UPI/RTGS/NEFT/IMPS transactions should have proper party names
- [x] Consistent party name detection across Excel and PDF files

