# Test Questions for Ledger Detective

20 questions ranging from simple to complex to test the system's capabilities.

---

## Level 1: Simple Count Queries (Basic)

### 1. How many purchase orders are there?
**Expected:** Count from po_headers table  
**Complexity:** ⭐ Simple SELECT COUNT

### 2. How many invoices do we have?
**Expected:** Count from invoices table  
**Complexity:** ⭐ Simple SELECT COUNT

### 3. How many goods receipts have been recorded?
**Expected:** Count from goods_receipts table  
**Complexity:** ⭐ Simple SELECT COUNT

---

## Level 2: Simple Filtering & Lists (Easy)

### 4. Show me all vendors
**Expected:** List of unique vendor names  
**Complexity:** ⭐ SELECT DISTINCT

### 5. Which plants do we have purchase orders for?
**Expected:** List of unique plants  
**Complexity:** ⭐ SELECT DISTINCT with GROUP BY

### 6. Show me purchase orders from Chennai plant
**Expected:** Filtered list from po_headers  
**Complexity:** ⭐ SELECT with WHERE clause

---

## Level 3: Aggregations (Medium)

### 7. What is the total value of all purchase orders?
**Expected:** SUM of po_value from po_items  
**Complexity:** ⭐⭐ Aggregate function

### 8. What is the total amount that has been invoiced?
**Expected:** SUM of invoice_amount from invoice_items  
**Complexity:** ⭐⭐ Aggregate function

### 9. Which vendor has the most purchase orders?
**Expected:** Vendor name with highest PO count  
**Complexity:** ⭐⭐ GROUP BY with ORDER BY

### 10. What is the average purchase order value?
**Expected:** Average of total PO values  
**Complexity:** ⭐⭐ AVG function with subquery

---

## Level 4: Multi-Table Joins (Medium-Hard)

### 11. Show me all goods receipts for PO 4500001
**Expected:** List of receipts with material details  
**Complexity:** ⭐⭐⭐ JOIN between goods_receipts and po_items

### 12. Which purchase orders have invoices?
**Expected:** POs that exist in invoices table  
**Complexity:** ⭐⭐⭐ JOIN or EXISTS subquery

### 13. Show me vendor performance - how many POs and invoices per vendor
**Expected:** Vendor name with PO count and invoice count  
**Complexity:** ⭐⭐⭐ Multiple JOINs with GROUP BY

---

## Level 5: Missing Document Detection (Hard)

### 14. Which purchase orders have no goods receipts?
**Expected:** POs without any receipts  
**Complexity:** ⭐⭐⭐⭐ LEFT JOIN with NULL check or NOT EXISTS

### 15. Which goods receipts have no corresponding invoice?
**Expected:** Receipts without invoices  
**Complexity:** ⭐⭐⭐⭐ LEFT JOIN across multiple tables

### 16. Show me purchase orders that are fully received but not invoiced
**Expected:** POs with receipts matching order qty but no invoice  
**Complexity:** ⭐⭐⭐⭐ Complex multi-table join with aggregation

---

## Level 6: Value-Based & Variance Detection (Very Hard)

### 17. Show me unmatched receipts over 100000
**Expected:** Receipts without invoices where receipt value > 100000  
**Complexity:** ⭐⭐⭐⭐⭐ Multi-table JOIN with calculated fields and filtering

### 18. Which invoices have price differences from the purchase order?
**Expected:** Invoice items where unit_price != PO unit_price  
**Complexity:** ⭐⭐⭐⭐⭐ JOIN with variance calculation

### 19. Show me the three-way match status for all purchase orders
**Expected:** PO number, ordered qty, received qty, invoiced qty, and status  
**Complexity:** ⭐⭐⭐⭐⭐ Complex 4-table JOIN with CASE logic

### 20. Which line items have quantity variances between receipt and invoice?
**Expected:** Line items where invoice_qty != total received_qty  
**Complexity:** ⭐⭐⭐⭐⭐ Multi-table JOIN with aggregation and variance detection

---

## Expected Behaviors

### ✅ Good Responses
- Returns accurate data from database
- Provides natural language answer
- Shows SQL query used (in some implementations)
- Handles zero results gracefully

### ⚠️ Edge Cases to Watch
- Ambiguous questions (should ask for clarification)
- Out-of-scope questions (should politely refuse)
- Questions about data that doesn't exist
- Very large result sets

### ❌ Bad Responses (System Should Prevent)
- Hallucinated data not in database
- SQL errors or crashes
- Dangerous SQL (DROP, DELETE, etc.)
- Accessing unauthorized tables

---

## Testing Tips

1. **Start Simple:** Test questions 1-6 first to verify basic functionality
2. **Build Complexity:** Move to questions 7-13 for joins and aggregations
3. **Test Edge Cases:** Questions 14-16 test missing document detection
4. **Challenge System:** Questions 17-20 are the most complex scenarios
5. **Mix Order:** Don't test in sequence - mix easy and hard questions

---

## Success Criteria

- **Basic (Q1-6):** Should answer correctly 100% of the time
- **Medium (Q7-13):** Should answer correctly 90%+ of the time
- **Hard (Q14-16):** Should answer correctly 80%+ of the time
- **Very Hard (Q17-20):** Should answer correctly 70%+ of the time

---

## Bonus Questions (If System is Working Well)

21. Show me all partially received purchase orders
22. Which vendor has the highest total invoice amount?
23. Show me overdue invoices (due_date < today and status != Paid)
24. What percentage of purchase orders are fully matched?
25. Show me the top 5 most expensive materials ordered

---

## Quick Reference: Expected Data Counts

- PO Headers: 120
- PO Items: 242
- Goods Receipts: 268
- Invoices: 101
- Invoice Items: 185

Use these to verify count queries are working correctly!
