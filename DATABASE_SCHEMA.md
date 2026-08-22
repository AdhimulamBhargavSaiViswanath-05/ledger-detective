# Database Schema Documentation

## Overview

The Ledger Detective system uses a SQLite database with **5 interconnected tables** that represent a complete SAP-style procurement process from purchase order creation to invoice payment. This structure enables sophisticated **three-way matching** (PO → Goods Receipt → Invoice) and various reconciliation scenarios.

**Total Records: 916 across 5 tables**

---

## Database Statistics

| Table | Records | Purpose |
|-------|---------|---------|
| `po_headers` | 120 | Purchase order header information |
| `po_items` | 242 | Purchase order line items (avg 2 per PO) |
| `goods_receipts` | 268 | Goods receipt records (multiple receipts per PO line) |
| `invoices` | 101 | Vendor invoice headers |
| `invoice_items` | 185 | Invoice line items |
| **TOTAL** | **916** | |

---

## Table Schemas

### 1. `po_headers` (120 records)
Purchase order header - one record per purchase order.

| Column | Type | Description |
|--------|------|-------------|
| `po_number` | INTEGER | Primary key - unique PO identifier |
| `vendor_id` | TEXT | Vendor identifier (e.g., V-2041) |
| `vendor_name` | TEXT | Vendor company name |
| `po_date` | TEXT | Date PO was created (YYYY-MM-DD) |
| `plant` | TEXT | Plant/location (e.g., Plant-Chennai) |
| `currency` | TEXT | Currency code (INR, USD, EUR) |
| `payment_terms` | TEXT | Payment terms (Net30, Net45, etc.) |
| `po_status` | TEXT | Status (Open, Closed, Partially Received, Fully Received) |
| `created_by` | TEXT | User who created the PO |

**Sample Data:**
```
po_number: 4500001
vendor_name: Anand Steel Traders
po_date: 2026-03-15
plant: Plant-Chennai
currency: INR
```

---

### 2. `po_items` (242 records)
Purchase order line items - multiple items per PO.

| Column | Type | Description |
|--------|------|-------------|
| `po_number` | INTEGER | Foreign key to po_headers |
| `po_line_item` | INTEGER | Line item number (10, 20, 30...) |
| `material_code` | TEXT | Material SKU code |
| `material_description` | TEXT | Human-readable material name |
| `order_qty` | INTEGER | Quantity ordered |
| `unit_price` | INTEGER | Price per unit |
| `currency` | TEXT | Currency code |
| `po_value` | INTEGER | Total line value (qty × price) |
| `uom` | TEXT | Unit of measure (KG, PC, MT, M) |
| `delivery_date` | TEXT | Expected delivery date |
| `item_status` | TEXT | Line item status |

**Primary Key:** (po_number, po_line_item)

**Sample Data:**
```
po_number: 4500001
po_line_item: 10
material: HR Coil 2mm
order_qty: 1000
unit_price: 3046
po_value: 3046000
```

---

### 3. `goods_receipts` (268 records)
Goods receipt - records when materials are physically received.

| Column | Type | Description |
|--------|------|-------------|
| `gr_number` | TEXT | Primary key - unique GR identifier |
| `po_number` | INTEGER | References po_items |
| `po_line_item` | INTEGER | References po_items |
| `received_qty` | INTEGER | Quantity physically received |
| `receipt_date` | TEXT | Date goods were received |
| `movement_type` | INTEGER | SAP movement type (101 = GR) |
| `storage_location` | TEXT | Where materials were stored |
| `received_by` | TEXT | User who confirmed receipt |

**Foreign Key:** (po_number, po_line_item) → po_items

**Note:** One PO line can have multiple receipts (partial deliveries).

**Sample Data:**
```
gr_number: GR-10001
po_number: 4500001
po_line_item: 20
received_qty: 130 (out of 200 ordered)
receipt_date: 2026-03-25
```

---

### 4. `invoices` (101 records)
Vendor invoice headers - one record per invoice.

