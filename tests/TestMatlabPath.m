classdef TestMatlabPath < matlab.unittest.TestCase
    
    properties
        collection
    end

    methods (TestClassSetup)
        function setup_pyenv(testClass)
            [status, pythonpath] = system("uv python find");
            if status ~= 0
                error("python:failedToFindPython", ...
                    "Failed to find Python in %s", projectpath);
            end
            if ispc % Use headless python if possible on Windows
                pythondir = fileparts(pythonpath);
                if isfile(fullfile(pythondir, 'pythonw.exe'))
                    pythonpath = fullfile(pythondir, 'pythonw.exe');
                end
            end
            pyenv('Version', strtrim(pythonpath), 'ExecutionMode', 'InProcess');
            test_path = fullfile(fileparts(mfilename('fullpath')), 'files');
            addpath(genpath(test_path));
            testClass.collection = py.maxx.collection.PathsCollection({test_path}, recursive=true);

            logger_path = fullfile(fileparts(fileparts(mfilename('fullpath'))), ...
                'submodule', 'advanced-logger', 'advancedLogger');
            addpath(logger_path)
            testClass.collection.addpath(logger_path);

            logger_test_path = fullfile(fileparts(fileparts(mfilename('fullpath'))), ...
                'submodule', 'advanced-logger', 'test');
            addpath(logger_test_path)
            testClass.collection.addpath(logger_test_path);
        end
    end

    properties (TestParameter)
        call = {
            'MyClass'
            'test_function'
            'plot_axes'
            'my_script'
            'ClassFolder'
            'namespace.NamespaceClass'
            'namespace.test_namespace_function'
            'mlog.Logger'
            'mlog.Level'
            'mlog.Message'
            'mlog.view.LogDisplay'
            'mlog.test.TestLogger'
            }
        testParameter1 = struct("scalar",1,"vector",[1 1]);
    end

    methods(Test)
        function testExample(testCase, call)
            % Example test: verify that 1+1 equals 2
            path_matlab = which(call);
            testCase.verifyNotEmpty(path_matlab, sprintf('Failed to find %s in MATLAB path', call));
            if contains(path_matlab, '@')
                parts = strsplit(path_matlab, filesep);
                [~, filename, ~] = fileparts(path_matlab);
                if strcmp(filename, parts{end-1}(2:end))
                    path_matlab = strjoin(parts(1:end-1), filesep);
                end
            end
            try
                path_python = char(py.str(testCase.collection.get_path(call)));
            catch
                error('Failed to find %s in Python path', call);
            end
            testCase.verifyEqual(path_matlab, path_python, sprintf('Paths do not match for %s', call));
        end
    end
end
