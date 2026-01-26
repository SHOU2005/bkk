"""
Excel Processor - Extract Transactions from XLS/XLSX Files
Comprehensive pattern matching for Indian bank statements
"""

import io
import logging
from datetime import datetime
import pandas as pd
import re

logger = logging.getLogger(__name__)


class ExcelProcessor:
    def __init__(self):
        # ========== COMPREHENSIVE UPI PATTERNS ==========
        # All possible UPI transaction formats from Indian banks
        self.upi_patterns = [
            # Standard formats: UPI/CR/REF/PARTY/OK, UPI/DR/REF/PARTY/OK
            r'UPI/(?:CR|DR)/\d+/(.+?)/(?:OK|FAIL|PA|BI|AX|BI|PASS)',
            r'UPI/(?:CR|DR)/\d+/(.+?)$',
            r'UPI/\d+/(.+?)/(?:OK|FAIL|PA|BI)',
            r'UPI/(.+?)/(?:OK|FAIL|PA|BI)$',
            # UPI with dash separators: UPI-REF-PARTY-OK
            r'UPI-(?:CR|DR)?-?\d*-?(.+?)(?:[-/]OK|[-/]FAIL|[-/]PA|[-/]BI|$)',
            r'UPI[-/]*(?:CR|DR)?[-/]*\d*[-/]*(.+?)(?:[-/]OK|[-/]PA|[-/]BI|$)',
            # UPI with @ handle: @partyname
            r'@([a-zA-Z0-9]+)',
            r'UPI[/\s]*@([a-zA-Z0-9]+)',
            # UPI from/to formats
            r'UPI[/\s]*(?:from|to|by)[/\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|/)',
            # UPI with transaction ref: UPI/D123456789012345/PARTYNAME
            r'UPI/(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|/)',
            # UPI with CR/DR and ref
            r'UPI[/\s]*(?:CR|DR)[/\s]*(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$)',
            # Additional common UPI formats
            r'UPI[/]*(?:CR|DR)?[/]*([A-Z][A-Za-z\s]+?)(?:/OKAX|/OKBI|/OKPA|/OK|/PA|/BI|/PAYPASS|$)',
            r'UPI[/\s]*(?:CR|DR)?[/\s]*(?:D\d+)?[/\s]*([A-Z0-9]+(?:\s*[A-Z0-9]+)?)(?:/OKAX|/OKBI|/OKPA|/OK|/PA|/BI|/PAYPASS|$)',
            r'UPI[/\s]*(?:CR|DR)?[/\s]*(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]+?)(?:/OKPA|/GPAYBILLPAY)',
        ]
        
        # ========== RTGS PATTERNS ==========
        self.rtgs_patterns = [
            # RTGS CR-123456- PARTYNAME -123456
            r'RTGS\s+CR[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]\s*[A-Z0-9]|$)',
            r'RTGS\s+(?:CR|DR)[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            # RTGS transfer formats
            r'RTGS\s+(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'RTGS[/\s]+(?:transfer|TRF)?[/\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            # RTGS with ref numbers
            r'RTGS\s+(?:CR|DR)?\s*[A-Z0-9/\-]*\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== NEFT PATTERNS ==========
        self.neft_patterns = [
            # NEFT CR-123456- PARTYNAME -123456
            r'NEFT\s+CR[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            r'NEFT\s+(?:CR|DR)[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            # NEFT transfer formats
            r'NEFT\s+(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'NEFT[/\s]+(?:transfer|TRF)?[/\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            # NEFT with ref numbers
            r'NEFT\s+(?:CR|DR)?\s*[A-Z0-9/\-]*\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== IMPS PATTERNS ==========
        self.imps_patterns = [
            # IMPS CR-123456- PARTYNAME -123456
            r'IMPS\s+(?:CR|DR)[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            # IMPS from/to formats
            r'IMPS[/]*(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'IMPS\s+(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$)',
            # IMPS transfer formats
            r'IMPS[/\s]+(?:transfer|TRF)?[/\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            # IMPS with ref numbers
            r'IMPS\s+(?:CR|DR)?\s*[A-Z0-9/\-]*\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== GENERIC TRANSFER PATTERNS ==========
        self.transfer_patterns = [
            r'(?:transfer|TRANSFER)\s+(?:from|to|FROM|TO)\s+([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'PAID\s+TO\s+([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'RECEIVED\s+FROM\s+([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'BY\s+(?:TRANSFER|NEFT|RTGS|IMPS)[:\s-]*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'TRF\s+(?:TO|FROM)[:\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'TRANSFER\s+(?:TO|FROM)?\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'Payment\s+(?:to|from)?\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
        ]
        
        # ========== CASH PATTERNS ==========
        self.cash_patterns = [
            r'CASH\s+DEPOSIT\s+(?:AT|BY)?\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'CASH\s+(?:DEPOSIT|WITHDRAWAL)[-]\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'CASH\s+BY\s+([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'CASH\s+(?:DEPOSIT|WITHDRAWAL)\s+(?:AT)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== BILL/EMI PATTERNS ==========
        self.bill_patterns = [
            r'(?:BILL|EMI|LOAN)\s+(?:PAYMENT|REPAYMENT)[:\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'(?:BILL|EMI)\s+(?:FOR|TO)?\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'(?:CREDIT\s+CARD|DEBIT\s+CARD)\s+BILL[:\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'INSURANCE\s+(?:PREMIUM|PAYMENT)[:\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'(?:BILL|PAYMENT)\s+(?:FOR|TO)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== SALARY/INTEREST PATTERNS ==========
        self.salary_patterns = [
            r'SALARY\s+(?:FROM|TO)?\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'INTEREST\s+(?:FROM|ON)?\s*([A-Z][A-Za-z\s]{2,})(?:\s*$|,)',
            r'DIVIDEND\s+(?:FROM)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== CHEQUE PATTERNS ==========
        self.cheque_patterns = [
            r'CHEQUE\s+(?:PAYMENT|DEPOSIT|CLEARING)[:\s-]*([A-Z][A-Za-z\s]{2,})',
            r'CHQ[:\s-]*([A-Z][A-Za-z\s]{2,})',
            r'CHEQUE\s+NO[:\s]*\d+\s*(?:DRAWN\s+ON)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== COMMON BUSINESS SUFFIXES ==========
        self.business_suffixes = [
            'traders', 'trdg', 'trd', 'agencies', 'agy', 'enterprises', 'entp',
            'services', 'srv', 'solutions', 'soln', 'pvt', 'ltd', 'limited',
            'corp', 'corporation', 'inc', 'company', 'co', 'group', 'associates',
            'bank', 'banking', 'holdings', 'fintech', 'payments', 'industries',
            'constructions', 'developers', 'realty', 'estates', 'stores', 'retail',
        ]
        
        # ========== KNOWN MERCHANTS ==========
        self.merchant_patterns = {
            r'\buber\b': 'UBER', 
            r'\bola\b': 'OLA', 
            r'\bswiggy\b': 'SWIGGY',
            r'\bzomato\b': 'ZOMATO', 
            r'\bamazon\b': 'AMAZON', 
            r'\bflipkart\b': 'FLIPKART',
            r'\bmyntra\b': 'MYNTRA', 
            r'\boyo\b': 'OYO', 
            r'\birctc\b': 'IRCTC',
            r'\bmakemytrip\b': 'MAKE MY TRIP', 
            r'\bredbus\b': 'REDBUS',
            r'\bpaytm\b': 'PAYTM', 
            r'\bphonepe\b': 'PHONEPE', 
            r'\bgpay\b': 'GPAY',
            r'\bbhim\b': 'BHIM', 
            r'\bgoogle\b': 'GOOGLE',
            r'\bnetflix\b': 'NETFLIX', 
            r'\bspotify\b': 'SPOTIFY',
            r'\bprime\b': 'PRIME VIDEO',
            r'\bhotstar\b': 'HOTSTAR',
            r'\bbookmyshow\b': 'BOOKMYSHOW',
            r'\bdominos\b': 'DOMINO\'S',
            r'\bpizzahut\b': 'PIZZA HUT',
            r'\bkfc\b': 'KFC',
            r'\bmcdonalds\b': 'MCDONALD\'S',
            r'\bswiggy\b': 'SWIGGY',
            r'\bzomato\b': 'ZOMATO',
            r'\bsblink\b': 'BLINKIT',
            r'\bzepto\b': 'ZEPTO',
            r'\bdunzo\b': 'DUNZO',
            r'\bsnapdeal\b': 'SNAPDEAL',
            r'\bmyntra\b': 'MYNTRA',
            r'\bajio\b': 'AJIO',
            r'\bnykaa\b': 'NYKAA',
            r'\bpurplle\b': 'PURPLLE',
        }
        
        # ========== BANK IFSC MAPPING ==========
        self.bank_from_ifsc = {
            'BDBL': 'Bandhan Bank', 'HDFC': 'HDFC Bank', 'SBIN': 'State Bank of India',
            'ICIC': 'ICICI Bank', 'AXIS': 'Axis Bank', 'KKBK': 'Kotak Mahindra Bank',
            'YESB': 'Yes Bank', 'IDFB': 'IDFC First Bank', 'CNRB': 'Canara Bank',
            'UTIB': 'Axis Bank', 'HDFC': 'HDFC Bank', 'ICIC': 'ICICI Bank',
            'SBIN': 'SBI', 'BARB': 'Bank of Baroda', 'PUNB': 'Punjab National Bank',
            'ORBC': 'Oriental Bank', 'VIJB': 'Vijaya Bank', 'BKID': 'Bank of India',
            'MAHB': 'Bank of Maharashtra', 'IDIB': 'Indian Bank', 'SYNB': 'Syndicate Bank',
            'CBIN': 'Central Bank', 'RATN': 'RBL Bank', 'YESB': 'Yes Bank',
        }
        
        self.party_cache = {}
        self.date_formats = ['%d-%b-%Y', '%d-%b-%y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
    
    def extract_transactions(self, file_content: bytes, filename: str = ""):
        transactions = []
        account_profile = {}
        
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_content))
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                    account_profile = self._extract_account_profile(df)
                    
                    header_row = self._detect_header_row(df)
                    if header_row is None:
                        continue
                    
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                    df.columns = [str(c).replace('\n', ' ').strip() if pd.notna(c) else c for c in df.columns]
                    df = self._normalize_columns(df)
                    
                    sheet_transactions = self._extract_from_dataframe(df, filename, sheet_name)
                    transactions.extend(sheet_transactions)
                except Exception as e:
                    logger.warning(f"Error in sheet '{sheet_name}': {e}")
                    continue
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return [], {}
        
        return transactions, account_profile
    
    def _extract_account_profile(self, df):
        account_profile = {}
        header_text = ""
        for idx in range(min(15, len(df))):
            row_values = [str(v) for v in df.iloc[idx].values if pd.notna(v)]
            header_text += " " + " ".join(row_values)
        header_text = header_text.upper()
        
        patterns = [
            r'(?:ACCOUNT\s*TITLE[:\s]*)([A-Z][A-Z\s]{2,50})',
            r'(?:ACCOUNT\s*HOLDER[:\s]*)([A-Z][A-Z\s]{2,50})',
            r'(?:NAME[:\s]*)([A-Z][A-Z\s]{2,50})',
        ]
        for pattern in patterns:
            match = re.search(pattern, header_text)
            if match:
                name = match.group(1).strip()
                name = ' '.join(name.split())
                if len(name) >= 3:
                    account_profile['account_holder_name'] = name
                    break
        
        match = re.search(r'(?:ACCOUNT|NO\.?)[:\s#]*([A-Z0-9]{5,20})', header_text)
        if match:
            account_profile['account_number'] = match.group(1)
        
        match = re.search(r'(?:IFSC[:\s]*)([A-Z]{4}[0-9]{7})', header_text)
        if match:
            ifsc = match.group(1)
            account_profile['ifsc_code'] = ifsc
            bank_prefix = ifsc[:4]
            if bank_prefix in self.bank_from_ifsc:
                account_profile['bank_name'] = self.bank_from_ifsc[bank_prefix]
        
        return account_profile
    
    def _detect_header_row(self, df):
        keywords = ['date', 'description', 'credit', 'debit', 'balance', 'narration', 'amount']
        for idx, row in df.iterrows():
            row_str = ' '.join([str(v).replace('\n', ' ') for v in row.values if pd.notna(v)]).lower()
            matches = sum(1 for kw in keywords if kw in row_str)
            if matches >= 2:
                return idx
        return None
    
    def _normalize_columns(self, df):
        new_columns = {}
        used_types = set()
        
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            
            if col_lower in ['date', 'trans date', 'txn date', 'posting date'] and 'date' not in used_types:
                new_columns[col] = 'date'
                used_types.add('date')
            elif col_lower in ['description', 'narration', 'particulars', 'details', 'remarks'] and 'description' not in used_types:
                new_columns[col] = 'description'
                used_types.add('description')
            elif col_lower in ['credit', 'credits', 'cr', 'deposit', 'deposits'] and 'credit' not in used_types:
                new_columns[col] = 'credit'
                used_types.add('credit')
            elif col_lower in ['debit', 'debits', 'dr', 'withdrawal', 'withdrawals'] and 'debit' not in used_types:
                new_columns[col] = 'debit'
                used_types.add('debit')
            elif col_lower in ['balance', 'bal', 'closing balance'] and 'balance' not in used_types:
                new_columns[col] = 'balance'
                used_types.add('balance')
        
        df = df.rename(columns=new_columns)
        
        final_cols = []
        for c in ['date', 'description', 'credit', 'debit', 'balance']:
            if c in df.columns:
                final_cols.append(c)
        
        return df[final_cols] if final_cols else df
    
    def _extract_from_dataframe(self, df, filename, sheet_name):
        transactions = []
        
        for idx, row in df.iterrows():
            try:
                date_val = row.get('date')
                date = None
                if pd.notna(date_val):
                    date_str = str(date_val).replace('\n', ' ').strip()
                    for fmt in self.date_formats:
                        try:
                            date = datetime.strptime(date_str, fmt).strftime('%d/%m/%Y')
                            break
                        except:
                            continue
                    if not date:
                        date = date_str
                
                desc_val = row.get('description')
                description = str(desc_val).replace('\n', ' ').strip() if pd.notna(desc_val) else ''
                
                def get_amount(val):
                    if pd.isna(val):
                        return 0.0
                    s = str(val).replace('\n', ' ').strip()
                    s = re.sub(r'[Rs$,\s]', '', s)
                    s = re.sub(r'[^0-9.-]', '', s)
                    try:
                        return float(s) if s else 0.0
                    except:
                        return 0.0
                
                credit = get_amount(row.get('credit'))
                debit = get_amount(row.get('debit'))
                balance = get_amount(row.get('balance'))
                amount = credit if credit > 0 else (-debit if debit > 0 else 0)
                
                if not date and not description and amount == 0:
                    continue
                
                detected_party = self._extract_party_name(description)
                
                # Set both party and detected_party for frontend compatibility
                party = detected_party if detected_party else None
                
                transactions.append({
                    'date': date,
                    'description': description.strip(),
                    'amount': amount,
                    'credit': credit,
                    'debit': debit,
                    'balance': balance,
                    'source_file': filename,
                    'source_sheet': sheet_name,
                    'party': party,
                    'detected_party': party,
                    'is_transfer': any(kw in description.lower() for kw in ['neft', 'imps', 'rtgs', 'transfer', 'trf', 'by transfer']),
                    'is_upi': any(kw in description.lower() for kw in ['upi', '@', 'gpay', 'phonepe', 'paytm', 'bhim']),
                })
            except Exception as e:
                logger.debug(f"Row {idx} error: {e}")
                continue
        
        return transactions
    
    def _extract_party_name(self, narration):
        """
        Extract party name from transaction narration with comprehensive pattern matching.
        Returns the party name or None if not found.
        """
        if not narration or len(narration) < 2:
            return None
        
        narration_clean = narration.strip()
        cache_key = narration_clean.upper()[:100]
        if cache_key in self.party_cache:
            return self.party_cache[cache_key]
        
        party = None
        
        # ========== STEP 1: Check known merchants ==========
        for pattern, name in self.merchant_patterns.items():
            if re.search(pattern, narration_clean.lower()):
                party = name
                logger.debug(f"Merchant match: '{narration}' -> '{party}'")
                break
        
        # ========== STEP 2: Try all pattern groups ==========
        if not party:
            pattern_groups = [
                (self.upi_patterns, 'UPI'),
                (self.rtgs_patterns, 'RTGS'),
                (self.neft_patterns, 'NEFT'),
                (self.imps_patterns, 'IMPS'),
                (self.transfer_patterns, 'Transfer'),
                (self.cheque_patterns, 'Cheque'),
                (self.cash_patterns, 'Cash'),
                (self.bill_patterns, 'Bill'),
                (self.salary_patterns, 'Salary'),
            ]
            
            for group_patterns, ptype in pattern_groups:
                for pattern in group_patterns:
                    match = re.search(pattern, narration, re.IGNORECASE)
                    if match:
                        try:
                            if match.group(1):
                                candidate = match.group(1).upper().strip()
                                candidate = ' '.join(candidate.split())
                                # Validate candidate
                                if len(candidate) >= 2 and candidate not in ['DR', 'CR', 'TRF', 'BY', 'TO', 'FROM', 'PAID', 'RECEIVED']:
                                    party = self._normalize_party_name(candidate)
                                    logger.debug(f"Match ({ptype}): '{narration}' -> '{party}'")
                                    break
                        except IndexError:
                            continue
                if party:
                    break
        
        # ========== STEP 3: Advanced fallback - extract from description ==========
        if not party:
            party = self._extract_party_advanced(narration_clean)
        
        if party:
            self.party_cache[cache_key] = party
        
        return party
    
    def _extract_party_advanced(self, narration):
        """
        Advanced party extraction for complex narrations.
        Uses various heuristics to extract party names.
        """
        party = None
        
        # Try to find patterns like "TO PARTYNAME", "FROM PARTYNAME"
        to_patterns = [
            r'TO\s+([A-Z][A-Za-z\s]{2,})',
            r'FOR\s+([A-Z][A-Za-z\s]{2,})',
            r'ON\s+([A-Z][A-Za-z\s]{2,})',
            r'AT\s+([A-Z][A-Za-z\s]{2,})',
        ]
        
        for pattern in to_patterns:
            match = re.search(pattern, narration, re.IGNORECASE)
            if match:
                candidate = match.group(1).upper().strip()
                candidate = ' '.join(candidate.split())
                # Remove common prefixes/suffixes
                candidate = re.sub(r'^(TO|FROM|FOR|AT|ON|BY|REF|REFNO|NO|NEW|AC|ACC|ACCOUNT)\s*', '', candidate, flags=re.IGNORECASE)
                if len(candidate) >= 2:
                    party = self._normalize_party_name(candidate)
                    break
        
        # If still no party, try to extract meaningful words
        if not party:
            # Remove common transaction words
            cleaned = narration
            transaction_words = ['DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'TRANSFER', 'CREDIT', 'DEBIT', 
                               'BALANCE', 'CHARGES', 'FEE', 'TAX', 'EMI', 'BILL', 'SALARY',
                               'INTEREST', 'DIVIDEND', 'REFUND', 'REVERSAL', 'CLEARING']
            for word in transaction_words:
                cleaned = re.sub(r'\b' + word + r'\b', ' ', cleaned, flags=re.IGNORECASE)
            
            words = cleaned.strip().split()
            meaningful = [w for w in words if len(w) > 2 and not w.isdigit()]
            
            if meaningful:
                # Take first 3 meaningful words as party name
                party = ' '.join(meaningful[:3]).upper()
                party = self._normalize_party_name(party)
        
        return party
    
    def _normalize_party_name(self, name):
        """
        Normalize party name by removing suffixes and cleaning up.
        """
        if not name:
            return ""
        
        name = str(name).upper().strip()
        
        # Remove business suffixes
        for suffix in self.business_suffixes:
            name = re.sub(rf'\b{suffix}\b', '', name, flags=re.IGNORECASE)
        
        # Remove long number sequences (likely phone numbers or refs)
        name = re.sub(r'\b[\d]{10,}\b', '', name)
        
        # Remove special characters except spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Remove common prefixes
        name = re.sub(r'^(?:TO|FROM|FOR|VIA|BY|REF|REFNO|NO|NEW|AC|ACC|ACCOUNT|TRANSFER|TRF)\s*', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        result = name.strip()
        
        # Ensure we return something meaningful
        if len(result) >= 2:
            return result
        
        return "UNKNOWN"
    
    def clear_cache(self):
        self.party_cache.clear()

