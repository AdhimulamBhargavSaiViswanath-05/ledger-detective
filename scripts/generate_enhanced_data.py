"""
Generate enhanced SAP-style procurement data for realistic reconciliation scenarios.

Creates 5 related tables:
1. PO Headers - Purchase order headers
2. PO Items - Line items for each PO
3. Goods Receipts - Physical receipt records
4. Invoices - Vendor invoice headers
5. Invoice Items - Line items on invoices

Includes various reconciliation scenarios:
- Fully matched (PO = GR = Invoice)
- Partially received
- Over/under invoicing
- Missing receipts
- Missing invoices
- Price variances
- Quantity variances
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# Set random seed for reproducibility
random.seed(42)

# Configuration
NUM_PO_HEADERS = 120
NUM_PO_ITEMS_PER_PO = [1, 1, 1, 2, 2, 2, 3, 3, 4]  # Distribution
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 7, 31)

# Master data
VENDORS = [
    ("V-2041", "Anand Steel Traders"),
    ("V-2052", "Bharat Forgings Ltd"),
    ("V-2063", "Coastal Metals"),
    ("V-2074", "Delhi Steel Works"),
    ("V-2085", "Eastern Suppliers"),
    ("V-2096", "Ferro Alloys India"),
    ("V-2107", "Gujarat Industries"),
    ("V-2118", "Hyderabad Metals"),
    ("V-2129", "Indo Steel Corp"),
    ("V-2140", "Jaipur Manufacturing"),
    ("V-2151", "Karnataka Forgings"),
    ("V-2162", "Ludhiana Steel Mills"),
    ("V-2173", "Maharashtra Metals"),
    ("V-2184", "Nagpur Industries"),
    ("V-2195", "Odisha Steel Works"),
]

MATERIALS = [
    ("HR Coil 2mm", 2500, 3000),
    ("MS Round Bar 25mm", 850, 1200),
    ("Stainless Sheet 304", 3200, 4500),
    ("Aluminum Plate 5mm", 1800, 2500),
    ("Copper Wire 10mm", 4500, 6000),
    ("Brass Rod 20mm", 3000, 4000),
    ("Steel Pipe 2inch", 1200, 1800),
    ("Iron Angle 50x50", 650, 900),
    ("Zinc Sheet 1mm", 2200, 3000),
    ("Nickel Bar 15mm", 8000, 10000),
    ("Titanium Plate 3mm", 12000, 15000),
    ("Carbon Steel Sheet", 1500, 2000),
    ("Alloy Steel Bar", 2800, 3500),
    ("Cast Iron Block", 800, 1200),
    ("Forged Steel Component", 5000, 7000),
]

PLANTS = [
    "Plant-Chennai",
    "Plant-Mumbai",
    "Plant-Bangalore",
    "Plant-Pune",
    "Plant-Hyderabad",
    "Plant-Guntur",
    "Plant-Kolkata",
]

CURRENCIES = ["INR", "USD", "EUR"]

PAYMENT_TERMS = ["Net30", "Net45", "Net60", "Immediate", "AdvancePayment"]

INVOICE_STATUS = [
    "Pending Approval",
    "Approved",
    "Paid",
    "Partially Paid",
    "Blocked",
    "Disputed",
]


def random_date(start, end):
    """Generate random date between start and end."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")


def generate_po_headers():
    """Generate purchase order headers."""
    po_headers = []
    
    for i in range(1, NUM_PO_HEADERS + 1):
        po_number = 4500000 + i
        vendor_id, vendor_name = random.choice(VENDORS)
        po_date = random_date(START_DATE, END_DATE)
        plant = random.choice(PLANTS)
        currency = random.choice(CURRENCIES)
        payment_terms = random.choice(PAYMENT_TERMS)
        po_status = random.choice(["Open", "Closed", "Partially Received", "Fully Received"])
        
        po_headers.append({
            "po_number": po_number,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "po_date": po_date,
            "plant": plant,
            "currency": currency,
            "payment_terms": payment_terms,
            "po_status": po_status,
            "created_by": f"USER{random.randint(1, 20):03d}",
        })
    
    return pd.DataFrame(po_headers)


