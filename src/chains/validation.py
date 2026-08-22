"""SQL validation and guard layer - ensures only safe queries are executed."""
import re
import sqlparse
from typing import Tuple


# Whitelist of allowed tables and their columns
ALLOWED_TABLES = {
    'po_headers': {
        'po_number', 'vendor_id', 'vendor_name', 'po_date',
        'plant', 'currency', 'payment_terms', 'po_status', 'created_by'
    },
    'po_items': {
        'po_number', 'po_line_item', 'material_code', 'material_description',
        'order_qty', 'unit_price', 'currency', 'po_value', 'uom',
        'delivery_date', 'item_status'
    },
    'goods_receipts': {
        'gr_number', 'po_number', 'po_line_item', 'received_qty',
        'receipt_date', 'movement_type', 'storage_location', 'received_by'
    },
    'invoices': {
        'invoice_number', 'po_number', 'vendor_id', 'vendor_name',
        'invoice_date', 'posting_date', 'due_date', 'currency',
        'payment_terms', 'invoice_status', 'posted_by'
    },
    'invoice_items': {
        'invoice_number', 'invoice_line_item', 'po_number', 'po_line_item',
        'material_code', 'material_description', 'invoice_qty', 'unit_price',
        'currency', 'invoice_amount', 'tax_amount', 'total_amount', 'gr_reference'
    }
}

