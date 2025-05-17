classdef ClassFolder
% Test class folder for MATLAB parser
% This class demonstrates class folder functionality in MATLAB.
%
% Properties:
%   Name - The name property
%   Data - The data property
%
% Methods:
%   ClassFolder - Constructor
%   process - Process the data
%   display - Display class information

    properties
        Name string = ""
        Data double = []
    end
    
    methods
        function obj = ClassFolder(name, data)
            % ClassFolder constructor
            % Initialize the class with name and data
            
            arguments
                name string = "DefaultName"
                    % Name of the instance
                data (1,:) double = []
                    % Data array to process
            end
            
            obj.Name = name;
            obj.Data = data;
        end
    end
    
    methods (Access = public)
        function result = process(obj, options)
            % Process the stored data
            % 
            % Returns processed data according to options
            
            arguments
                obj
                options.method (1,1) string {mustBeMember(options.method, ["sum", "mean", "max"])} = "sum"
                    % Method to use for processing: 'sum', 'mean', or 'max'
                options.scale (1,1) double {mustBePositive} = 1
                    % Scaling factor for the result
            end
            
            switch options.method
                case "sum"
                    result = sum(obj.Data) * options.scale;
                case "mean"
                    result = mean(obj.Data) * options.scale;
                case "max"
                    result = max(obj.Data) * options.scale;
            end
        end
    end
    
    methods (Access = private)
        function displayInfo(obj)
            % Display information about the class instance
            
            arguments
                obj
            end
            
            fprintf('ClassFolder: %s with %d data points\n', obj.Name, length(obj.Data));
        end
    end
end
