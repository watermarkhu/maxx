classdef GetterSetterClass < handle
    % Class with getter and setter methods

    properties (Dependent)
        ComputedValue
    end

    properties (Access = private)
        InternalValue = 0
    end

    methods
        function value = get.ComputedValue(obj)
            % Getter for ComputedValue
            value = obj.InternalValue * 2;
        end

        function set.ComputedValue(obj, value)
            % Setter for ComputedValue
            obj.InternalValue = value / 2;
        end
    end
end