# Dangerous keywords that should never appear
DANGEROUS_KEYWORDS = {
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
    'ATTACH', 'PRAGMA', 'EXEC', 'EXECUTE', 'CREATE'
}


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Validate that SQL is safe to execute.
    
    Rules:
    1. Must be a single SELECT statement
    2. No dangerous keywords (DROP, DELETE, UPDATE, etc.)
    3. Only references tables in the whitelist
    4. Only references columns that exist in those tables
    
    Args:
        sql: SQL query string to validate
        
    Returns:
        Tuple of (is_valid, reason)
        - is_valid: True if query is safe, False otherwise
        - reason: Explanation of why query is invalid (empty string if valid)
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"
    
    sql = sql.strip()
    
    # Check for multiple statements (SQL injection attempt)
    if ';' in sql.rstrip(';'):
        return False, "Multiple SQL statements detected (possible injection)"
    
    # Parse SQL
    try:
        parsed = sqlparse.parse(sql)
    except Exception as e:
        return False, f"Failed to parse SQL: {str(e)}"
    
    if len(parsed) == 0:
        return False, "No SQL statement found"
    
    if len(parsed) > 1:
        return False, "Multiple SQL statements detected"
    
    statement = parsed[0]
    
    # Check if it's a SELECT statement
    if statement.get_type() != 'SELECT':
        return False, f"Only SELECT queries are allowed, got {statement.get_type()}"
    
    # Check for dangerous keywords in the SQL
    sql_upper = sql.upper()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            return False, f"Dangerous keyword detected: {keyword}"
    
    # Simple but effective: check for all table names in the SQL
    sql_lower = sql.lower()
    
    # Check for non-whitelisted tables
    # Split by common SQL keywords and check each word
    words = set()
    for word in sql_lower.replace(',', ' ').replace('(', ' ').replace(')', ' ').split():
        word = word.strip('`;"\' ')
        if word:
            words.add(word)
    
    # Check if any word looks like a table name that's not whitelisted
    potential_tables = words - {'select', 'from', 'where', 'join', 'inner', 'left', 'right', 'outer', 
                                 'on', 'and', 'or', 'as', 'order', 'by', 'group', 'having', 'limit',
                                 'distinct', 'count', 'sum', 'avg', 'max', 'min', 'null', 'not', 'in',
                                 'between', 'like', 'is'}
    
    # Remove numbers and common operators
    potential_tables = {t for t in potential_tables if not t.replace('.', '').replace('*', '').isdigit()}
    potential_tables = {t for t in potential_tables if len(t) > 1}  # Remove single chars
    
    # Check if query references whitelisted tables
    references_whitelisted_table = any(table in sql_lower for table in ALLOWED_TABLES.keys())
    if not references_whitelisted_table:
        return False, "No whitelisted tables referenced in query"
    
    # Check for table names that are NOT in whitelist
    # Look for patterns like "FROM tablename" or "JOIN tablename" or "FROM table1, table2"
    import re
    from_pattern = r'\bFROM\s+([\w\s,]+?)(?:\s+WHERE|\s+JOIN|\s+ORDER|\s+GROUP|\s+LIMIT|;|$)'
    join_pattern = r'\bJOIN\s+(\w+)'
    
    from_matches = re.findall(from_pattern, sql_upper, re.IGNORECASE)
    join_matches = re.findall(join_pattern, sql_upper)
    
    # Process FROM matches (might contain comma-separated tables or aliases)
    all_referenced_tables = set()
    for match in from_matches:
        # Split by comma to handle multiple tables
        tables = [t.strip() for t in match.split(',')]
        for table_expr in tables:
            # Handle table aliases (e.g., "purchase_orders p" or "receipts r")
            # Take only the first word (the actual table name)
            table_parts = table_expr.strip().split()
            if table_parts:
                table_name = table_parts[0].lower()
                all_referenced_tables.add(table_name)
    
    # Add JOIN matches
    all_referenced_tables.update(m.lower() for m in join_matches)
    
    for table in all_referenced_tables:
        # Remove common aliases (single letters or abbreviations)
        table_clean = table.strip()
        if table_clean and table_clean not in ALLOWED_TABLES:
            # Allow single-letter aliases (p, r, etc.)
            if len(table_clean) > 2:
                return False, f"Table not in whitelist: {table_clean}"
    
    # Extract and validate column names from SELECT clause
    # Find the portion between SELECT and FROM
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_upper, re.IGNORECASE | re.DOTALL)
    if select_match:
        select_clause = select_match.group(1)
        
        # Skip validation if using SELECT *
        if select_clause.strip() != '*':
            # Extract column names (simplified - handles basic cases)
            # Remove function calls and aliases
            select_clause_lower = select_clause.lower()
            
            # Split by comma to get individual column expressions
            column_expressions = [c.strip() for c in select_clause_lower.split(',')]
            
            # Build set of all allowed column names
            all_allowed_columns = set()
            for columns in ALLOWED_TABLES.values():
                all_allowed_columns.update(columns)
            
            for expr in column_expressions:
                # Skip aggregate functions
                if any(func in expr for func in ['count(', 'sum(', 'avg(', 'max(', 'min(', 'coalesce(']):
                    continue
                
                # Extract column name (handle aliases and table prefixes)
                # Remove AS aliases
                if ' as ' in expr:
                    expr = expr.split(' as ')[0].strip()
                
                # Remove table prefixes (p., r., etc.)
                if '.' in expr:
                    expr = expr.split('.')[-1].strip()
                
                # Remove operators and extra characters
                expr = expr.strip('*()+-/ ')
                
                # Skip if it's now empty or just whitespace
                if not expr or expr.isspace():
                    continue
                
                # Skip if it's a number or arithmetic expression
                if any(c.isdigit() for c in expr) and any(op in expr for op in ['*', '+', '-', '/']):
                    continue
                
                # Check if this looks like a column name
                if expr and not expr.isdigit() and expr not in ['*', 'null']:
                    # Check against whitelist
                    if expr not in all_allowed_columns:
                        return False, f"Column not in whitelist: {expr}"
    
    return True, ""


def is_safe_query(sql: str) -> bool:
    """
    Quick check if SQL is safe to execute.
    
    Args:
        sql: SQL query string
        
    Returns:
        True if safe, False otherwise
    """
    is_valid, _ = validate_sql(sql)
    return is_valid
