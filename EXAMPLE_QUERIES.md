# Example Natural Language Queries

This document provides example natural language questions that demonstrate the Ledger Detective system's capabilities with the enhanced SAP-style procurement database.

---

## Basic Queries

### Count & Summary Questions

**Question:** "How many purchase orders are there?"
```sql
SELECT COUNT(*) FROM po_headers
```

**Question:** "How many line items exist across all purchase orders?"
```sql
SELECT COUNT(*) FROM po_items
```

**Question:** "How many goods receipts have been recorded?"
```sql
SELECT COUNT(*) FROM goods_receipts
```

**Question:** "How many invoices are in the system?"
```sql
SELECT COUNT(*) FROM invoices
```

---

### Vendor Analysis

**Question:** "Which vendors have the most purchase orders?"
```sql
SELECT vendor_name, COUNT(*) as po_count
FROM po_headers
GROUP BY vendor_name
ORDER BY po_count DESC
LIMIT 10
```

**Question:** "What is the total purchase order value by vendor?"
```sql
SELECT 
    poh.vendor_name,
    SUM(poi.po_value) as total_value,
    COUNT(DISTINCT poh.po_number) as po_count
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
GROUP BY poh.vendor_name
ORDER BY total_value DESC
```

**Question:** "Show me all vendors from Chennai plant"
```sql
SELECT DISTINCT vendor_name, vendor_id
FROM po_headers
WHERE plant = 'Plant-Chennai'
```

---

## Reconciliation Queries

### Missing Documents

**Question:** "Which purchase orders have no goods receipts?"
```sql
SELECT poh.po_number, poh.vendor_name, poh.po_date
FROM po_headers poh
WHERE NOT EXISTS (
    SELECT 1 FROM goods_receipts gr 
    WHERE gr.po_number = poh.po_number
)
```

**Question:** "Which goods receipts have no corresponding invoice?"
```sql
SELECT 
    gr.gr_number,
    gr.po_number,
    poi.material_description,
    gr.received_qty,
    poi.unit_price,
    gr.received_qty * poi.unit_price as value
FROM goods_receipts gr
JOIN po_items poi ON gr.po_number = poi.po_number 
    AND gr.po_line_item = poi.po_line_item
WHERE NOT EXISTS (
    SELECT 1 FROM invoice_items ii 
    WHERE ii.po_number = gr.po_number 
        AND ii.po_line_item = gr.po_line_item
)
ORDER BY value DESC
```

**Question:** "Show me purchase orders that have been invoiced but not received"
```sql
SELECT 
    inv.invoice_number,
    inv.po_number,
    poi.material_description
FROM invoices inv
JOIN invoice_items ii ON inv.invoice_number = ii.invoice_number
JOIN po_items poi ON ii.po_number = poi.po_number 
    AND ii.po_line_item = poi.po_line_item
WHERE NOT EXISTS (
    SELECT 1 FROM goods_receipts gr 
    WHERE gr.po_number = ii.po_number 
        AND gr.po_line_item = ii.po_line_item
)
```

---

### Value-Based Queries

**Question:** "Which unmatched receipts are over $100,000?"
```sql
SELECT 
    gr.gr_number,
    gr.po_number,
    poi.material_description,
    gr.received_qty,
    poi.unit_price,
    gr.received_qty * poi.unit_price as receipt_value
FROM goods_receipts gr
JOIN po_items poi ON gr.po_number = poi.po_number 
    AND gr.po_line_item = poi.po_line_item
LEFT JOIN invoice_items ii ON gr.po_number = ii.po_number 
    AND gr.po_line_item = ii.po_line_item
WHERE ii.invoice_number IS NULL
    AND gr.received_qty * poi.unit_price > 100000
ORDER BY receipt_value DESC
```

**Question:** "What is the total amount that has been invoiced but not paid?"
```sql
SELECT SUM(ii.total_amount) as unpaid_amount
FROM invoice_items ii
JOIN invoices inv ON ii.invoice_number = inv.invoice_number
WHERE inv.invoice_status != 'Paid'
```

**Question:** "Show me high-value purchase orders over 500,000"
```sql
SELECT 
    poh.po_number,
    poh.vendor_name,
    SUM(poi.po_value) as total_value
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
GROUP BY poh.po_number, poh.vendor_name
HAVING SUM(poi.po_value) > 500000
ORDER BY total_value DESC
```

---

## Three-Way Match Analysis