def generate_po_items(po_headers_df):
    """Generate purchase order line items."""
    po_items = []
    
    for _, po_header in po_headers_df.iterrows():
        po_number = po_header["po_number"]
        currency = po_header["currency"]
        num_items = random.choice(NUM_PO_ITEMS_PER_PO)
        
        for line_item in range(1, num_items + 1):
            material_desc, min_price, max_price = random.choice(MATERIALS)
            unit_price = random.randint(min_price, max_price)
            order_qty = random.choice([50, 100, 150, 200, 250, 300, 500, 1000])
            po_value = unit_price * order_qty
            
            delivery_date = datetime.strptime(po_header["po_date"], "%Y-%m-%d") + timedelta(days=random.randint(14, 60))
            
            po_items.append({
                "po_number": po_number,
                "po_line_item": line_item * 10,
                "material_code": f"MAT-{random.randint(10000, 99999)}",
                "material_description": material_desc,
                "order_qty": order_qty,
                "unit_price": unit_price,
                "currency": currency,
                "po_value": po_value,
                "uom": random.choice(["KG", "PC", "MT", "M"]),
                "delivery_date": delivery_date.strftime("%Y-%m-%d"),
                "item_status": random.choice(["Open", "Closed", "Partially Received", "Fully Received"]),
            })
    
    return pd.DataFrame(po_items)


def generate_goods_receipts(po_items_df):
    """Generate goods receipt records."""
    goods_receipts = []
    gr_counter = 10001
    
    for _, po_item in po_items_df.iterrows():
        # 85% chance of having at least one receipt
        if random.random() < 0.85:
            po_number = po_item["po_number"]
            po_line_item = po_item["po_line_item"]
            order_qty = po_item["order_qty"]
            
            # Determine receipt scenario
            scenario = random.choices(
                ["full", "partial_one", "partial_multi", "over"],
                weights=[0.60, 0.20, 0.15, 0.05]
            )[0]
            
            delivery_date = datetime.strptime(po_item["delivery_date"], "%Y-%m-%d")
            
            if scenario == "full":
                # Full receipt in one go
                receipt_date = delivery_date + timedelta(days=random.randint(-5, 10))
                goods_receipts.append({
                    "gr_number": f"GR-{gr_counter}",
                    "po_number": po_number,
                    "po_line_item": po_line_item,
                    "received_qty": order_qty,
                    "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                    "movement_type": "101",
                    "storage_location": f"SL{random.randint(1, 5):02d}",
                    "received_by": f"USER{random.randint(1, 20):03d}",
                })
                gr_counter += 1
                
            elif scenario == "partial_one":
                # One partial receipt
                partial_qty = int(order_qty * random.uniform(0.5, 0.9))
                receipt_date = delivery_date + timedelta(days=random.randint(-5, 10))
                goods_receipts.append({
                    "gr_number": f"GR-{gr_counter}",
                    "po_number": po_number,
                    "po_line_item": po_line_item,
                    "received_qty": partial_qty,
                    "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                    "movement_type": "101",
                    "storage_location": f"SL{random.randint(1, 5):02d}",
                    "received_by": f"USER{random.randint(1, 20):03d}",
                })
                gr_counter += 1
                
            elif scenario == "partial_multi":
                # Multiple partial receipts
                remaining_qty = order_qty
                num_receipts = random.randint(2, 3)
                
                for i in range(num_receipts):
                    if i == num_receipts - 1:
                        # Last receipt gets remaining
                        receipt_qty = remaining_qty
                    else:
                        receipt_qty = int(remaining_qty * random.uniform(0.3, 0.6))
                    
                    receipt_date = delivery_date + timedelta(days=random.randint(-5 + (i*7), 10 + (i*7)))
                    goods_receipts.append({
                        "gr_number": f"GR-{gr_counter}",
                        "po_number": po_number,
                        "po_line_item": po_line_item,
                        "received_qty": receipt_qty,
                        "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                        "movement_type": "101",
                        "storage_location": f"SL{random.randint(1, 5):02d}",
                        "received_by": f"USER{random.randint(1, 20):03d}",
                    })
                    remaining_qty -= receipt_qty
                    gr_counter += 1
                    
            elif scenario == "over":
                # Over-receipt (more than ordered)
                over_qty = int(order_qty * random.uniform(1.05, 1.15))
                receipt_date = delivery_date + timedelta(days=random.randint(-5, 10))
                goods_receipts.append({
                    "gr_number": f"GR-{gr_counter}",
                    "po_number": po_number,
                    "po_line_item": po_line_item,
                    "received_qty": over_qty,
                    "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                    "movement_type": "101",
                    "storage_location": f"SL{random.randint(1, 5):02d}",
                    "received_by": f"USER{random.randint(1, 20):03d}",
                })
                gr_counter += 1
    
    return pd.DataFrame(goods_receipts)


