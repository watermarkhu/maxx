function plot_axes(ax)
    arguments
        ax (1,1) matlab.graphics.axis.Axes = gca 
        % adds the gradient to the plot in axes with handle `ax`. 
    end
    plot(ax);
end