**Question:** "Show me the three-way match status for all purchase orders"
```sql
SELECT 
    poi.po_number,
    poi.po_line_item,
    poi.material_description,
    poi.order_qty as ordered,
    COALESCE(SUM(gr.received_qty), 0) as received,
    COALESCE(ii.invoice_qty, 0) as invoiced,
    CASE 
        WHEN SUM(gr.received_qty) IS NULL THEN 'No Receipt'
        WHEN ii.invoice_qty IS NULL THEN 'No Invoice'
        WHEN SUM(gr.received_qty) = ii.invoice_qty 
            AND poi.order_qty = SUM(gr.received_qty) THEN 'Fully Matched'
        WHEN SUM(gr.received_qty) < poi.order_qty THEN 'Partially Received'
        WHEN ii.invoice_qty > SUM(gr.received_qty) THEN 'Over-Invoiced'
        ELSE 'Variance'
    END as match_status
FROM po_items poi
LEFT JOIN goods_receipts gr ON poi.po_number = gr.po_number 
    AND poi.po_line_item = gr.po_line_item
LEFT JOIN invoice_items ii ON poi.po_number = ii.po_number 
    AND poi.po_line_item = ii.po_line_item
GROUP BY poi.po_number, poi.po_line_item
```

**Question:** "Which line items have quantity variances between receipt and invoice?"
```sql
SELECT 
    ii.invoice_number,
    ii.po_number,
    ii.material_description,
    gr_total.total_received,
    ii.invoice_qty,
    ii.invoice_qty - gr_total.total_received as variance
FROM invoice_items ii
JOIN (
    SELECT po_number, po_line_item, SUM(received_qty) as total_received
    FROM goods_receipts
    GROUP BY po_number, po_line_item
) gr_total ON ii.po_number = gr_total.po_number 
    AND ii.po_line_item = gr_total.po_line_item
WHERE ii.invoice_qty != gr_total.total_received
```

---

## Price Variance Analysis

**Question:** "Show me all price variances between PO and invoice"
```sql
SELECT 
    ii.invoice_number,
    ii.po_number,
    ii.material_description,
    poi.unit_price as po_price,
    ii.unit_price as invoice_price,
    ii.unit_price - poi.unit_price as price_variance,
    ii.invoice_qty,
    (ii.unit_price - poi.unit_price) * ii.invoice_qty as total_variance
FROM invoice_items ii
JOIN po_items poi ON ii.po_number = poi.po_number 
    AND ii.po_line_item = poi.po_line_item
WHERE ii.unit_price != poi.unit_price
ORDER BY ABS(total_variance) DESC
```

**Question:** "Which invoices have price increases over 10%?"
```sql
SELECT 
    ii.invoice_number,
    ii.po_number,
    ii.material_description,
    poi.unit_price as po_price,
    ii.unit_price as invoice_price,
    ROUND(((ii.unit_price - poi.unit_price) * 100.0 / poi.unit_price), 2) as price_increase_pct
FROM invoice_items ii
JOIN po_items poi ON ii.po_number = poi.po_number 
    AND ii.po_line_item = poi.po_line_item
WHERE ((ii.unit_price - poi.unit_price) * 100.0 / poi.unit_price) > 10
```

---

## Vendor Performance

**Question:** "Show me vendor performance summary"
```sql
SELECT 
    poh.vendor_name,
    COUNT(DISTINCT poh.po_number) as total_pos,
    COUNT(DISTINCT gr.gr_number) as total_receipts,
    COUNT(DISTINCT inv.invoice_number) as total_invoices,
    SUM(poi.po_value) as total_po_value
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
LEFT JOIN goods_receipts gr ON poi.po_number = gr.po_number 
    AND poi.po_line_item = gr.po_line_item
LEFT JOIN invoices inv ON poh.po_number = inv.po_number
GROUP BY poh.vendor_name
ORDER BY total_po_value DESC
```

**Question:** "Which vendors have the most delivery delays?"
```sql
SELECT 
    poh.vendor_name,
    AVG(julianday(gr.receipt_date) - julianday(poi.delivery_date)) as avg_delay_days,
    COUNT(*) as receipt_count
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
JOIN goods_receipts gr ON poi.po_number = gr.po_number 
    AND poi.po_line_item = gr.po_line_item
WHERE gr.receipt_date > poi.delivery_date
GROUP BY poh.vendor_name
HAVING COUNT(*) >= 3
ORDER BY avg_delay_days DESC
```

---

## Material Analysis

**Question:** "What are the most frequently ordered materials?"
```sql
SELECT 
    material_description,
    COUNT(*) as order_count,
    SUM(order_qty) as total_qty,
    SUM(po_value) as total_value
FROM po_items
GROUP BY material_description
ORDER BY order_count DESC
LIMIT 10
```

**Question:** "Which materials have the highest value?"
```sql
SELECT 
    material_description,
    SUM(po_value) as total_value,
    AVG(unit_price) as avg_price
FROM po_items
GROUP BY material_description
ORDER BY total_value DESC
LIMIT 10
```

---

## Status-Based Queries

**Question:** "Show me all pending invoices"
```sql
SELECT 
    invoice_number,
    vendor_name,
    invoice_date,
    due_date,
    invoice_status
FROM invoices
WHERE invoice_status = 'Pending Approval'
ORDER BY due_date
```

