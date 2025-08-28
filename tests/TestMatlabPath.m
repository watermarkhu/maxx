classdef TestMatlabPath < matlab.unittest.TestCase
    
    properties
        collection
    end

    methods (MyClassSetup)
        function setup_pyenv(MyClass)
            [status, pythonpath] = system("uv python find");
            if status ~= 0
                error("python:failedToFindPython", ...
                    "Failed to find Python in %s", projectpath);
            end
            pyenv('Version', strtrim(pythonpath), 'ExecutionMode', 'InProcess');
            test_path = fullfile(fileparts(mfilename('fullpath')), 'files');
            addpath(genpath(test_path))
            MyClass.collection = py.maxx.collection.PathsCollection({test_path}, recursive=true);
        end
    end

    properties (TestParameter)
        call = {
            'MyClass',
            'test_function',
            'plot_axes',
            'my_script',
            'ClassFolder',
            'namespace.NamespaceClass',
            'namespace.test_namespace_function',
        }
    end

    methods(Test)
        function testExample(testCase, call)
            % Example test: verify that 1+1 equals 2
            path_matlab = which(call);
            testCase.verifyNotEmpty(path_matlab, sprintf('Failed to find %s in MATLAB path', call));
            try
                deque = testCase.collection.get_path(call);
                list = py.list(deque);
                path_python = char(py.str(list(0)));
            catch
                testCase.verifyFail(sprintf('Failed to find %s in Python path', call));
            end
            testCase.verifyEqual(path_matlab, path_python, sprintf('Paths do not match for %s', call));
        end
    end
end
