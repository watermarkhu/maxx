function result = block_comment_function(x, y)
%{
This is a block comment
that spans multiple lines.
It tests the block comment parsing functionality.

Arguments:
    x (double) - First input
    y (double) - Second input

Returns:
    result (double) - Sum of inputs
%}

%#codegen
result = x + y;
end
