function [result] = test_function(input1, input2, options)
% Test function for MATLAB parser
% This function is used to test the FileParser functionality.

    arguments
        input1 (1,:) double
            % The first input parameter
        input2 double {mustBePositive} = 1
            % The second input parameter
        options.text string = "Test"
            % Optional text parameter
    end

    % Function body
    result = input1(1) + input2(1);
    disp(options.text);
    
    % Additional comments
    % This is just for testing parsing
end
