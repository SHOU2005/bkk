"""
Transaction Categorization Service
Uses NLP-based classification to categorize transactions
"""

import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TransactionCategorizer:
    """Categorize transactions using NLP-based rules and patterns"""
    
    def __init__(self):
        self.category_patterns = self._build_category_patterns()
        self.merchant_risk_keywords = self._build_risk_keywords()
    
    def _build_category_patterns(self) -> Dict[str, List[str]]:
        """Build pattern dictionaries for transaction categorization"""
        return {
            'Income': [
                r'salary', r'payroll', r'wages', r'income', r'credit.*salary',
                r'employer', r'pay.*credit', r'salary.*credit', r'salary.*transfer'
            ],
            'Reward/Cashback': [
                r'reward', r'cashback', r'bonus', r'cash.*back', r'loyalty',
                r'points.*credit', r'reward.*points', r'cashback.*credit'
            ],
            'Refund': [
                r'refund', r'reversal', r'chargeback', r'return.*refund',
                r'refund.*credit', r'payment.*reversal', r'refund.*received'
            ],
            'Bill Payment': [
                r'electricity', r'water', r'gas', r'utility', r'bill.*payment',
                r'phone.*bill', r'mobile.*bill', r'internet.*bill', r'cable.*bill',
                r'electricity.*bill', r'water.*bill', r'gas.*bill'
            ],
            'Subscription': [
                r'subscription', r'netflix', r'spotify', r'prime', r'monthly.*fee',
                r'annually', r'recurring.*subscription', r'auto.*debit.*subscription',
                r'amazon.*prime', r'youtube.*premium', r'subscription.*fee'
            ],
            'EMI': [
                r'emi', r'loan.*emi', r'installment', r'loan.*repayment',
                r'equated.*monthly', r'home.*loan.*emi', r'car.*loan.*emi',
                r'personal.*loan.*emi', r'emi.*payment'
            ],
            'UPI Transfer': [
                r'upi', r'paytm', r'phonepe', r'gpay', r'google.*pay',
                r'bank.*transfer.*upi', r'instant.*payment', r'upi.*transfer',
                r'upi.*payment', r'upi.*to', r'vpa.*upi'
            ],
            'Bank Transfer': [
                r'neft', r'rtgs', r'imps', r'bank.*transfer', r'fund.*transfer',
                r'online.*transfer', r'electronic.*transfer', r'eft', r'wire.*transfer'
            ],
            'Cash Flow': [
                r'atm', r'cash.*withdrawal', r'cash.*atm', r'withdrawal.*atm',
                r'cash.*deposit', r'cash.*transaction'
            ],
            'Loan': [
                r'loan.*disbursement', r'personal.*loan', r'credit.*limit',
                r'loan.*credit', r'advance.*loan', r'loan.*sanction',
                r'loan.*disbursed', r'personal.*loan.*credit'
            ],
            'Investment': [
                r'investment', r'mutual.*fund', r'stocks', r'shares',
                r'fixed.*deposit', r'fd', r'rd', r'recurring.*deposit',
                r'mutual.*fund.*purchase', r'sip.*investment', r'demat.*account'
            ],
            'Expense': [
                r'expense', r'purchase', r'payment', r'debit', r'spending',
                r'merchant.*payment', r'pos.*transaction', r'card.*payment'
            ],
        }
    
    def _build_risk_keywords(self) -> Dict[str, float]:
        """Build risk scoring keywords for merchants/descriptions"""
        return {
            'high_risk': ['casino', 'gambling', 'betting', 'crypto', 'bitcoin', 'forex', 'trading.*platform'],
            'medium_risk': ['online.*payment', 'merchant.*unknown', 'international', 'foreign.*transaction'],
            'low_risk': ['salary', 'utility', 'government', 'bank', 'established.*merchant']
        }
    
    def categorize_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize a single transaction and return category metadata.
        Returns: category, subcategory, merchant_risk_score, narration_risk_confidence, behavioral_deviation
        """
        description = str(transaction.get('description', '')).lower()
        credit = float(transaction.get('credit', 0.0))
        debit = float(transaction.get('debit', 0.0))
        amount = credit if credit > 0 else debit
        
        # Initialize defaults
        category = 'Unknown'
        subcategory = ''
        merchant_risk_score = 0.5  # Default medium risk
        narration_risk_confidence = 0.5
        behavioral_deviation = 'Normal'
        
        # Categorize based on patterns
        matched_category = None
        max_match_length = 0
        
        for cat_key, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    if len(pattern) > max_match_length:
                        max_match_length = len(pattern)
                        matched_category = cat_key
                        break
        
        if matched_category:
            # Use matched category directly (no subcategory splitting for new categories)
            category = matched_category
            subcategory = ''
        else:
            # Fallback categorization based on amount and type
            if credit > 0:
                category = 'Income'
                subcategory = ''
            elif debit > 0:
                category = 'Expense'
                subcategory = ''
        
        # Calculate merchant risk score
        merchant_risk_score = self._calculate_merchant_risk(description)
        
        # Calculate narration risk confidence (based on pattern match quality)
        if matched_category:
            narration_risk_confidence = min(0.95, 0.5 + (max_match_length / 100))
        else:
            narration_risk_confidence = 0.3
        
        # Determine behavioral deviation
        behavioral_deviation = self._determine_behavioral_deviation(transaction, category)
        
        return {
            'category': category,
            'subcategory': subcategory,
            'merchant_risk_score': round(merchant_risk_score, 3),
            'narration_risk_confidence': round(narration_risk_confidence, 3),
            'behavioral_deviation': behavioral_deviation
        }
    
    def _calculate_merchant_risk(self, description: str) -> float:
        """Calculate merchant risk score (0.0 to 1.0)"""
        description_lower = description.lower()
        
        # Check high risk keywords
        for keyword in self.merchant_risk_keywords.get('high_risk', []):
            if re.search(keyword, description_lower):
                return 0.9
        
        # Check medium risk keywords
        for keyword in self.merchant_risk_keywords.get('medium_risk', []):
            if re.search(keyword, description_lower):
                return 0.6
        
        # Check low risk keywords
        for keyword in self.merchant_risk_keywords.get('low_risk', []):
            if re.search(keyword, description_lower):
                return 0.2
        
        # Default medium risk
        return 0.5
    
    def _determine_behavioral_deviation(self, transaction: Dict[str, Any], category: str) -> str:
        """Determine behavioral deviation tag"""
        amount = float(transaction.get('credit', 0.0)) or float(transaction.get('debit', 0.0))
        
        # Large amounts might indicate deviation
        if amount > 100000:  # Threshold for large transactions
            return 'High Value'
        elif amount < 10:  # Very small transactions
            return 'Micro Transaction'
        elif category == 'Unknown':
            return 'Uncategorized'
        else:
            return 'Normal'