| Column | Type | Description |
|--------|------|-------------|
| `invoice_number` | TEXT | Primary key - unique invoice ID |
| `po_number` | INTEGER | References po_headers |
| `vendor_id` | TEXT | Vendor identifier |
| `vendor_name` | TEXT | Vendor company name |
| `invoice_date` | TEXT | Date on vendor's invoice |
| `posting_date` | TEXT | Date posted in system |
| `due_date` | TEXT | Payment due date |
| `currency` | TEXT | Currency code |
| `payment_terms` | TEXT | Payment terms |
| `invoice_status` | TEXT | Status (Pending, Approved, Paid, etc.) |
| `posted_by` | TEXT | User who posted invoice |

**Foreign Key:** po_number → po_headers

**Sample Data:**
```
invoice_number: INV-80001
po_number: 4500001
invoice_date: 2026-04-02
invoice_status: Paid
```

---

### 5. `invoice_items` (185 records)
Invoice line items - what the vendor is billing for.

| Column | Type | Description |
|--------|------|-------------|
| `invoice_number` | TEXT | Foreign key to invoices |
| `invoice_line_item` | INTEGER | Line item number |
| `po_number` | INTEGER | References po_items |
| `po_line_item` | INTEGER | References po_items |
| `material_code` | TEXT | Material SKU |
| `material_description` | TEXT | Material name |
| `invoice_qty` | INTEGER | Quantity being invoiced |
| `unit_price` | INTEGER | Price per unit on invoice |
| `currency` | TEXT | Currency code |
| `invoice_amount` | INTEGER | Line amount (qty × price) |
| `tax_amount` | INTEGER | Tax amount (18% GST) |
| `total_amount` | INTEGER | Total including tax |
| `gr_reference` | TEXT | Related goods receipt number |

**Foreign Keys:**
- invoice_number → invoices
- (po_number, po_line_item) → po_items
- gr_reference → goods_receipts

---

## Relationships

```
po_headers (1)────────(N) po_items
    │                      │
    │                      │
    │                      │ (1)
    │                      │
    │                      └───(N) goods_receipts
    │                      │
    │                      │ (1)
    │ (1)                  │
    │                      └───(N) invoice_items
    │                               │
    └────(N) invoices (1)───────────┘
```

**Key Relationships:**

1. **PO Header to Items:** One PO can have multiple line items
   - `po_headers.po_number` → `po_items.po_number`

2. **PO Items to Goods Receipts:** One line item can have multiple receipts (partial deliveries)
   - `po_items.(po_number, po_line_item)` → `goods_receipts.(po_number, po_line_item)`

3. **PO Header to Invoices:** One PO can have multiple invoices
   - `po_headers.po_number` → `invoices.po_number`

4. **Invoices to Invoice Items:** One invoice can have multiple line items
   - `invoices.invoice_number` → `invoice_items.invoice_number`

5. **Invoice Items to PO Items:** Each invoice line references a PO line
   - `invoice_items.(po_number, po_line_item)` → `po_items.(po_number, po_line_item)`

6. **Invoice Items to Goods Receipts:** Each invoice line references a goods receipt
   - `invoice_items.gr_reference` → `goods_receipts.gr_number`

---

## Three-Way Matching

The database supports SAP-style **three-way matching**:

```
Purchase Order → Goods Receipt → Invoice
```

For a perfect match:
- **Quantity:** PO qty = GR qty = Invoice qty
- **Price:** PO price = Invoice price
- **Reference:** Invoice references the correct GR and PO

---

## Data Scenarios Included

The database contains realistic reconciliation scenarios:

### 1. **Fully Matched Records** (~65%)
- PO quantity = Goods received = Invoice quantity
- PO price = Invoice price
- All documents linked correctly

### 2. **Partially Received Orders** (~20%)
- Goods received < PO quantity
- May or may not have invoice yet
- Common in supply chain delays

