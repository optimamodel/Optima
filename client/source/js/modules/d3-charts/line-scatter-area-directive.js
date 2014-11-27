define(['./module'], function (module) {
  'use strict';

  module.directive('lineScatterAreaChart', function (d3Charts) {
    return {
      scope: {
        data: '=',
        options: '='
      },
      link: function (scope, element) {
        var dimensions = {
          height: scope.options.height,
          width: scope.options.width
        };

        var chartSize = {
          width: scope.options.width - scope.options.margin.left - scope.options.margin.right,
          height: scope.options.height - scope.options.margin.top - scope.options.margin.bottom
        };

        var svg = d3Charts.createSvg(element[0], dimensions, scope.options.margin);

        // Define svg groups
        var chartGroup = svg.append("g").attr("class", "chart_group");
        var axesGroup = svg.append("g").attr("class", "axes_group");

        // initialize chart instances
        var lineChartInstance = new d3Charts.LineChart(chartGroup, '', chartSize, 100);
        var areaChartInstance = new d3Charts.AreaChart(chartGroup, '', chartSize, 100);
        var scatterChartInstance = new d3Charts.ScatterChart(chartGroup, '', chartSize, 100);

        // fetch & generate data for the graphs
        var lineData = scope.data.line;
        var scatterData = scope.data.scatter;
        var areaLineHighData = scope.data.area.lineHigh;
        var areaLineLowData = scope.data.area.lineLow;
        var areaData = areaLineHighData.map(function (dot, index) {
          return {
            x: dot[0],
            y0: dot[1],
            y1: areaLineLowData[index][1]
          };
        });

        // normalizing all graphs scales to include maximum possible x and y
        var calculatedLineScales = lineChartInstance.scales(areaLineHighData);
        areaChartInstance.scales(areaLineHighData);
        scatterChartInstance.scales(areaLineHighData);

        d3Charts.drawAxes(
          calculatedLineScales,
          scope.options,
          axesGroup,
          chartSize
        );

        // draw graphs
        areaChartInstance.draw(areaData);
        lineChartInstance.draw(lineData);
        scatterChartInstance.draw(scatterData);

      }
    };
  });
});
