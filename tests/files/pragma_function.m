function result = pragma_function(x, y)
% Function with pragma comments
%
%#codegen
%#eml
% --8<-- [start:example]
%
% Arguments:
%   x (double) - First input
%   y (double) - Second input
%
% Returns:
%   result (double) - Sum

result = x + y;
end
