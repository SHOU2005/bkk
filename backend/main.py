"""
AcuTrace - Party Ledger & Fund Flow Intelligence Platform
Backend API Server
"""

import re
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from services.excel_processor import ExcelProcessor
from services.pdf_processor import PDFProcessor
from services.entity_normalizer import EntityNormalizer
from services.fund_flow_chain_builder import FundFlowChainBuilder
from services.transaction_categorizer import TransactionCategorizer
from services.export_service import ExportService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AcuTrace API",
    description="Party Ledger & Fund Flow Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

excel_processor = ExcelProcessor()
pdf_processor = PDFProcessor()
entity_normalizer = EntityNormalizer()
fund_flow_builder = FundFlowChainBuilder()
categorizer = TransactionCategorizer()
export_service = ExportService()

SUPPORTED_EXTENSIONS = ('.xls', '.xlsx', '.pdf')


def _extract_party_from_narration(narration: str) -> Optional[str]:
    """
    Extract party name from narration using comprehensive pattern matching.
    This is the fallback method when processor-level extraction fails.
    """
    if not narration or len(narration) < 2:
        return None
    
    narration = narration.upper().strip()
    party = None
    
    # ========== UPI PATTERNS ==========
    upi_patterns = [
        r'UPI/(?:CR|DR)/\d+/(.+?)/(?:OK|FAIL|PA|BI|AX|PASS)',
        r'UPI/\d+/(.+?)/(?:OK|FAIL|PA|BI)$',
        r'UPI-(?:CR|DR)?-?\d*-?(.+?)(?:[-/]OK|[-/]FAIL|[-/]PA|[-/]BI|$)',
        r'@([a-zA-Z0-9]+)',
        r'UPI[/\s]*(?:from|to|by)[/\s]*([A-Z][A-Za-z\s]{2,})',
        r'UPI/(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]{2,})',
        r'UPI[/\s]*(?:CR|DR)[/\s]*(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]{2,})',
        r'(?:UPI|PAYTM|GPAY|PHONEPE)[/\s]*(?:CR|DR)?[/\s]*(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]+?)(?:/OKPA|/OKAX|/OKBI|/OK)',
    ]
    
    for pattern in upi_patterns:
        match = re.search(pattern, narration, re.IGNORECASE)
        if match and match.group(1):
            candidate = match.group(1).upper().strip()
            candidate = ' '.join(candidate.split())
            if len(candidate) >= 2 and candidate not in ['DR', 'CR', 'TRF', 'BY', 'TO', 'FROM']:
                party = candidate
                break
    
    # ========== TRANSFER PATTERNS ==========
    if not party:
        transfer_patterns = [
            r'(?:transfer|TRANSFER)\s+(?:from|to|FROM|TO)\s+([A-Z][A-Za-z\s]{2,})',
            r'PAID\s+TO\s+([A-Z][A-Za-z\s]{2,})',
            r'RECEIVED\s+FROM\s+([A-Z][A-Za-z\s]{2,})',
            r'BY\s+(?:TRANSFER|NEFT|RTGS|IMPS)[:\s-]*([A-Z][A-Za-z\s]{2,})',
            r'TRF\s+(?:TO|FROM)[:\s]*([A-Z][A-Za-z\s]{2,})',
        ]
        for pattern in transfer_patterns:
            match = re.search(pattern, narration, re.IGNORECASE)
            if match and match.group(1):
                candidate = match.group(1).upper().strip()
                candidate = ' '.join(candidate.split())
                if len(candidate) >= 2:
                    party = candidate
                    break
    
    # ========== RTGS/NEFT/IMPS PATTERNS ==========
    if not party:
        other_transfer_patterns = [
            r'RTGS\s+(?:CR|DR)?[-]?\s*(?:[A-Z0-9]+[-])?\s*([A-Z][A-Za-z\s]{2,})',
            r'NEFT\s+(?:CR|DR)?[-]?\s*(?:[A-Z0-9]+[-])?\s*([A-Z][A-Za-z\s]{2,})',
            r'IMPS\s+(?:CR|DR)?[-]?\s*(?:[A-Z0-9]+[-])?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        for pattern in other_transfer_patterns:
            match = re.search(pattern, narration, re.IGNORECASE)
            if match and match.group(1):
                candidate = match.group(1).upper().strip()
                candidate = ' '.join(candidate.split())
                if len(candidate) >= 2:
                    party = candidate
                    break
    
    # ========== CASH/BILL PATTERNS ==========
    if not party:
        other_patterns = [
            r'CASH\s+(?:DEPOSIT|WITHDRAWAL)\s*(?:AT|BY)?\s*([A-Z][A-Za-z\s]{2,})',
            r'(?:BILL|EMI|LOAN)\s+(?:PAYMENT|REPAYMENT)[:\s]*([A-Z][A-Za-z\s]{2,})',
            r'INSURANCE\s+(?:PREMIUM|PAYMENT)[:\s]*([A-Z][A-Za-z\s]{2,})',
            r'SALARY\s+(?:FROM|TO)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        for pattern in other_patterns:
            match = re.search(pattern, narration, re.IGNORECASE)
            if match and match.group(1):
                candidate = match.group(1).upper().strip()
                candidate = ' '.join(candidate.split())
                if len(candidate) >= 2:
                    party = candidate
                    break
    
    # ========== TO/FOR/FROM PATTERNS ==========
    if not party:
        to_from_patterns = [
            r'TO\s+([A-Z][A-Za-z\s]{2,})',
            r'FOR\s+([A-Z][A-Za-z\s]{2,})',
            r'FROM\s+([A-Z][A-Za-z\s]{2,})',
            r'AT\s+([A-Z][A-Za-z\s]{2,})',
        ]
        for pattern in to_from_patterns:
            match = re.search(pattern, narration, re.IGNORECASE)
            if match and match.group(1):
                candidate = match.group(1).upper().strip()
                candidate = re.sub(r'^(TO|FROM|FOR|AT|ON|BY|REF|NO|NEW|AC|ACC)\s*', '', candidate)
                candidate = ' '.join(candidate.split())
                if len(candidate) >= 2:
                    party = candidate
                    break
    
    # ========== NORMALIZE PARTY NAME ==========
    if party:
        # Remove business suffixes
        suffixes = ['TRADERS', 'TRDG', 'AGENCIES', 'SERVICES', 'PVT', 'LTD', 'LIMITED',
                   'CORP', 'INC', 'COMPANY', 'HOLDINGS', 'INDUSTRIES']
        for suffix in suffixes:
            party = re.sub(rf'\b{suffix}\b', '', party, flags=re.IGNORECASE)
        
        # Remove special characters and digits
        party = re.sub(r'[^\w\s]', ' ', party)
        party = re.sub(r'\b[\d]{10,}\b', '', party)
        
        # Clean up
        party = ' '.join(party.split())
        party = party.strip()
        
        if len(party) >= 2:
            logger.debug(f"Party extracted from narration: '{narration[:50]}...' -> '{party}'")
            return party
    
    # ========== LAST RESORT: Extract meaningful words ==========
    if not party:
        transaction_words = ['DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'TRANSFER', 'CREDIT', 'DEBIT',
                           'BALANCE', 'CHARGES', 'FEE', 'TAX', 'EMI', 'BILL', 'SALARY',
                           'INTEREST', 'DIVIDEND', 'REFUND', 'REVERSAL', 'CLEARING', 'NO', 'NUM',
                           'BY', 'TO', 'FROM', 'FOR', 'AT', 'ON']
        cleaned = narration
        for word in transaction_words:
            cleaned = re.sub(r'\b' + word + r'\b', ' ', cleaned, flags=re.IGNORECASE)
        
        words = cleaned.strip().split()
        meaningful = [w for w in words if len(w) > 2 and not w.isdigit()]
        
        if meaningful:
            party = ' '.join(meaningful[:3]).upper()
            # Clean up
            party = re.sub(r'[^\w\s]', ' ', party)
            party = ' '.join(party.split())
            if len(party) >= 2:
                logger.debug(f"Party extracted (fallback): '{narration[:50]}...' -> '{party}'")
                return party
    
    logger.debug(f"No party found for narration: '{narration[:50]}...'")
    return None


@app.get("/")
async def root():
    return {"message": "AcuTrace API", "status": "operational", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "acutrace-party-ledger"}

@app.post("/api/analyze")
async def analyze_statement(file: UploadFile = File(...)):
    """Analyze a single bank statement for party ledger and fund flow intelligence."""
    try:
        if not file.filename.lower().endswith(SUPPORTED_EXTENSIONS):
            raise HTTPException(status_code=400, detail=f"Only {', '.join(SUPPORTED_EXTENSIONS)} files are supported")
        
        logger.info(f"Processing file: {file.filename}")
        
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        transactions = []
        account_profile = {}
        
        if file.filename.lower().endswith(('.xls', '.xlsx')):
            logger.info("Extracting transactions from Excel...")
            try:
                result = excel_processor.extract_transactions(file_bytes, file.filename)
                
                if isinstance(result, tuple) and len(result) == 2:
                    transactions, account_profile = result
                else:
                    transactions = result if isinstance(result, list) else []
                    account_profile = {}
                
                logger.info(f"Excel extraction returned {len(transactions)} transactions")
            except Exception as e:
                logger.error(f"Excel extraction error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Failed to process Excel file: {str(e)}")
        
        elif file.filename.lower().endswith('.pdf'):
            logger.info("Extracting transactions from PDF...")
            try:
                transactions = pdf_processor.extract_transactions(file_bytes)
                logger.info(f"PDF extraction returned {len(transactions)} transactions")
                
                if not transactions:
                    raise ValueError("No transactions found in PDF.")
            except Exception as e:
                logger.error(f"PDF extraction error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Failed to process PDF file: {str(e)}")
        
        if not transactions or len(transactions) == 0:
            logger.warning(f"No transactions found in {file.filename}")
            raise HTTPException(status_code=400, detail="No transactions found. Please ensure the file contains valid bank statement data.")
        
        logger.info(f"Extracted {len(transactions)} transactions from {file.filename}")
        
        # Clear and reset
        entity_normalizer.clear()
        fund_flow_builder.clear()
        
        # Process each transaction - REGISTER PARTIES WITH ENTITY NORMALIZER
        party_extraction_stats = {'total': len(transactions), 'found': 0, 'fallback': 0}
        
        for idx, txn in enumerate(transactions):
            try:
                # Calculate amount if not set
                if txn.get('amount', 0) == 0:
                    txn['amount'] = (txn.get('credit', 0) or 0) - (txn.get('debit', 0) or 0)
                
                # Get existing party from processor
                existing_party = txn.get('detected_party') or txn.get('party')
                description = txn.get('description', '')
                is_credit = txn.get('credit', 0) > 0
                amount = txn.get('amount', 0)
                
                # If party already exists from processor, use it directly
                party_to_register = existing_party
                
                if not party_to_register or party_to_register in ['DEPOSIT', 'CASH', 'WITHDRAWAL', 'TRANSFER', 'UNKNOWN', '']:
                    # Try fallback extraction
                    fallback_party = _extract_party_from_narration(description)
                    if fallback_party:
                        party_to_register = fallback_party
                        txn['detected_party'] = fallback_party
                        txn['party'] = fallback_party
                        party_extraction_stats['fallback'] += 1
                    else:
                        # Last resort: extract meaningful words from description
                        words = description.replace('DEPOSIT', '').replace('PAYMENT', '').replace('CASH', '').replace('UTR', '').strip().split()
                        meaningful = [w for w in words if len(w) > 2 and not w.isdigit()]
                        if meaningful:
                            party_to_register = ' '.join(meaningful[:3]).upper()
                            txn['detected_party'] = party_to_register
                            txn['party'] = party_to_register
                            party_extraction_stats['fallback'] += 1
                
                if party_to_register and party_to_register not in ['DEPOSIT', 'CASH', 'WITHDRAWAL', 'TRANSFER', 'UNKNOWN', '']:
                    party_extraction_stats['found'] += 1
                    # Register party with entity_normalizer
                    entity_normalizer.extract_entity(
                        description,
                        amount,
                        is_credit=is_credit
                    )
                    # Get the registered party name (normalized)
                    registered_party = entity_normalizer._normalize_name(party_to_register)
                    if registered_party and registered_party in entity_normalizer.entities:
                        txn['party'] = registered_party
                        txn['detected_party'] = registered_party
                    logger.debug(f"Registered party: {party_to_register}")
                
                # Categorize transaction (includes IMPS, RTGS)
                category_data = categorizer.categorize_transaction(txn)
                txn.update(category_data)
                
            except Exception as e:
                logger.warning(f"Error processing transaction {idx}: {str(e)}")
                continue
        
        logger.info(f"Party extraction stats: {party_extraction_stats}")
        
        # Build fund flow chains
        fund_flow_builder.add_transactions(transactions, file.filename)
        fund_flow_builder.build_chains()
        
        # Get party ledger summary
        party_ledger = entity_normalizer.get_party_ledger_summary()
        
        # Debug: log party ledger
        logger.info(f"Party ledger: {len(party_ledger)} parties")
        for party in party_ledger[:10]:
            logger.info(f"  - {party['party_name']}: {party['transaction_count']} transactions, ₹{party['total_credit'] + party['total_debit']}")
        
        fund_flow_chains = fund_flow_builder.get_chain_summary()
        entity_relations = entity_normalizer.get_entity_relation_index()
        
        source_type = "pdf" if file.filename.lower().endswith('.pdf') else "xls"
        
        response_data = {
            "status": "success",
            "metadata": {
                "filename": file.filename,
                "total_transactions": len(transactions),
                "analysis_timestamp": datetime.now().isoformat(),
                "source": f"single_{source_type}",
                "party_extraction_stats": party_extraction_stats
            },
            "transactions": transactions,
            "account_profile": account_profile,
            "party_ledger": {
                "parties": party_ledger,
                "total_parties": len(party_ledger),
                "statistics": entity_normalizer.get_statistics()
            },
            "fund_flow_chains": fund_flow_chains,
            "entity_relations": entity_relations
        }
        
        logger.info(f"Analysis complete. Found {len(party_ledger)} parties, {fund_flow_chains.get('total_chains', 0)} fund flow chains")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/analyze/multi")
async def analyze_multiple_statements(files: List[UploadFile] = File(...)):
    """Analyze multiple bank statement files simultaneously."""
    try:
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        logger.info(f"Processing {len(files)} files simultaneously...")
        
        import asyncio
        
        async def process_file(file: UploadFile):
            try:
                if not file.filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    return None, None, {}
                
                file_bytes = await file.read()
                if len(file_bytes) == 0:
                    return None, None, {}
                
                transactions = []
                account_profile = {}
                
                if file.filename.lower().endswith(('.xls', '.xlsx')):
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        excel_processor.extract_transactions, 
                        file_bytes,
                        file.filename
                    )
                    
                    if isinstance(result, tuple) and len(result) == 2:
                        transactions, account_profile = result
                    else:
                        transactions = result if isinstance(result, list) else []
                        account_profile = {}
                
                elif file.filename.lower().endswith('.pdf'):
                    transactions = pdf_processor.extract_transactions(file_bytes)
                
                if not transactions or len(transactions) == 0:
                    return None, None, {}
                
                for txn in transactions:
                    txn['_source_file'] = file.filename
                
                metadata = {
                    "filename": file.filename,
                    "file_type": "pdf" if file.filename.lower().endswith('.pdf') else "xls",
                    "transaction_count": len(transactions)
                }
                
                return transactions, metadata, account_profile
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                return None, None, {}
        
        tasks = [process_file(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_transactions = []
        file_metadata = []
        combined_account_profile = {}
        
        for result in results:
            if isinstance(result, Exception):
                continue
            
            transactions, metadata, account_profile = result
            if transactions and metadata:
                all_transactions.extend(transactions)
                file_metadata.append(metadata)
                if account_profile:
                    for key, value in account_profile.items():
                        if key not in combined_account_profile or not combined_account_profile[key]:
                            combined_account_profile[key] = value
        
        if not all_transactions or len(all_transactions) == 0:
            raise HTTPException(status_code=400, detail="No transactions found in any file.")
        
        logger.info(f"Total extracted: {len(all_transactions)} transactions from {len(file_metadata)} files")
        
        entity_normalizer.clear()
        fund_flow_builder.clear()
        
        party_extraction_stats = {'total': len(all_transactions), 'found': 0, 'fallback': 0}
        
        for txn in all_transactions:
            if txn.get('amount', 0) == 0:
                txn['amount'] = (txn.get('credit', 0) or 0) - (txn.get('debit', 0) or 0)
            
            existing_party = txn.get('detected_party') or txn.get('party')
            description = txn.get('description', '')
            is_credit = txn.get('credit', 0) > 0
            amount = txn.get('amount', 0)
            
            # If party already exists from processor, use it directly
            party_to_register = existing_party
            
            if not party_to_register or party_to_register in ['DEPOSIT', 'CASH', 'WITHDRAWAL', 'TRANSFER', 'UNKNOWN', '']:
                # Try fallback extraction
                fallback_party = _extract_party_from_narration(description)
                if fallback_party:
                    party_to_register = fallback_party
                    txn['detected_party'] = fallback_party
                    txn['party'] = fallback_party
                    party_extraction_stats['fallback'] += 1
                else:
                    # Last resort: extract meaningful words from description
                    words = description.replace('DEPOSIT', '').replace('PAYMENT', '').replace('CASH', '').replace('UTR', '').strip().split()
                    meaningful = [w for w in words if len(w) > 2 and not w.isdigit()]
                    if meaningful:
                        party_to_register = ' '.join(meaningful[:3]).upper()
                        txn['detected_party'] = party_to_register
                        txn['party'] = party_to_register
                        party_extraction_stats['fallback'] += 1
            
            if party_to_register and party_to_register not in ['DEPOSIT', 'CASH', 'WITHDRAWAL', 'TRANSFER', 'UNKNOWN', '']:
                party_extraction_stats['found'] += 1
                # Register party with entity_normalizer
                entity_normalizer.extract_entity(
                    description,
                    amount,
                    is_credit=is_credit
                )
                # Get the registered party name (normalized)
                registered_party = entity_normalizer._normalize_name(party_to_register)
                if registered_party and registered_party in entity_normalizer.entities:
                    txn['party'] = registered_party
                    txn['detected_party'] = registered_party
            
            category_data = categorizer.categorize_transaction(txn)
            txn.update(category_data)
        
        logger.info(f"Party extraction stats (multi-file): {party_extraction_stats}")
        
        fund_flow_builder.add_transactions(all_transactions)
        fund_flow_builder.build_chains()
        
        merged = entity_normalizer.auto_merge_similar_entities()
        
        party_ledger = entity_normalizer.get_party_ledger_summary()
        fund_flow_chains = fund_flow_builder.get_chain_summary()
        entity_relations = entity_normalizer.get_entity_relation_index()
        
        response_data = {
            "status": "success",
            "metadata": {
                "files_processed": len(file_metadata),
                "file_details": file_metadata,
                "total_transactions": len(all_transactions),
                "analysis_timestamp": datetime.now().isoformat(),
                "source": "multi_file",
                "auto_merged_entities": merged,
                "party_extraction_stats": party_extraction_stats
            },
            "transactions": all_transactions,
            "account_profile": combined_account_profile,
            "party_ledger": {
                "parties": party_ledger,
                "total_parties": len(party_ledger),
                "statistics": entity_normalizer.get_statistics()
            },
            "fund_flow_chains": fund_flow_chains,
            "entity_relations": entity_relations
        }
        
        logger.info(f"Analysis complete. Found {len(party_ledger)} parties")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/party/{party_name}")
async def get_party_details(party_name: str):
    try:
        normalized = entity_normalizer._normalize_name(party_name)
        
        if normalized not in entity_normalizer.entities:
            raise HTTPException(status_code=404, detail=f"Party '{party_name}' not found")
        
        entity_data = entity_normalizer.entities[normalized]
        money_paths = fund_flow_builder.get_money_path_by_party(party_name)
        
        return JSONResponse(content={
            "status": "success",
            "party": {
                "name": normalized,
                "entity_type": entity_data.get("entity_type", "Unknown"),
                "transaction_count": entity_data["transaction_count"],
                "total_credit": entity_data["total_credit"],
                "total_debit": entity_data["total_debit"],
                "net_flow": entity_data["total_credit"] - entity_data["total_debit"],
                "upi_handles": list(entity_data.get("upi_handles", [])),
                "money_paths": money_paths,
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting party details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/fund-flow/chains")
async def get_fund_flow_chains():
    try:
        chains = fund_flow_builder.get_chain_summary()
        return JSONResponse(content={"status": "success", "fund_flow_chains": chains})
    except Exception as e:
        logger.error(f"Error getting fund flow chains: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/party-ledger")
async def get_party_ledger():
    try:
        party_ledger = entity_normalizer.get_party_ledger_summary()
        statistics = entity_normalizer.get_statistics()
        return JSONResponse(content={"status": "success", "party_ledger": {"parties": party_ledger, "total_parties": len(party_ledger), "statistics": statistics}})
    except Exception as e:
        logger.error(f"Error getting party ledger: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/relations")
async def get_party_relations():
    try:
        relations = entity_normalizer.get_entity_relation_index()
        return JSONResponse(content={"status": "success", "relations": relations, "total_relations": len(relations)})
    except Exception as e:
        logger.error(f"Error getting relations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/export/json")
async def export_analysis(format: str = Query("json")):
    try:
        party_ledger = entity_normalizer.get_party_ledger_summary()
        fund_flow_chains = fund_flow_builder.get_chain_summary()
        entity_relations = entity_normalizer.get_entity_relation_index()
        
        export_data = {"export_timestamp": datetime.now().isoformat(), "party_ledger": party_ledger, "fund_flow_chains": fund_flow_chains, "entity_relations": entity_relations}
        return JSONResponse(content=export_data)
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
    return {"message": "Report generation endpoint", "report_id": report_id}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

