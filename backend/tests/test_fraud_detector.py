import pytest
from services.fraud_detector import FraudDetector
from datetime import datetime, timedelta


def make_txn(amount, date=None, credit=0.0, debit=0.0, desc=''):
    if date is None:
        date = datetime.now().strftime('%d/%m/%Y')
    return {
        'credit': credit,
        'debit': debit,
        'amount': amount,
        'date': date,
        'description': desc,
        'balance': 1000
    }


def test_find_matched_transactions_detects_transfer():
    fd = FraudDetector()

    # Create a credit in one statement and a matching debit in another
    d1 = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
    d2 = datetime.now().strftime('%d/%m/%Y')

    txn1 = {'credit': 500.0, 'debit': 0.0, 'date': d1, 'description': 'NEFT from ABC'}
    txn2 = {'credit': 0.0, 'debit': 500.0, 'date': d2, 'description': 'NEFT to XYZ'}

    matches = fd._find_matched_transactions([txn1, txn2])
    assert isinstance(matches, list)
    assert len(matches) == 1
    m = matches[0]
    assert m['transaction_1']['amount'] == 500.0
    assert m['transaction_2']['amount'] == 500.0
    # date difference should be small
    assert m.get('date_difference_days', 0) <= fd.MATCH_DATE_DELTA_DAYS


def test_detect_fraud_structured_output():
    fd = FraudDetector()
    txns = [
        {'credit': 1000.0, 'debit': 0.0, 'date': datetime.now().strftime('%d/%m/%Y'), 'description': 'Salary'},
        {'credit': 0.0, 'debit': 150.0, 'date': datetime.now().strftime('%d/%m/%Y'), 'description': 'Grocery Store'},
    ]

    res = fd.detect_fraud(txns)
    assert 'flagged_count' in res
    assert 'fraud_rate' in res
    assert 'flagged_transactions' in res
    assert 'all_transactions' in res
    # fraud_probability values should be between 0 and 1
    fps = [t['fraud_probability'] for t in res['all_transactions']]
    assert all(0.0 <= p <= 1.0 for p in fps)


def test_dynamic_threshold_flags_on_larger_dataset():
    fd = FraudDetector()
    txns = []
    # create 100 transactions with occasional large anomalies
    for i in range(100):
        if i % 20 == 0:
            txns.append({'credit': 0.0, 'debit': 10000.0 + i * 10, 'date': datetime.now().strftime('%d/%m/%Y'), 'description': 'Suspicious payment'})
        else:
            txns.append({'credit': 0.0, 'debit': 50.0 + (i % 5), 'date': datetime.now().strftime('%d/%m/%Y'), 'description': 'Routine expense'})

    res = fd.detect_fraud(txns)
    flagged = res.get('flagged_transactions', [])
    # Expect at least one flagged but not excessive
    assert len(flagged) >= 1
    assert len(flagged) < 50