### 3. **Price Variances** (~15%)
- Invoice price ≠ PO price (±5-10% variance)
- Requires approval for payment
- Could be legitimate price adjustments

### 4. **Quantity Variances** (~15%)
- Invoice quantity ≠ Received quantity
- Could indicate over/under invoicing
- Requires investigation

### 5. **Over-Receipt** (~5%)
- Received quantity > Ordered quantity
- Vendor shipped extra
- May need return or price adjustment

### 6. **Missing Receipts** (~15%)
- PO exists but no goods receipt
- Order not yet delivered

### 7. **Missing Invoices** (~10%)
- Goods received but no invoice yet
- Vendor hasn't billed yet

### 8. **Over-Invoicing** (~5%)
- Invoice amount > Goods received value
- Potential billing error or fraud

---

## Example Complex Queries

### Find Unmatched Receipts Over $100,000
```sql
SELECT 
    gr.gr_number,
    gr.po_number,
    poi.material_description,
    gr.received_qty * poi.unit_price as receipt_value
FROM goods_receipts gr
JOIN po_items poi ON gr.po_number = poi.po_number 
    AND gr.po_line_item = poi.po_line_item
LEFT JOIN invoice_items ii ON gr.po_number = ii.po_number 
    AND gr.po_line_item = ii.po_line_item
WHERE ii.invoice_number IS NULL
    AND gr.received_qty * poi.unit_price > 100000;
```

### Three-Way Match Status
```sql
SELECT 
    poi.po_number,
    poi.material_description,
    poi.order_qty as ordered,
    SUM(gr.received_qty) as received,
    ii.invoice_qty as invoiced,
    CASE 
        WHEN SUM(gr.received_qty) = 0 THEN 'No Receipt'
        WHEN ii.invoice_qty = 0 THEN 'No Invoice'
        WHEN SUM(gr.received_qty) = ii.invoice_qty THEN 'Matched'
        ELSE 'Variance'
    END as status
FROM po_items poi
LEFT JOIN goods_receipts gr USING (po_number, po_line_item)
LEFT JOIN invoice_items ii USING (po_number, po_line_item)
GROUP BY poi.po_number, poi.po_line_item;
```

### Price Variance Analysis
```sql
SELECT 
    ii.invoice_number,
    ii.material_description,
    poi.unit_price as po_price,
    ii.unit_price as invoice_price,
    (ii.unit_price - poi.unit_price) * ii.invoice_qty as total_variance
FROM invoice_items ii
JOIN po_items poi USING (po_number, po_line_item)
WHERE ii.unit_price != poi.unit_price;
```

### Vendor Performance
```sql
SELECT 
    poh.vendor_name,
    COUNT(DISTINCT poh.po_number) as total_pos,
    SUM(poi.po_value) as total_value,
    COUNT(DISTINCT gr.gr_number) as total_receipts,
    AVG(julianday(gr.receipt_date) - julianday(poi.delivery_date)) as avg_delay_days
FROM po_headers poh
JOIN po_items poi ON poh.po_number = poi.po_number
LEFT JOIN goods_receipts gr ON poi.po_number = gr.po_number
GROUP BY poh.vendor_name;
```

---

## Schema Generation

The database is automatically generated from CSV files using `scripts/generate_enhanced_data.py`. To regenerate:

```bash
cd ledger-detective
python3 scripts/generate_enhanced_data.py
rm data/ledger.db
python3 -c "from src.db import init_database; init_database()"
```

---

## Interview Showcase Points

This database structure demonstrates:

1. **Real-world complexity** - Multiple tables with meaningful relationships
2. **SAP-style three-way matching** - Industry-standard procurement reconciliation
3. **Data quality issues** - Price variances, quantity mismatches, missing documents
4. **Scale** - 900+ records across 5 tables
5. **Complex queries** - Multi-table joins, aggregations, conditional logic
6. **Business scenarios** - Partial deliveries, over-invoicing, vendor performance

Perfect for demonstrating natural language query translation and data-grounded answers!
