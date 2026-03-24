classdef TestDocstringBefore
    % Test class for docstring_before feature
    
    properties
        % Property with docstring before
        Prop1
        
        % Another property with docstring before
        Prop2
    end
    
    enumeration
        % First enumeration member docstring
        EnumMember1
        
        % Second enumeration member docstring
        EnumMember2
    end
    
    methods
        function obj = TestDocstringBefore(arg1, arg2)
            % Constructor with arguments that have docstrings before
            arguments
                % First argument docstring
                arg1 double
                
                % Second argument docstring
                arg2 string
            end
            obj.Prop1 = arg1;
            obj.Prop2 = arg2;
        end
    end
end
