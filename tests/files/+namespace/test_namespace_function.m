function [result] = test_namespace_function(input_value, options)
% Test namespace function for MATLAB parser
% This function demonstrates namespace functionality in MATLAB.
%
% Example:
%   result = namespace.test_namespace_function(5)
%   result = namespace.test_namespace_function(5, 'precision', 2)

    arguments
        input_value (1,1) double {mustBeNumeric}
            % The input value to process
        options.precision (1,1) double {mustBePositive} = 3
            % Precision for output rounding
        options.multiplier (1,1) double = 2
            % Value to multiply the input by
    end

    % Function body
    calculated = input_value * options.multiplier;
    result = round(calculated, options.precision);
end
