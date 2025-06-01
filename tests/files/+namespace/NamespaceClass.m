classdef NamespaceClass
% Test namespace class for MATLAB parser
% This class demonstrates classes within namespaces.
%
% Properties:
%   Value - The stored value
%
% Methods:
%   NamespaceClass - Constructor
%   increment - Increases the value
%   getValue - Returns the current value
    
    properties
        Value double = 0
            % The stored value
    end
    
    methods
        function obj = NamespaceClass(init_value)
            % NamespaceClass constructor
            % Initialize the class with a value
            
            arguments
                init_value (1,1) double {mustBeNumeric} = 0
                    % Initial value to store
            end
            
            obj.Value = init_value;
        end
        
        function obj = increment(obj, amount)
            % Increment the stored value
            
            arguments
                obj
                amount (1,1) double {mustBeNumeric} = 1
                    % Amount to increment by
            end
            
            obj.Value = obj.Value + amount;
        end
        
        function value = getValue(obj)
            % Get the current value
            
            arguments
                obj
            end
            
            value = obj.Value;
        end
    end
end
