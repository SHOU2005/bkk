"""
Report Generation Service
Generates summary data and prepares reports
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate analysis reports and summaries"""
    
    def generate_report_data(
        self,
        transactions: List[Dict[str, Any]],
        fraud_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary report data"""
        
        # Calculate category distribution
        category_counts = {}
        total_credit = 0.0
        total_debit = 0.0
        
        for txn in transactions:
            category = txn.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
            
            total_credit += float(txn.get('credit', 0.0))
            total_debit += float(txn.get('debit', 0.0))
        
        return {
            'summary': {
                'total_transactions': len(transactions),
                'total_credit': round(total_credit, 2),
                'total_debit': round(total_debit, 2),
                'net_balance': round(total_credit - total_debit, 2),
                'category_distribution': category_counts,
                'flagged_count': fraud_results.get('flagged_count', 0),
                'fraud_rate': fraud_results.get('fraud_rate', 0.0)
            }
        }

