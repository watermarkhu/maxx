function Ai = inv(A)
    D = size(A);
    if numel(D)>2
        error('MATLAB:inv:inputMustBe2D', 'Input must be 2-D.');
    elseif D(1)~=D(2)
        error('MATLAB:square', 'Matrix must be square.')
    end

    I = eye(size(A));
    Ai = A\I;
end
