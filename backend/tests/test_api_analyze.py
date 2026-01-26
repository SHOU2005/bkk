import io
from fastapi.testclient import TestClient

from main import app, pdf_processor

client = TestClient(app)


def _fake_transactions(bytes_data):
    # Return two simple transactions so pipeline proceeds
    return [
        {'date': '01/01/2025', 'description': 'Salary credit', 'credit': 50000.0, 'debit': 0.0, 'balance': 100000.0},
        {'date': '05/01/2025', 'description': 'Grocery store debit', 'credit': 0.0, 'debit': 2500.0, 'balance': 97500.0}
    ]


def test_multi_analyze_returns_json_and_results(monkeypatch):
    # Patch the pdf_processor to return deterministic transactions
    monkeypatch.setattr(pdf_processor, 'extract_transactions', lambda b: _fake_transactions(b))

    files = {
        'files': (
            io.BytesIO(b'%PDF-1.4 fake'), 'stmt1.pdf'
        )
    }

    # Send two files as part of multipart - TestClient supports multiple tuples
    response = client.post("/api/analyze/multi", files=[('files', ('stmt1.pdf', b'%PDF-1.4', 'application/pdf')), ('files', ('stmt2.pdf', b'%PDF-1.4', 'application/pdf'))])
    assert response.status_code == 200
    data = response.json()
    assert data.get('status') == 'success'
    assert data.get('metadata', {}).get('files_processed') == 2
    assert data.get('metadata', {}).get('total_transactions') == 4 or data.get('transactions')


def test_single_analyze_error_returns_json(monkeypatch):
    # Patch to raise an exception during extraction
    def _raise(b):
        raise ValueError('Invalid PDF')

    monkeypatch.setattr(pdf_processor, 'extract_transactions', _raise)

    response = client.post("/api/analyze", files={'file': ('bad.pdf', b'%PDF-1.4', 'application/pdf')})
    assert response.status_code == 500
    data = response.json()
    assert data.get('status') == 'error'
    assert 'Invalid PDF' in data.get('detail', '')
