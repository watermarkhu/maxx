% Test file for parameter counting rules MW-F002 and MW-F003

% Test MW-F002: Function with 2 inputs (OK - within limit of 6)
function result = twoInputs(a, b)
    result = a + b;
end

% Test MW-F002: Function with 7 inputs (VIOLATION - exceeds limit of 6)
function result = sevenInputs(a, b, c, d, e, f, g)
    result = a + b + c + d + e + f + g;
end

% Test MW-F002: Function with 10 inputs (VIOLATION - exceeds limit of 6)
function result = tenInputs(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10)
    result = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9 + p10;
end

% Test MW-F003: Function with 2 outputs (OK - within limit of 4)
function [x, y] = twoOutputs(input)
    x = input * 2;
    y = input * 3;
end

% Test MW-F003: Function with 5 outputs (VIOLATION - exceeds limit of 4)
function [a, b, c, d, e] = fiveOutputs(input)
    a = input * 1;
    b = input * 2;
    c = input * 3;
    d = input * 4;
    e = input * 5;
end

% Test MW-F003: Function with 7 outputs (VIOLATION - exceeds limit of 4)
function [out1, out2, out3, out4, out5, out6, out7] = sevenOutputs(x)
    out1 = x;
    out2 = x * 2;
    out3 = x * 3;
    out4 = x * 4;
    out5 = x * 5;
    out6 = x * 6;
    out7 = x * 7;
end

% Test both rules: 8 inputs and 6 outputs (both violations)
function [r1, r2, r3, r4, r5, r6] = complexFunction(i1, i2, i3, i4, i5, i6, i7, i8)
    r1 = i1 + i2;
    r2 = i3 + i4;
    r3 = i5 + i6;
    r4 = i7 + i8;
    r5 = i1 * i2;
    r6 = i3 * i4;
end
