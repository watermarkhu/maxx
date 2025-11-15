function result = testFunction(x, y)
    % This is a simple test function
    global myGlobal;

    result = x + y;

    if result > 10
        result = 10;
    end

    data = eval('x + y');
end

function noDocstring(a, b)
    c = a + b;
end
