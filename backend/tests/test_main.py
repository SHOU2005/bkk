
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import pandas as pd

# Set a dummy environment variable before importing the app
os.environ['DUMMY_ENV_VAR'] = 'dummy_value'

from main import app

client = TestClient(app)

# Test for the root endpoint
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FinSight AI API", "status": "operational"}

# Test for the health check endpoint
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "finsight-ai"}

# Happy path test for /api/analyze
@patch('main.FileProcessor')
@patch('main.TransactionCategorizer')
@patch('main.FraudDetector')
@patch('main.ReportGenerator')
def test_analyze_statement_success(MockReportGenerator, MockFraudDetector, MockTransactionCategorizer, MockFileProcessor):
    # Mock instances
    mock_file_processor = MockFileProcessor.return_value
    mock_categorizer = MockTransactionCategorizer.return_value
    mock_fraud_detector = MockFraudDetector.return_value
    mock_report_generator = MockReportGenerator.return_value

    # Mock data
    mock_transactions = [{'description': 'Test Transaction', 'amount': 100.0}]
    mock_categorized_transactions = [{'description': 'Test Transaction', 'amount': 100.0, 'category': 'Test'}]
    mock_fraud_results = {'flagged_count': 0}
    mock_report_data = {'summary': 'Test Summary'}

    # Mock method return values
    mock_file_processor.extract_transactions.return_value = mock_transactions
    mock_categorizer.categorize_transaction.return_value = {'category': 'Test'}
    mock_fraud_detector.detect_fraud.return_value = mock_fraud_results
    mock_report_generator.generate_report_data.return_value = mock_report_data

    # Perform the request
    df = pd.DataFrame({'Date': ['01/01/2022'], 'Description': ['Test Transaction'], 'Amount': [100.0]})
    df.to_excel('dummy.xls', index=False)
    
    with open('dummy.xls', 'rb') as f:
        response = client.post("/api/analyze", files={"file": ("dummy.xls", f, "application/vnd.ms-excel")})

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert data['metadata']['filename'] == 'dummy.xls'
    assert len(data['transactions']) == 1
    assert data['fraud_analysis'] == mock_fraud_results
    assert data['summary'] == mock_report_data['summary']

    # Cleanup the dummy file
    os.remove('dummy.xls')

# Test for unsupported file type
def test_analyze_statement_unsupported_file():
    with open('dummy.txt', 'w') as f:
        f.write('dummy text content')
    
    with open('dummy.txt', 'rb') as f:
        response = client.post("/api/analyze", files={"file": ("dummy.txt", f, "text/plain")})

    assert response.status_code == 400
    assert response.json()['detail'] == 'Only XLS files are supported'

    os.remove('dummy.txt')

# Test for empty file
def test_analyze_statement_empty_file():
    with open('empty.xls', 'wb') as f:
        pass
    
    with open('empty.xls', 'rb') as f:
        response = client.post("/api/analyze", files={"file": ("empty.xls", f, "application/vnd.ms-excel")})
    
    assert response.status_code == 400
    assert response.json()['detail'] == 'Empty XLS file'

    os.remove('empty.xls')

# Test for no transactions found in XLS
@patch('main.FileProcessor')
def test_analyze_statement_no_transactions(MockFileProcessor):
    mock_file_processor = MockFileProcessor.return_value
    mock_file_processor.extract_transactions.return_value = []

    df = pd.DataFrame({'Date': ['01/01/2022'], 'Description': ['Test Transaction'], 'Amount': [100.0]})
    df.to_excel('dummy.xls', index=False)
    
    with open('dummy.xls', 'rb') as f:
        response = client.post("/api/analyze", files={"file": ("dummy.xls", f, "application/vnd.ms-excel")})

    assert response.status_code == 400
    assert 'No transactions found in XLS' in response.json()['detail']

    os.remove('dummy.xls')

# Test for XLS processing error (malformed XLS)
@patch('main.FileProcessor')
def test_analyze_statement_xls_error(MockFileProcessor):
    mock_file_processor = MockFileProcessor.return_value
    mock_file_processor.extract_transactions.side_effect = ValueError("Invalid XLS structure")

    df = pd.DataFrame({'Date': ['01/01/2022'], 'Description': ['Test Transaction'], 'Amount': [100.0]})
    df.to_excel('dummy.xls', index=False)
    
    with open('dummy.xls', 'rb') as f:
        response = client.post("/api/analyze", files={"file": ("dummy.xls", f, "application/vnd.ms-excel")})

    assert response.status_code == 400
    assert response.json()['detail'] == 'Invalid XLS structure'

    os.remove('dummy.xls')

# Test for unexpected internal server error
@patch('main.FileProcessor')
def test_analyze_statement_internal_error(MockFileProcessor):
    mock_file_processor = MockFileProcessor.return_value
    mock_file_processor.extract_transactions.side_effect = Exception("Unexpected error")

    df = pd.DataFrame({'Date': ['01/01/2022'], 'Description': ['Test Transaction'], 'Amount': [100.0]})
    df.to_excel('dummy.xls', index=False)
    
    with open('dummy.xls', 'rb') as f:
        response = client.post("/api/analyze", files={"file": ("dummy.xls", f, "application/vnd.ms-excel")})

    assert response.status_code == 500
    assert 'Internal server error' in response.json()['detail']

    os.remove('dummy.xls')
