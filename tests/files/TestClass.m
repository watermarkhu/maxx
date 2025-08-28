classdef TestClass < handle & int16
% Test class for MATLAB parser
% This class is used to test the FileParser functionality.
%
% Properties:
%   Property1 - The first property
%   Property2 - The second property
%
% Methods:
%   method1 - The first method
%   method2 - The second method (private)
%   method3 - The third method
    enumeration
        foo (0) % foo
        bar (42)
            % bar
        baz (69)
    end

    properties
        Property1 double = 0
        Property2 string = ""
    end
    
    methods
        function obj = TestClass(init_val)
            % TestClass constructor
            % Initialize the class properties
            
            arguments
                init_val double {mustBeNumeric} = 0
                    % Initial value for Property1
            end
            
            obj.Property1 = init_val;
        end
        
        function result = method1(obj, input1)
            % First test method
            % This method demonstrates parsing of a class method
            
            arguments
                obj
                input1 (1,:) double {mustBeNumeric}
                    % The input parameter for method1
            end
            
            result = obj.Property1 + input1;
        end
    end
    
    methods (Access = private)
        function method2(obj, options)
            % Second test method (private)
            % This method demonstrates a void method with options
            
            arguments
                obj
                options.text string = "Modified"
                    % Text to set for Property2
                options.flag (1,1) logical = false
                    % Optional flag parameter
            end
            
            if options.flag
                obj.Property2 = upper(options.text);
            else
                obj.Property2 = options.text;
            end
        end
    end
    
    methods (Access = public)
        function result = method3(obj, factor, options)
            % Third test method
            % This method demonstrates multiple arguments with validation
            
            arguments
                obj
                factor (1,1) double {mustBePositive} = 1
                    % Scaling factor for the calculation
                options.precision (1,1) double {mustBeInRange(options.precision, 0, 10)} = 2
                    % Precision for output rounding
            end
            
            result = round(obj.Property1 * factor, options.precision);
        end
    end
end
