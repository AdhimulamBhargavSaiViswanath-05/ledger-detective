"""
Anomaly Detection System - Proactive issue detection and alerts
"""
from typing import List, Dict, Any
from src.db import get_database


class Anomaly:
    """Represents a detected anomaly"""
    
    def __init__(self, anomaly_type: str, severity: str, description: str, 
                 details: Dict[str, Any], recommendation: str):
        self.type = anomaly_type
        self.severity = severity  # 'high', 'medium', 'low'
        self.description = description
        self.details = details
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'severity': self.severity,
            'description': self.description,
            'details': self.details,
            'recommendation': self.recommendation
        }


class AnomalyDetector:
    """Detects anomalies and issues in procurement data"""
    
    def __init__(self):
        self.db = get_database()
    
    def scan_all(self) -> List[Anomaly]:
        """Run all anomaly detection checks"""
        anomalies = []
        
        anomalies.extend(self.detect_price_variances())
        anomalies.extend(self.detect_missing_goods_receipts())
        anomalies.extend(self.detect_three_way_match_failures())
        anomalies.extend(self.detect_duplicate_invoices())
        anomalies.extend(self.detect_quantity_variances())
        
        return anomalies
    
    def detect_price_variances(self) -> List[Anomaly]:
        """Detect price differences between PO and Invoice > 10%"""
        anomalies = []
        
        sql = """
        SELECT 
            i.invoice_number,
            i.po_number,
            ii.material_code,
            poi.unit_price as po_price,
            ii.unit_price as invoice_price,
            ROUND((ii.unit_price - poi.unit_price) * 100.0 / poi.unit_price, 2) as variance_pct
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_number = i.invoice_number
        JOIN po_items poi ON i.po_number = poi.po_number AND ii.material_code = poi.material_code
        WHERE ABS((ii.unit_price - poi.unit_price) * 100.0 / poi.unit_price) > 10
        LIMIT 10
        """
        
        result = self.db.run(sql)
        
        if result and result != '[]':
            count = result.count('(')
            anomalies.append(Anomaly(
                anomaly_type='price_variance',
                severity='high',
                description=f'Found {count} invoice items with price variance > 10%',
                details={
                    'count': count,
                    'threshold': '10%',
                    'sample': result[:200] if len(result) > 200 else result
                },
                recommendation='Review vendor pricing agreements and invoice accuracy'
            ))
        
        return anomalies
    
    def detect_missing_goods_receipts(self) -> List[Anomaly]:
        """Detect old POs without goods receipts"""
        anomalies = []
        
        sql = """
        SELECT 
            ph.po_number,
            ph.vendor_name,
            ph.po_date,
            ph.status
        FROM po_headers ph
        LEFT JOIN goods_receipts gr ON ph.po_number = gr.po_number
        WHERE gr.gr_number IS NULL
        AND ph.status != 'Closed'
        AND julianday('now') - julianday(ph.po_date) > 30
        LIMIT 10
        """
        
        result = self.db.run(sql)
        
        if result and result != '[]':
            count = result.count('(')
            anomalies.append(Anomaly(
                anomaly_type='missing_goods_receipt',
                severity='medium',
                description=f'Found {count} POs older than 30 days with no goods receipt',
                details={
                    'count': count,
                    'age_threshold': '30 days',
                    'sample': result[:200] if len(result) > 200 else result
                },
                recommendation='Follow up with warehouse and suppliers for pending deliveries'
            ))
        
        return anomalies
    
    def detect_three_way_match_failures(self) -> List[Anomaly]:
        """Detect invoices that don't match PO and GR"""
        anomalies = []
        
        sql = """
        SELECT 
            i.invoice_number,
            i.po_number,
            i.total_amount,
            COUNT(DISTINCT gr.gr_number) as gr_count
        FROM invoices i
        LEFT JOIN goods_receipts gr ON i.po_number = gr.po_number
        WHERE gr.gr_number IS NULL
        LIMIT 10
        """
        
        result = self.db.run(sql)
        
        if result and result != '[]':
            count = result.count('(')
            anomalies.append(Anomaly(
                anomaly_type='three_way_match_failure',
                severity='high',
                description=f'Found {count} invoices without matching goods receipts',
                details={
                    'count': count,
                    'issue': 'Invoice without GR - cannot verify receipt',
                    'sample': result[:200] if len(result) > 200 else result
                },
                recommendation='Hold payment until goods receipt is confirmed'
            ))
        
        return anomalies
    
    def detect_duplicate_invoices(self) -> List[Anomaly]:
        """Detect potential duplicate invoice submissions"""
        anomalies = []
        
        sql = """
        SELECT 
            vendor_code,
            po_number,
            total_amount,
            COUNT(*) as duplicate_count
        FROM invoices
        GROUP BY vendor_code, po_number, total_amount
        HAVING COUNT(*) > 1
        """
        
        result = self.db.run(sql)
        
        if result and result != '[]':
            count = result.count('(')
            anomalies.append(Anomaly(
                anomaly_type='duplicate_invoice',
                severity='high',
                description=f'Found {count} potential duplicate invoices',
                details={
                    'count': count,
                    'criteria': 'Same vendor, PO, and amount',
                    'sample': result[:200] if len(result) > 200 else result
                },
                recommendation='Review and reject duplicate invoice submissions'
            ))
        
        return anomalies
    
    def detect_quantity_variances(self) -> List[Anomaly]:
        """Detect quantity differences between GR and Invoice"""
        anomalies = []
        
        sql = """
        SELECT 
            gr.po_number,
            gr.material_code,
            SUM(gr.quantity_received) as total_gr_qty,
            COALESCE(SUM(ii.quantity), 0) as total_invoice_qty,
            ABS(SUM(gr.quantity_received) - COALESCE(SUM(ii.quantity), 0)) as variance
        FROM goods_receipts gr
        LEFT JOIN invoice_items ii ON gr.material_code = ii.material_code
        WHERE ABS(SUM(gr.quantity_received) - COALESCE(SUM(ii.quantity), 0)) > 10
        GROUP BY gr.po_number, gr.material_code
        LIMIT 10
        """
        
        result = self.db.run(sql)
        
        if result and result != '[]':
            count = result.count('(')
            anomalies.append(Anomaly(
                anomaly_type='quantity_variance',
                severity='medium',
                description=f'Found {count} items with quantity variance > 10 units',
                details={
                    'count': count,
                    'threshold': '10 units',
                    'sample': result[:200] if len(result) > 200 else result
                },
                recommendation='Reconcile quantity differences and adjust invoices'
            ))
        
        return anomalies
    
    def generate_alert_message(self, anomalies: List[Anomaly]) -> str:
        """Generate a user-friendly alert message"""
        if not anomalies:
            return "✅ No issues detected. All procurement data looks good!"
        
        high_severity = [a for a in anomalies if a.severity == 'high']
        medium_severity = [a for a in anomalies if a.severity == 'medium']
        
        message = f"⚠️ I detected {len(anomalies)} issues in your procurement data:\n\n"
        
        # High severity first
        for i, anomaly in enumerate(high_severity, 1):
            message += f"{i}. **{anomaly.description}** (High Priority)\n"
            message += f"   → {anomaly.recommendation}\n\n"
        
        # Medium severity
        for i, anomaly in enumerate(medium_severity, len(high_severity) + 1):
            message += f"{i}. {anomaly.description} (Medium Priority)\n"
            message += f"   → {anomaly.recommendation}\n\n"
        
        return message.strip()
