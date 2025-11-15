function result = comprehensive_test(x, y)
    % Test file for MathWorks coding guidelines

    % Test MW-N001: Variable name length (this one is OK)
    temperature = 25;

    % Test MW-N001: Variable name too long (>32 chars)
    this_is_an_extremely_long_variable_name_that_exceeds_the_limit = 100;

    % Test MW-G001: Global variable usage
    global myGlobalVariable;
    myGlobalVariable = 42;

    % Test MW-G002: Use of eval
    data = eval('x + y');

    % Basic calculation
    result = x + y + temperature;
end

% Test MW-N003: Function name too long (>32 chars)
function output = this_is_a_very_long_function_name_that_clearly_exceeds_thirty_two_characters(input)
    output = input * 2;
end
