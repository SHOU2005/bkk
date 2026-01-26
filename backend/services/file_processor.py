"""
File Processing Service - Extracts transactions from bank statement XLS files
"""

import pandas as pd
from typing import List, Dict, Any
from io import BytesIO
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileProcessor:
    """Process XLS bank statements and extract transaction data"""
    
    def __init__(self):
        self.date_patterns = [
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}\.\d{2}\.\d{4}', # DD.MM.YYYY
        ]
        self.amount_pattern = r'[\d,]+\.?\d{0,2}'
        
    def extract_transactions(self, xls_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract all transactions from XLS bank statement.
        """
        transactions = []
        
        try:
            transactions = self._extract_with_pandas(xls_bytes)
            
            # Validate and clean transactions
            transactions = self._validate_and_clean(transactions)
            
            if not transactions:
                raise ValueError("No valid transactions extracted from XLS")
            
            logger.info(f"Successfully extracted {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Error extracting transactions: {str(e)}")
            raise
    
    def _extract_with_pandas(self, xls_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract transactions using pandas"""
        transactions = []
        
        try:
            df = pd.read_excel(BytesIO(xls_bytes))
            
            # Find header row
            header_row_idx = self._find_header_row(df)
            if header_row_idx is None:
                raise ValueError("Could not find header row in XLS")
            
            # Set header
            df.columns = df.iloc[header_row_idx]
            df = df.iloc[header_row_idx + 1:]
            
            # Rename columns
            df = df.rename(columns={
                'Date': 'date',
                'Transaction Date': 'date',
                'Description': 'description',
                'Narration': 'description',
                'Particulars': 'description',
                'Details': 'description',
                'Credit': 'credit',
                'Cr': 'credit',
                'Deposit': 'credit',
                'Debit': 'debit',
                'Dr': 'debit',
                'Withdrawal': 'debit',
                'Balance': 'balance',
                'Bal': 'balance'
            })
            
            # Convert to list of dicts
            transactions = df.to_dict('records')
            
        except Exception as e:
            logger.warning(f"pandas extraction error: {str(e)}")
        
        return transactions
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Find the header row in a dataframe"""
        header_keywords = ['date', 'description', 'narration', 'credit', 'debit', 'balance', 'amount']
        
        for idx, row in df.head().iterrows():
            row_text = ' '.join([str(cell).lower() if cell else '' for cell in row])
            if any(keyword in row_text for keyword in header_keywords):
                return idx
        return None
    
    def _validate_and_clean(self, transactions: List[Dict]) -> List[Dict]:
        """Validate and clean extracted transactions"""
        validated = []
        
        for txn in transactions:
            # Validate required fields
            if not txn.get('date') or not txn.get('description'):
                continue
            
            # Format date
            if txn['date']:
                try:
                    txn['date'] = pd.to_datetime(txn['date']).strftime('%d/%m/%Y')
                except:
                    txn['date'] = str(txn['date'])
            
            # Format amounts
            for col in ['credit', 'debit', 'balance']:
                if col in txn:
                    try:
                        txn[col] = float(txn[col])
                    except:
                        txn[col] = 0.0
                else:
                    txn[col] = 0.0
            
            validated.append(txn)
            
        return validated
