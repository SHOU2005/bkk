"""
Entity Normalizer - AI Party Detection from Transaction Narration
Comprehensive pattern matching for Indian bank statements
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class EntityNormalizer:
    def __init__(self):
        self.entities: Dict[str, Dict] = {}
        self.entity_relations: Dict[str, Dict] = defaultdict(lambda: {
            'sent_to': set(),
            'received_from': set(),
            'shared_refs': set(),
            'upi_handles': set(),
            'transaction_count': 0,
            'total_amount': 0.0
        })
        
        self.upi_clusters: Dict[str, Set[str]] = defaultdict(set)
        self.upi_to_party: Dict[str, str] = {}
        
        # ========== COMPREHENSIVE UPI PATTERNS ==========
        self.upi_patterns = [
            # UPI/CR/REF/PARTY/OK, UPI/DR/REF/PARTY/OK formats
            r'UPI/(?:CR|DR)/\d+/(.+?)/(?:OK|FAIL|PA|BI|AX|PASS)',
            r'UPI/(?:CR|DR)/\d+/(.+?)$',
            r'UPI/\d+/(.+?)/(?:OK|FAIL|PA|BI)$',
            r'UPI/(.+?)/(?:OK|FAIL|PA|BI)$',
            # UPI with dash separators
            r'UPI-(?:CR|DR)?-?\d*-?(.+?)(?:[-/]OK|[-/]FAIL|[-/]PA|[-/]BI|$)',
            r'UPI[-/]*(?:CR|DR)?[-/]*\d*[-/]*(.+?)(?:[-/]OK|[-/]PA|[-/]BI|$)',
            # UPI with @ handle
            r'@([a-zA-Z0-9]+)',
            r'UPI[/\s]*@([a-zA-Z0-9]+)',
            # UPI from/to formats
            r'UPI[/\s]*(?:from|to|by)[/\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|/)',
            # UPI with transaction ref
            r'UPI/(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$|/)',
            # UPI with CR/DR and ref
            r'UPI[/\s]*(?:CR|DR)[/\s]*(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]{2,})(?:\s*$)',
            # Additional common formats
            r'(?:UPI|PAYTM|GPAY|PHONEPE)[/\s]*(?:CR|DR)?[/\s]*(?:D\d+)?[/\s]*([A-Z][A-Za-z\s]+?)(?:/OKPA|/OKAX|/OKBI|/OK|/PAYPASS|$)',
            r'(?:UPI|upi)(?:[/\s-]*(?:CR|DR))?[/\s-]*\d*[/\s-]*([A-Z][A-Za-z\s]+?)(?:[/\s]*(?:OK|PA|BI)$|$)',
        ]
        
        # ========== RTGS PATTERNS ==========
        self.rtgs_patterns = [
            r'RTGS\s+CR[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]\s*[A-Z0-9]|$)',
            r'RTGS\s+(?:CR|DR)[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            r'RTGS\s+(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'RTGS[/\s]+(?:transfer|TRF)?[/\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'RTGS\s+(?:CR|DR)?\s*[A-Z0-9/\-]*\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== NEFT PATTERNS ==========
        self.neft_patterns = [
            r'NEFT\s+CR[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            r'NEFT\s+(?:CR|DR)[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            r'NEFT\s+(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'NEFT[/\s]+(?:transfer|TRF)?[/\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'NEFT\s+(?:CR|DR)?\s*[A-Z0-9/\-]*\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== IMPS PATTERNS ==========
        self.imps_patterns = [
            r'IMPS\s+(?:CR|DR)[-]\s*[A-Z0-9]+[-]\s*([A-Z][A-Za-z\s]+?)(?:[-]|$)',
            r'IMPS[/]*(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'IMPS\s+(?:from|to)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$)',
            r'IMPS[/\s]+(?:transfer|TRF)?[/\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'IMPS\s+(?:CR|DR)?\s*[A-Z0-9/\-]*\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== TRANSFER PATTERNS ==========
        self.transfer_patterns = [
            r'(?:transfer|TRANSFER)\s+(?:from|to|FROM|TO)\s+([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'PAID\s+TO\s+([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'RECEIVED\s+FROM\s+([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'BY\s+(?:TRANSFER|NEFT|RTGS|IMPS)[:\s-]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'TRF\s+(?:TO|FROM)[:\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'TRANSFER\s+(?:TO|FROM)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'Payment\s+(?:to|from)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
        ]
        
        # ========== CASH PATTERNS ==========
        self.cash_patterns = [
            r'CASH\s+DEPOSIT\s+(?:AT|BY)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'CASH\s+(?:DEPOSIT|WITHDRAWAL)[-]\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'CASH\s+BY\s+([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'CASH\s+(?:DEPOSIT|WITHDRAWAL)\s+(?:AT)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== BILL/EMI PATTERNS ==========
        self.bill_patterns = [
            r'(?:BILL|EMI|LOAN)\s+(?:PAYMENT|REPAYMENT)[:\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'(?:BILL|EMI)\s+(?:FOR|TO)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'(?:CREDIT\s+CARD|DEBIT\s+CARD)\s+BILL[:\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'INSURANCE\s+(?:PREMIUM|PAYMENT)[:\s]*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'(?:BILL|PAYMENT)\s+(?:FOR|TO)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== SALARY/INTEREST PATTERNS ==========
        self.salary_patterns = [
            r'SALARY\s+(?:FROM|TO)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'INTEREST\s+(?:FROM|ON)?\s*([A-Z][A-Za-z\s]+?)(?:\s*$|,)',
            r'DIVIDEND\s+(?:FROM)?\s*([A-Z][A-Za-z\s]+?)',
        ]
        
        # ========== CHEQUE PATTERNS ==========
        self.cheque_patterns = [
            r'CHEQUE\s+(?:PAYMENT|DEPOSIT|CLEARING)[:\s-]*([A-Z][A-Za-z\s]{2,})',
            r'CHQ[:\s-]*([A-Z][A-Za-z\s]{2,})',
            r'CHEQUE\s+NO[:\s]*\d+\s*(?:DRAWN\s+ON)?\s*([A-Z][A-Za-z\s]{2,})',
        ]
        
        # ========== INTEREST PATTERNS ==========
        self.interest_patterns = [
            r'CASA\s+CREDIT\s+INTEREST\s+CAPITALIZED',
            r'INTEREST\s+CAPITALIZED',
            r'INTEREST\s+PAID',
            r'INTEREST\s+CREDITED',
        ]
        
        # ========== SUFFIXES TO REMOVE ==========
        self.suffixes_to_remove = [
            'TRADERS', 'TRDG', 'TRD', 'AGENCIES', 'AGY', 'ENTERPRISES', 'ENTP',
            'SERVICES', 'SRV', 'SOLUTIONS', 'SOLN', 'PVT', 'LTD', 'LIMITED',
            'CORP', 'CORPORATION', 'INC', 'COMPANY', 'CO', 'HOLDINGS', 'HDG',
            'INDUSTRIES', 'CONSTRUCTIONS', 'DEVELOPERS', 'REALTY', 'ESTATES',
        ]
        
        # ========== MERCHANT ALIASES ==========
        self.merchant_aliases = {
            'AMZN': 'AMAZON', 'AZ': 'AMAZON', 'FLIP': 'FLIPKART',
            'SWIGGY': 'SWIGGY', 'ZOMATO': 'ZOMATO', 'MYN': 'MYNTRA',
            'NYK': 'NYKAA', 'GPAY': 'GPAY', 'PHONEPE': 'PHONEPE',
            'PAYTM': 'PAYTM', 'AMAZN': 'AMAZON', 'UBER': 'UBER',
            'OLA': 'OLA', 'IRCTC': 'IRCTC', 'MM': 'MAKE MY TRIP',
        }
        
        self.similarity_threshold = 0.75
    
    def extract_entity(self, description: str, amount: float, is_credit: bool = True) -> Optional[str]:
        """
        Extract and normalize entity/party name from transaction description.
        Returns the normalized party name or None if not found.
        """
        if not description:
            return None
        
        description = str(description).upper().strip()
        entity = None
        entity_type = 'General'
        upi_handle = None
        
        # ========== STEP 1: Check interest patterns ==========
        for pattern in self.interest_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                entity = 'INTEREST INCOME'
                entity_type = 'Income'
                logger.debug(f"Match (Income): '{description}' -> '{entity}'")
                break
        
        # ========== STEP 2: Try all pattern groups ==========
        if not entity:
            pattern_groups = [
                (self.upi_patterns, 'UPI'),
                (self.rtgs_patterns, 'Transfer'),
                (self.neft_patterns, 'Transfer'),
                (self.imps_patterns, 'Transfer'),
                (self.transfer_patterns, 'Transfer'),
                (self.cheque_patterns, 'Cheque'),
                (self.cash_patterns, 'Cash'),
                (self.bill_patterns, 'Bill'),
                (self.salary_patterns, 'Income'),
            ]
            
            for patterns, etype in pattern_groups:
                for pattern in patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        try:
                            if match.group(1):
                                candidate = match.group(1).upper().strip()
                                candidate = ' '.join(candidate.split())
                                # Filter out common non-party words
                                if (len(candidate) >= 2 and 
                                    candidate not in ['DR', 'CR', 'TRF', 'BY', 'TO', 'FROM', 
                                                    'PAID', 'RECEIVED', 'TRANSFER', 'DEPOSIT',
                                                    'WITHDRAWAL', 'BALANCE', 'CHARGES', 'FEE']):
                                    entity = candidate
                                    entity_type = etype
                                    logger.debug(f"Match ({etype}): '{description}' -> '{entity}'")
                                    break
                        except IndexError:
                            continue
                if entity:
                    break
        
        # ========== STEP 3: If entity found, register and return ==========
        if entity:
            normalized = self._normalize_name(entity)
            if normalized and len(normalized) >= 2:
                self._register_entity(normalized, entity, entity_type, amount, is_credit, upi_handle)
                return normalized
        
        # ========== STEP 4: Try advanced extraction ==========
        entity = self._extract_party_advanced(description)
        if entity:
            normalized = self._normalize_name(entity)
            if normalized and len(normalized) >= 2:
                self._register_entity(normalized, entity, 'General', amount, is_credit, upi_handle)
                return normalized
        
        # ========== STEP 5: Last resort - extract meaningful words from description ==========
        # This ensures every transaction has a party associated with it
        cleaned = description
        transaction_words = ['DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'TRANSFER', 'CREDIT', 'DEBIT',
                           'BALANCE', 'CHARGES', 'FEE', 'TAX', 'EMI', 'BILL', 'SALARY',
                           'INTEREST', 'DIVIDEND', 'REFUND', 'REVERSAL', 'CLEARING', 'NO', 'NUM',
                           'BY', 'TO', 'FROM', 'FOR', 'AT', 'ON']
        for word in transaction_words:
            cleaned = re.sub(r'\b' + word + r'\b', ' ', cleaned, flags=re.IGNORECASE)
        
        words = cleaned.strip().split()
        meaningful = [w for w in words if len(w) > 2 and not w.isdigit()]
        
        if meaningful:
            candidate = ' '.join(meaningful[:3]).upper()
            candidate = self._normalize_name(candidate)
            if len(candidate) >= 2:
                self._register_entity(candidate, candidate, 'General', amount, is_credit, upi_handle)
                return candidate
        
        return None
    
    def _extract_party_advanced(self, description):
        """
        Advanced party extraction for complex narrations.
        """
        # Try patterns like "TO PARTYNAME", "FROM PARTYNAME"
        patterns = [
            r'TO\s+([A-Z][A-Za-z\s]{2,})',
            r'FOR\s+([A-Z][A-Za-z\s]{2,})',
            r'FROM\s+([A-Z][A-Za-z\s]{2,})',
            r'AT\s+([A-Z][A-Za-z\s]{2,})',
            r'ON\s+([A-Z][A-Za-z\s]{2,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                candidate = match.group(1).upper().strip()
                candidate = ' '.join(candidate.split())
                # Remove common prefixes
                candidate = re.sub(r'^(TO|FROM|FOR|AT|ON|BY|REF|REFNO|NO|NEW|AC|ACC|ACCOUNT)\s*', '', candidate)
                if len(candidate) >= 2:
                    return candidate
        
        # Last resort: extract meaningful words
        transaction_words = ['DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'TRANSFER', 'CREDIT', 'DEBIT',
                           'BALANCE', 'CHARGES', 'FEE', 'TAX', 'EMI', 'BILL', 'SALARY',
                           'INTEREST', 'DIVIDEND', 'REFUND', 'REVERSAL', 'CLEARING', 'NO', 'NUM']
        cleaned = description
        for word in transaction_words:
            cleaned = re.sub(r'\b' + word + r'\b', ' ', cleaned, flags=re.IGNORECASE)
        
        words = cleaned.strip().split()
        meaningful = [w for w in words if len(w) > 2 and not w.isdigit()]
        
        if meaningful:
            return ' '.join(meaningful[:3]).upper()
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize party name for consistent matching.
        """
        if not name:
            return ""
        
        name = str(name).upper().strip()
        
        # Apply merchant aliases
        if name in self.merchant_aliases:
            name = self.merchant_aliases[name]
        
        # Remove digits and special characters (but keep some context)
        name = re.sub(r'[0-9#*]', ' ', name)
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Remove business suffixes
        for suffix in self.suffixes_to_remove:
            name = re.sub(r'\b' + suffix + r'\b', '', name, flags=re.IGNORECASE).strip()
        
        # Remove common prefixes
        name = re.sub(r'^(?:TO|FROM|FOR|AT|ON|BY|REF|REFNO|NO|NEW|AC|ACC|ACCOUNT|TRANSFER|TRF)\s*', '', name, flags=re.IGNORECASE)
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        return name
    
    def _register_entity(self, normalized: str, original: str, entity_type: str, 
                         amount: float, is_credit: bool, upi_handle: Optional[str] = None):
        """Register an entity in the system."""
        if normalized not in self.entities:
            self.entities[normalized] = {
                'original_names': set([original]),
                'entity_type': entity_type,
                'transaction_count': 0,
                'total_credit': 0.0,
                'total_debit': 0.0,
                'first_seen': None,
                'last_seen': None,
                'upi_handles': set(),
                'phone_numbers': set(),
                'aliases': set()
            }
        
        self.entities[normalized]['original_names'].add(original)
        self.entities[normalized]['transaction_count'] += 1
        
        if is_credit:
            self.entities[normalized]['total_credit'] += abs(amount)
        else:
            self.entities[normalized]['total_debit'] += abs(amount)
        
        if upi_handle:
            self.entities[normalized]['upi_handles'].add(upi_handle)
            self.upi_to_party[upi_handle] = normalized
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def find_similar_entities(self, entity: str, threshold: float = None) -> List[Tuple[str, float]]:
        """Find entities similar to the given entity name."""
        if threshold is None:
            threshold = self.similarity_threshold
        
        normalized = self._normalize_name(entity)
        if not normalized:
            return []
        
        candidates = []
        
        for existing in self.entities.keys():
            if normalized == existing:
                candidates.append((existing, 1.0))
                continue
            
            similarity = self._calculate_similarity(normalized, existing)
            
            # Boost similarity for substring matches
            if normalized in existing or existing in normalized:
                overlap = min(len(normalized), len(existing)) / max(len(normalized), len(existing))
                similarity = max(similarity, overlap)
            
            # Boost similarity for word overlap
            words1 = set(normalized.split())
            words2 = set(existing.split())
            if words1 and words2:
                word_overlap = len(words1 & words2) / len(words1 | words2)
                similarity = max(similarity, word_overlap)
            
            if similarity >= threshold:
                candidates.append((existing, similarity))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
    
    def merge_entities(self, entity1: str, entity2: str) -> bool:
        """Merge two entities into one."""
        norm1 = self._normalize_name(entity1)
        norm2 = self._normalize_name(entity2)
        
        if norm1 not in self.entities or norm2 not in self.entities:
            return False
        
        if norm1 == norm2:
            return True
        
        entity1_data = self.entities[norm1]
        entity2_data = self.entities.pop(norm2)
        
        entity1_data['original_names'].update(entity2_data['original_names'])
        entity1_data['transaction_count'] += entity2_data['transaction_count']
        entity1_data['total_credit'] += entity2_data['total_credit']
        entity1_data['total_debit'] += entity2_data['total_debit']
        entity1_data['upi_handles'].update(entity2_data['upi_handles'])
        
        for upi in entity2_data['upi_handles']:
            self.upi_to_party[upi] = norm1
        
        return True
    
    def auto_merge_similar_entities(self, threshold: float = None) -> int:
        """Automatically merge similar entities."""
        if threshold is None:
            threshold = self.similarity_threshold
        
        merged_count = 0
        processed = set()
        
        for entity in list(self.entities.keys()):
            if entity in processed:
                continue
            
            similar = self.find_similar_entities(entity, threshold * 0.9)
            for similar_entity, score in similar:
                if similar_entity != entity and similar_entity not in processed:
                    if self.merge_entities(entity, similar_entity):
                        merged_count += 1
                        processed.add(similar_entity)
            
            processed.add(entity)
        
        return merged_count
    
    def link_party_relation(self, from_party: str, to_party: str, amount: float, is_credit: bool):
        """Link two parties with a relationship."""
        from_norm = self._normalize_name(from_party)
        to_norm = self._normalize_name(to_party)
        
        if not from_norm or not to_norm:
            return
        
        if is_credit:
            self.entity_relations[to_norm]['received_from'].add(from_norm)
            self.entity_relations[from_norm]['sent_to'].add(to_norm)
        else:
            self.entity_relations[from_norm]['sent_to'].add(to_norm)
            self.entity_relations[to_norm]['received_from'].add(to_norm)
    
    def get_entity_relation_index(self) -> List[Dict]:
        """Get all party relationships."""
        relations = []
        
        for party, data in self.entity_relations.items():
            if party not in self.entities:
                continue
            
            entity_data = self.entities[party]
            total_flow = entity_data['total_credit'] + entity_data['total_debit']
            
            relations.append({
                'party': party,
                'normalized_name': party,
                'entity_type': entity_data.get('entity_type', 'Unknown'),
                'sent_to': sorted(list(data['sent_to'])),
                'received_from': sorted(list(data['received_from'])),
                'shared_refs': sorted(list(data['shared_refs'])),
                'upi_handles': sorted(list(entity_data.get('upi_handles', []))),
                'transfer_count': len(data['sent_to']) + len(data['received_from']),
                'transaction_count': entity_data['transaction_count'],
                'total_credit': round(entity_data['total_credit'], 2),
                'total_debit': round(entity_data['total_debit'], 2),
                'net_flow': round(entity_data['total_credit'] - entity_data['total_debit'], 2),
                'avg_transaction': round(total_flow / max(entity_data['transaction_count'], 1), 2),
            })
        
        relations.sort(key=lambda x: x['transaction_count'], reverse=True)
        return relations
    
    def get_party_ledger_summary(self) -> List[Dict]:
        """Get party ledger summary."""
        summary = []
        
        for party, data in self.entities.items():
            net = data['total_credit'] - data['total_debit']
            summary.append({
                'party_name': party,
                'total_credit': round(data['total_credit'], 2),
                'total_debit': round(data['total_debit'], 2),
                'net_amount': round(net, 2),
                'transaction_count': data['transaction_count'],
                'entity_type': data.get('entity_type', 'Unknown'),
                'upi_handles': list(data.get('upi_handles', []))
            })
        
        summary.sort(key=lambda x: x['total_credit'] + x['total_debit'], reverse=True)
        return summary
    
    def get_statistics(self) -> Dict:
        """Get system statistics."""
        total_transactions = sum(e['transaction_count'] for e in self.entities.values())
        total_amount = sum(e['total_credit'] + e['total_debit'] for e in self.entities.values())
        
        entity_types = defaultdict(int)
        for e in self.entities.values():
            entity_types[e.get('entity_type', 'Unknown')] += 1
        
        return {
            'total_entities': len(self.entities),
            'total_relations': len(self.entity_relations),
            'total_transactions': total_transactions,
            'total_amount': round(total_amount, 2),
            'entity_types': dict(entity_types),
            'upi_clusters': len(self.upi_clusters)
        }
    
    def clear(self):
        """Clear all data."""
        self.entities.clear()
        self.entity_relations.clear()
        self.upi_clusters.clear()
        self.upi_to_party.clear()

