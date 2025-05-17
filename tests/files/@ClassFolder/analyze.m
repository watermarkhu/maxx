function [stats] = analyze(obj, method)
% Analyze the data in the ClassFolder object
% This method performs statistical analysis on the stored data
%
% Example:
%   cf = ClassFolder('MyData', [1,2,3,4,5]);
%   stats = cf.analyze('full');

    arguments
        obj
        method (1,1) string {mustBeMember(method, ["basic", "full"])} = "basic"
            % Analysis method: 'basic' or 'full'
    end
    
    stats = struct();
    stats.count = numel(obj.Data);
    stats.mean = mean(obj.Data);
    stats.sum = sum(obj.Data);
    
    if method == "full"
        stats.std = std(obj.Data);
        stats.min = min(obj.Data);
        stats.max = max(obj.Data);
        stats.median = median(obj.Data);
    end
end
