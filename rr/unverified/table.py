from sys import stdout


def pprint(table, rows, cols, cell_fmt="{:^10}", cell_sep="|",
           top_left="", indent="", ostream=stdout):
    """A fairly simple function to pretty print data in a tabular format.
    'rows' is a sequence of row headers, i.e. the values that appear in the first column, and
    which are used to retrieve table cells. Likewise, 'cols' is a sequence of column headers,
    which appear in the first row, and are used together with row headers to retrive data from
    the table. 'top_left' is the content that appears in the top-left corner of the table.
    If provided, it should normally contain an explanation of the meaning of the row and column
    headers.
    Note that 'table' should actually be a callable taking 'row' and 'col' as arguments, and
    return the value of the corresponding cell in the table."""
    write = ostream.write
    if len(indent) > 0:
        write(indent)
    write(cell_sep + cell_fmt.format(top_left) + cell_sep)
    for col in cols:
        write(cell_fmt.format(col) + cell_sep)
    write("\n")
    for row in rows:
        if len(indent) > 0:
            write(indent)
        write(cell_sep + cell_fmt.format(row) + cell_sep)
        for col in cols:
            write(cell_fmt.format(table(row, col)) + cell_sep)
        write("\n")