def generate_invoices(po_headers_df, goods_receipts_df):
    """Generate vendor invoice headers."""
    invoices = []
    invoice_counter = 80001
    
    # Create invoice map for POs that have receipts
    po_with_receipts = goods_receipts_df["po_number"].unique()
    
    for po_number in po_with_receipts:
        # 90% chance of having an invoice if goods are received
        if random.random() < 0.90:
            po_header = po_headers_df[po_headers_df["po_number"] == po_number].iloc[0]
            
            # Get latest receipt date for this PO
            po_receipts = goods_receipts_df[goods_receipts_df["po_number"] == po_number]
            latest_receipt = datetime.strptime(max(po_receipts["receipt_date"]), "%Y-%m-%d")
            invoice_date = latest_receipt + timedelta(days=random.randint(1, 15))
            
            due_date = invoice_date + timedelta(days=30)
            
            invoices.append({
                "invoice_number": f"INV-{invoice_counter}",
                "po_number": po_number,
                "vendor_id": po_header["vendor_id"],
                "vendor_name": po_header["vendor_name"],
                "invoice_date": invoice_date.strftime("%Y-%m-%d"),
                "posting_date": (invoice_date + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d"),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "currency": po_header["currency"],
                "payment_terms": po_header["payment_terms"],
                "invoice_status": random.choice(INVOICE_STATUS),
                "posted_by": f"USER{random.randint(1, 20):03d}",
            })
            invoice_counter += 1
    
    return pd.DataFrame(invoices)


def generate_invoice_items(invoices_df, po_items_df, goods_receipts_df):
    """Generate invoice line items with various matching scenarios."""
    invoice_items = []
    
    for _, invoice in invoices_df.iterrows():
        po_number = invoice["po_number"]
        
        # Get PO items for this PO
        po_items = po_items_df[po_items_df["po_number"] == po_number]
        
        for _, po_item in po_items.iterrows():
            po_line_item = po_item["po_line_item"]
            
            # Get goods receipts for this line item
            receipts = goods_receipts_df[
                (goods_receipts_df["po_number"] == po_number) &
                (goods_receipts_df["po_line_item"] == po_line_item)
            ]
            
            if len(receipts) > 0:
                total_received = receipts["received_qty"].sum()
                unit_price = po_item["unit_price"]
                
                # Determine invoice scenario
                scenario = random.choices(
                    ["exact_match", "price_variance", "qty_variance", "over_invoice"],
                    weights=[0.65, 0.15, 0.15, 0.05]
                )[0]
                
                if scenario == "exact_match":
                    invoice_qty = total_received
                    invoice_price = unit_price
                    
                elif scenario == "price_variance":
                    invoice_qty = total_received
                    # 5-10% price variance
                    variance = random.uniform(-0.10, 0.10)
                    invoice_price = int(unit_price * (1 + variance))
                    
                elif scenario == "qty_variance":
                    # Invoice for less than received
                    invoice_qty = int(total_received * random.uniform(0.85, 0.95))
                    invoice_price = unit_price
                    
                elif scenario == "over_invoice":
                    # Invoice for more than received
                    invoice_qty = int(total_received * random.uniform(1.05, 1.15))
                    invoice_price = unit_price
                
                invoice_amount = invoice_qty * invoice_price
                
                invoice_items.append({
                    "invoice_number": invoice["invoice_number"],
                    "invoice_line_item": po_line_item,
                    "po_number": po_number,
                    "po_line_item": po_line_item,
                    "material_code": po_item["material_code"],
                    "material_description": po_item["material_description"],
                    "invoice_qty": invoice_qty,
                    "unit_price": invoice_price,
                    "currency": invoice["currency"],
                    "invoice_amount": invoice_amount,
                    "tax_amount": int(invoice_amount * 0.18),  # 18% GST
                    "total_amount": int(invoice_amount * 1.18),
                    "gr_reference": receipts.iloc[0]["gr_number"],
                })
    
    return pd.DataFrame(invoice_items)


def main():
    """Generate all tables and save to CSV."""
    print("Generating enhanced SAP-style procurement data...\n")
    
    # Generate tables in order
    print("1. Generating PO Headers...")
    po_headers_df = generate_po_headers()
    print(f"   Created {len(po_headers_df)} PO headers")
    
    print("2. Generating PO Items...")
    po_items_df = generate_po_items(po_headers_df)
    print(f"   Created {len(po_items_df)} PO line items")
    
    print("3. Generating Goods Receipts...")
    goods_receipts_df = generate_goods_receipts(po_items_df)
    print(f"   Created {len(goods_receipts_df)} goods receipts")
    
    print("4. Generating Invoices...")
    invoices_df = generate_invoices(po_headers_df, goods_receipts_df)
    print(f"   Created {len(invoices_df)} invoices")
    
    print("5. Generating Invoice Items...")
    invoice_items_df = generate_invoice_items(invoices_df, po_items_df, goods_receipts_df)
    print(f"   Created {len(invoice_items_df)} invoice line items")
    
    # Save to CSV
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("\nSaving CSV files...")
    po_headers_df.to_csv(output_dir / "po_headers.csv", index=False)
    po_items_df.to_csv(output_dir / "po_items.csv", index=False)
    goods_receipts_df.to_csv(output_dir / "goods_receipts.csv", index=False)
    invoices_df.to_csv(output_dir / "invoices.csv", index=False)
    invoice_items_df.to_csv(output_dir / "invoice_items.csv", index=False)
    
    print("\n✓ Data generation complete!")
    print("\nSummary:")
    print(f"  - PO Headers: {len(po_headers_df)} records")
    print(f"  - PO Items: {len(po_items_df)} records")
    print(f"  - Goods Receipts: {len(goods_receipts_df)} records")
    print(f"  - Invoices: {len(invoices_df)} records")
    print(f"  - Invoice Items: {len(invoice_items_df)} records")
    print(f"  - Total: {len(po_headers_df) + len(po_items_df) + len(goods_receipts_df) + len(invoices_df) + len(invoice_items_df)} records")
    
    # Print some statistics
    print("\nData Statistics:")
    print(f"  - POs with receipts: {len(goods_receipts_df['po_number'].unique())} / {len(po_headers_df)}")
    print(f"  - POs with invoices: {len(invoices_df)} / {len(po_headers_df)}")
    print(f"  - Avg line items per PO: {len(po_items_df) / len(po_headers_df):.1f}")
    print(f"  - Avg receipts per PO: {len(goods_receipts_df) / len(goods_receipts_df['po_number'].unique()):.1f}")


if __name__ == "__main__":
    main()
