classdef (Abstract, Sealed) AbstractClass < handle
    % Abstract and Sealed test class
    % This class tests Abstract and Sealed attributes

    properties (Abstract)
        AbstractProp
    end

    properties (Hidden)
        HiddenProp = 42
    end

    properties (Constant)
        ConstantProp = 'constant'
    end

    properties (Access = protected)
        ProtectedProp = 0
    end

    properties (SetAccess = private)
        PrivateSetProp = 'readonly'
    end

    methods (Abstract)
        result = abstractMethod(obj, input)
    end

    methods (Static)
        function result = staticMethod(x)
            % Static method
            %
            % Arguments:
            %   x (double) - Input value
            result = x * 2;
        end
    end

    methods (Access = private)
        function result = privateMethod(obj)
            % Private method
            result = obj.HiddenProp;
        end
    end

    methods (Hidden)
        function result = hiddenMethod(obj)
            % Hidden method
            result = true;
        end
    end
end