**Question:** "Which purchase orders are still open?"
```sql
SELECT 
    po_number,
    vendor_name,
    po_date,
    po_status
FROM po_headers
WHERE po_status = 'Open'
```

**Question:** "Show me overdue invoices"
```sql
SELECT 
    invoice_number,
    vendor_name,
    due_date,
    invoice_status,
    julianday('now') - julianday(due_date) as days_overdue
FROM invoices
WHERE invoice_status NOT IN ('Paid', 'Cancelled')
    AND due_date < date('now')
ORDER BY days_overdue DESC
```

---

## Plant-Based Analysis

**Question:** "What is the total purchase order value by plant?"
```sql
SELECT 
    poh.plant,
    COUNT(DISTINCT poh.po_number) as po_count,
    SUM(poi.po_value) as total_value
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
GROUP BY poh.plant
ORDER BY total_value DESC
```

**Question:** "Show me all receipts at Mumbai plant"
```sql
SELECT 
    gr.gr_number,
    gr.po_number,
    poi.material_description,
    gr.received_qty,
    gr.receipt_date,
    poh.plant
FROM goods_receipts gr
JOIN po_items poi ON gr.po_number = poi.po_number 
    AND gr.po_line_item = poi.po_line_item
JOIN po_headers poh ON gr.po_number = poh.po_number
WHERE poh.plant = 'Plant-Mumbai'
ORDER BY gr.receipt_date DESC
```

---

## Complex Multi-Condition Queries

**Question:** "Which purchase orders from Anand Steel Traders have unmatched receipts over 100,000?"
```sql
SELECT 
    poh.po_number,
    poh.vendor_name,
    gr.gr_number,
    poi.material_description,
    gr.received_qty * poi.unit_price as receipt_value,
    gr.receipt_date
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
JOIN goods_receipts gr ON poi.po_number = gr.po_number 
    AND poi.po_line_item = gr.po_line_item
LEFT JOIN invoice_items ii ON gr.po_number = ii.po_number 
    AND gr.po_line_item = ii.po_line_item
WHERE poh.vendor_name = 'Anand Steel Traders'
    AND ii.invoice_number IS NULL
    AND gr.received_qty * poi.unit_price > 100000
ORDER BY receipt_value DESC
```

**Question:** "Show me Chennai plant orders with price variances over 5%"
```sql
SELECT 
    poh.po_number,
    poh.plant,
    ii.material_description,
    poi.unit_price as po_price,
    ii.unit_price as invoice_price,
    ROUND(ABS((ii.unit_price - poi.unit_price) * 100.0 / poi.unit_price), 2) as variance_pct
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
JOIN invoice_items ii ON poi.po_number = ii.po_number 
    AND poi.po_line_item = ii.po_line_item
WHERE poh.plant = 'Plant-Chennai'
    AND ABS((ii.unit_price - poi.unit_price) * 100.0 / poi.unit_price) > 5
```

---

## Aggregate & Statistical Queries

**Question:** "What is the average purchase order value?"
```sql
SELECT 
    AVG(total_value) as avg_po_value,
    MIN(total_value) as min_po_value,
    MAX(total_value) as max_po_value
FROM (
    SELECT po_number, SUM(po_value) as total_value
    FROM po_items
    GROUP BY po_number
)
```

**Question:** "What percentage of purchase orders are fully invoiced?"
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN ii.invoice_number IS NOT NULL THEN poi.po_number END) * 100.0 / 
        COUNT(DISTINCT poi.po_number) as pct_invoiced
FROM po_items poi
LEFT JOIN invoice_items ii ON poi.po_number = ii.po_number 
    AND poi.po_line_item = ii.po_line_item
```

---

## Time-Based Analysis

**Question:** "Show me purchase orders created in the last 30 days"
```sql
SELECT 
    po_number,
    vendor_name,
    po_date,
    po_status
FROM po_headers
WHERE julianday('now') - julianday(po_date) <= 30
ORDER BY po_date DESC
```

**Question:** "What is the average time between receipt and invoice?"
```sql
SELECT 
    AVG(julianday(inv.invoice_date) - julianday(gr.receipt_date)) as avg_days
FROM goods_receipts gr
JOIN invoice_items ii ON gr.po_number = ii.po_number 
    AND gr.po_line_item = ii.po_line_item
JOIN invoices inv ON ii.invoice_number = inv.invoice_number
WHERE inv.invoice_date >= gr.receipt_date
```

---

## Notes

- All queries are designed to work with the 5-table SAP-style schema
- Queries demonstrate various complexity levels from simple counts to multi-table joins
- Examples include real-world procurement reconciliation scenarios
- Use these as templates for testing the natural language to SQL translation capability
