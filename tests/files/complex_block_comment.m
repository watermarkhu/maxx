function result = complex_block_comment(a, b, c)
%{
This is a complex block comment
with multiple paragraphs.

It should handle:
- Multiple lines
- Various formatting
- Nested structures

Arguments:
    a (double) - First parameter
    b (double) - Second parameter
    c (double) - Third parameter

Returns:
    result (double) - The sum of all inputs

Examples:
    >> result = complex_block_comment(1, 2, 3)
    result = 6
%}

result = a + b + c;
end
