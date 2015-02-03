define(['./module', 'angular', 'd3'], function (module, angular, d3) {
  'use strict';

  module.controller('AnalysisOptimizationController', function ($scope, $http,
    $interval, meta, cfpLoadingBar, CONFIG, modalService, graphTypeFactory, optimizations) {

      $scope.chartsForDataExport = [];

      $scope.meta = meta;
      $scope.types = graphTypeFactory.types;
      // reset graph types every time you come to this page
      angular.extend($scope.types, angular.copy(CONFIG.GRAPH_TYPES));

      $scope.needData = $scope.meta.progs === undefined;
      $scope.activeTab = 1;
      var errorMessages = [];

      var statusEnum = {
        NOT_RUNNING: { text: "", isActive: false },
        RUNNING: { text: "Optimization is running", isActive: true },
        REQUESTED_TO_STOP : { text:"Optimization is requested to stop", isActive: true },
        STOPPING : { text:"Optimization is stopping", isActive: true },
        CHECKING: {text:"Checking for existing optimization", isActive: false}
      };

      $scope.optimizationStatus = statusEnum.NOT_RUNNING;
      $scope.optimizations = [];

      // According to angular best-practices we should wrap every object/value
      // inside a wrapper object. This is due the fact that directives like ng-if
      // always create a child scope & the reference can get lost.
      // see https://github.com/angular/angular.js/wiki/Understanding-Scopes
      $scope.state = {
        activeOptimizationName: undefined,
        optimisationGraphs: [],
        financialGraphs: [],
        radarCharts: [],
        pieCharts: [],
        stackedBarChart: undefined,
        outcomeChart: undefined,
        isTestRun: false
      };

      // cache placeholder
      var cachedResponse = null;

      // Set defaults
      $scope.params = {};
      $scope.params.timelimit = 3600;

      // Objectives
      $scope.params.objectives = {};
      $scope.params.objectives.what = 'outcome';

      // Outcome objectives defaults
      $scope.params.objectives.outcome = {};
      $scope.params.objectives.outcome.inci = false;
      $scope.params.objectives.outcome.daly = false;
      $scope.params.objectives.outcome.death = false;
      $scope.params.objectives.outcome.costann = false;

      // Money objectives defaults
      $scope.params.objectives.money = {};
      $scope.params.objectives.money.objectives = {};
      $scope.params.objectives.money.objectives.dalys = {};
      $scope.params.objectives.money.objectives.dalys.use = false;
      $scope.params.objectives.money.objectives.deaths = {};
      $scope.params.objectives.money.objectives.deaths.use = false;
      $scope.params.objectives.money.objectives.inci = {};
      $scope.params.objectives.money.objectives.inci.use = false;
      $scope.params.objectives.money.objectives.inciinj = {};
      $scope.params.objectives.money.objectives.inciinj.use = false;
      $scope.params.objectives.money.objectives.incisex = {};
      $scope.params.objectives.money.objectives.incisex.use = false;
      $scope.params.objectives.money.objectives.mtct = {};
      $scope.params.objectives.money.objectives.mtct.use = false;
      $scope.params.objectives.money.objectives.mtctbreast = {};
      $scope.params.objectives.money.objectives.mtctbreast.use = false;
      $scope.params.objectives.money.objectives.mtctnonbreast = {};
      $scope.params.objectives.money.objectives.mtctnonbreast.use = false;

      // Default program weightings
      $scope.params.objectives.money.costs = [];
      if(meta.progs) {
        $scope.programs = meta.progs.long;
        $scope.programCodes = meta.progs.short;

        for ( var i = 0; i < meta.progs.short.length; i++ ) {
          $scope.params.objectives.money.costs[i] = 100;
        }

        // Constraints Defaults
        $scope.params.constraints = {};
        $scope.params.constraints.txelig = 1;
        $scope.params.constraints.dontstopart = true;

        $scope.params.constraints.yeardecrease = [];
        $scope.params.constraints.yearincrease = [];
        $scope.params.constraints.totaldecrease = [];
        $scope.params.constraints.totalincrease = [];
        $scope.params.constraints.coverage = [];

        // Initialize program constraints models
        for ( var i = 0; i < meta.progs.short.length; i++ ) {
          $scope.params.constraints.yeardecrease[i] = {};
          $scope.params.constraints.yeardecrease[i].use = false;
          $scope.params.constraints.yeardecrease[i].by = 100;

          $scope.params.constraints.yearincrease[i] = {};
          $scope.params.constraints.yearincrease[i].use = false;
          $scope.params.constraints.yearincrease[i].by = 100;

          $scope.params.constraints.totaldecrease[i] = {};
          $scope.params.constraints.totaldecrease[i].use = false;
          $scope.params.constraints.totaldecrease[i].by = 100;

          $scope.params.constraints.totalincrease[i] = {};
          $scope.params.constraints.totalincrease[i].use = false;
          $scope.params.constraints.totalincrease[i].by = 100;

          $scope.params.constraints.coverage[i] = {};
          $scope.params.constraints.coverage[i].use = false;
          $scope.params.constraints.coverage[i].level = 0;
          $scope.params.constraints.coverage[i].year = undefined;
        }
      }

    var optimizationTimer;

    var linesGraphOptions = {
      height: 200,
      width: 320,
      margin: CONFIG.GRAPH_MARGINS,
      xAxis: {
        axisLabel: 'Year',
        tickFormat: function (d) {
          return d3.format('d')(d);
        }
      },
      yAxis: {
        axisLabel: ''
      }
    };

    /*
    * Returns an graph based on the provided yData.
    *
    * yData should be an array where each entry contains an array of all
    * y-values from one line.
    */
    var generateGraph = function(yData, xData, title, legend, xLabel, yLabel) {
      var linesGraphData = {
        lines: [],
        scatter: []
      };

      var graph = {
        options: angular.copy(linesGraphOptions),
        data: angular.copy(linesGraphData)
      };

      graph.options.title = title;
      graph.options.legend = legend;

      graph.options.xAxis.axisLabel = xLabel;
      graph.options.yAxis.axisLabel = yLabel;

      _(yData).each(function(lineData) {
        graph.data.lines.push(_.zip(xData, lineData));
      });

      return graph;
    };

    /**
     * Returns a prepared chart object for a pie chart.
     */
    var generatePieChart = function(data, legend) {
      var graphData = [];

      var options = {
        height: 350,
        width: 350,
        margin: {
          top: 20,
          right: 100,
          bottom: 20,
          left: 100
        },
        title: data.name
      };

      graphData = _(data).map(function (value, index) {
        return { value: value, label: legend[index] };
      });

      return {
        'data': {slices: graphData},
        'options': options
      };
    };

    /**
     * Returns all pie charts.
     */
    var preparePieCharts = function (data) {

      var charts = [];

      if (data[0] && data[0].piedata) {
        charts.push(generatePieChart(data[0].piedata, data[0].legend));
      }

      if (data[1] && data[1].piedata) {
        charts.push(generatePieChart(data[1].piedata, data[0].legend)); // not set for data[1]
      }

      return charts;
    };

    /**
     * Returns a prepared chart object for a radar chart.
     */
    var generateRadarChart = function(data, legend) {
      var graphData = [{axes: []}, {axes: []}, {axes: []}];

      var options = {
        legend: [],
        title: data.name
      };

      graphData[0].axes = _(data.low).map(function (value, index) {
        return { value: value, axis: legend[index] };
      });
      graphData[1].axes = _(data.best).map(function (value, index) {
        return { value: value, axis: legend[index] };
      });
      graphData[2].axes = _(data.high).map(function (value, index) {
        return { value: value, axis: legend[index] };
      });

      return {
        'data': graphData,
        'options': options,
        'radarAxesName': 'Programs'
      };
    };

    /**
     * Returns all radar charts.
     */
    var prepareRadarCharts = function (data) {

      var charts = [];

      if (data[0] && data[0].radardata) {
        charts.push(generateRadarChart(data[0].radardata, data[0].legend));
      }

      if (data[1] && data[1].radardata) {
        charts.push(generateRadarChart(data[1].radardata, data[0].legend)); // not set for data[1]
      }

      return charts;
    };

    /**
     * Returns a prepared chart object for a pie chart.
     */
    var generateStackedBarChart = function(yData, xData, legend, title) {
      var graphData = [];

      var options = {
        height: 200,
        width: 700,
        margin: CONFIG.GRAPH_MARGINS,
        xAxis: {
          axisLabel: 'Year'
        },
        yAxis: {
          axisLabel: ''
        },
        legend: legend,
        title: title
      };


      graphData = _(xData).map(function(xValue, index) {
        var yValues = _(yData).map(function(yEntry) { return yEntry[index]; });
        return [xValue, yValues];
      });

      return {
        'data': {bars: graphData},
        'options': options
      };
    };

    /**
     * Returns a stacked bar chart.
     */
    var prepareStackedBarChart = function (data) {
      return generateStackedBarChart(data.stackdata, data.xdata, data.legend,
        data.title);
    };

    /**
     * Returns a prepared chart object for a pie chart.
     */
    var generateMultipleBudgetsChart = function(yData, xData, labels, legend,
        title, leftTitle, rightTitle) {
      var graphData = [];

      var options = {
        height: 200,
        width: 700,
        margin: CONFIG.GRAPH_MARGINS,
        xAxis: {
          axisLabel: ''
        },
        yAxis: {
          axisLabel: 'Spent'
        },
        legend: legend,
        title: title,
        leftTitle: leftTitle,
        rightTitle: rightTitle
      };

      graphData = _(xData).map(function (xValue, index) {
        return [labels[index], xValue, yData[index]];
      });

      return {
        'data': {bars: graphData},
        'options': options
      };
    };

    /**
     * Returns a stacked bar chart.
     */
    var prepareMultipleBudgetsChart = function (data, outcomeData) {
      return generateMultipleBudgetsChart(data.bardata, outcomeData.bardata,
        data.xlabels, data.legend, data.title, outcomeData.title, data.ylabel);
      };

    /**
     * Regenerate graphs based on the response and type settings in the UI.
     */
    var prepareOptimisationGraphs = function (response) {
      var graphs = [];

      if (!response) {
        return graphs;
      }

      _($scope.types.population).each(function (type) {

        if (type === undefined) return;
        var data = response[type.id];
        if (data !== undefined) {

          // generate graphs showing the overall data for this type
          if (type.total) {
            var graph = generateGraph(
              data.tot.data, response.tvec,
              data.tot.title, data.tot.legend,
              data.xlabel, data.tot.ylabel
            );
            graphs.push(graph);
          }

          // generate graphs for this type for each population
          if (type.byPopulation) {
            _(data.pops).each(function (population) {
              var graph = generateGraph(
                population.data, response.tvec,
                population.title, population.legend,
                data.xlabel, population.ylabel
              );
              graphs.push(graph);
            });
          }
        }
      });

      return graphs;
    };

    /**
     * Returns a financial graph.
     */
    var generateFinancialGraph = function(data) {
      var graph = generateGraph(data.data, data.xdata, data.title, data.legend, data.xlabel, data.ylabel);
      return graph;
    };

    var prepareFinancialGraphs = function(graphData) {
      var graphs = [];

      if (graphData === undefined) return graphs;
      _($scope.types.financial).each(function (type) {
        if (type === undefined) return;
        // existing = cost for current people living with HIV
        // future = cost for future people living with HIV
        // costann = annual costs
        // costcum = cumulative costs
        if (type.annual) {
          var annualData = graphData.costann? graphData.costann[type.id][$scope.types.annualCost]:undefined;
          if(annualData) graphs.push(generateFinancialGraph(annualData));
        }

        if (type.cumulative) {
          var cumulativeData = graphData.costcum? graphData.costcum[type.id]:undefined;
          if (cumulativeData) graphs.push(generateFinancialGraph(cumulativeData));
        }
      });
      return graphs;
    };


    var prepareOutcomeChart = function(data) {
      if (data === undefined) return undefined;

      var chart = {
        options: angular.copy(linesGraphOptions),
        data: {
          lines: [],
          scatter: []
        }
      };
      chart.options.height = 320;
      chart.options.margin.bottom = 165;

      chart.options.title = data.title;
      chart.options.xAxis.axisLabel = data.xlabel;
      chart.options.yAxis.axisLabel = data.ylabel;
      chart.data.lines.push(_.zip(data.xdata, data.ydata));
      return chart;
    };

    // makes all graphs to recalculate and redraw
    function drawGraphs() {
      if (!cachedResponse || !cachedResponse.plot) return;
      if (cachedResponse.plot[0].alloc instanceof Array) {
        $scope.state.pieCharts = preparePieCharts(cachedResponse.plot[0].alloc);
        $scope.state.radarCharts = prepareRadarCharts(cachedResponse.plot[0].alloc);
        $scope.state.stackedBarChart = undefined;
        $scope.state.multipleBudgetsChart = undefined;
        $scope.state.outcomeChart = prepareOutcomeChart(cachedResponse.plot[0].outcome);
      } else {
        $scope.state.pieCharts = [];
        $scope.state.radarCharts = [];
        if (cachedResponse.plot[0].alloc.bardata) {
          $scope.state.stackedBarChart = undefined;
          $scope.state.outcomeChart = undefined;
          $scope.state.multipleBudgetsChart = prepareMultipleBudgetsChart(cachedResponse.plot[0].alloc,
            cachedResponse.plot[0].outcome);
        } else if (cachedResponse.plot[0].alloc.stackdata) {
          $scope.state.stackedBarChart = prepareStackedBarChart(cachedResponse.plot[0].alloc);
          $scope.state.outcomeChart = prepareOutcomeChart(cachedResponse.plot[0].outcome);
          $scope.state.multipleBudgetsChart = undefined;
        }
      }
      $scope.state.optimisationGraphs = prepareOptimisationGraphs(cachedResponse.plot[0].multi);
      $scope.state.financialGraphs = prepareFinancialGraphs(cachedResponse.plot[0].multi);
    }

    // makes all graphs to recalculate and redraw
    function updateGraphs(data) {
      /* new structure keeps everything together:
       * data.plot[n].alloc => pie & radar
       * data.plot[n].multi => old line-scatterplots
       * data.plot[n].outcome => new line plot
       * n - sequence number of saved optimization
       */
      if (data && data.plot && data.plot.length > 0) {
        cachedResponse = data;
        if (data.plot[0]) graphTypeFactory.enableAnnualCostOptions($scope.types, data.plot[0].multi);
        drawGraphs();
      }
    }

    $scope.validations = {
      years :{
        valid: function(){ return validateYears().valid},
        message: "Please specify program optimizations period."
      },
      fixedBudget: {
        valid: function(){ return $scope.params.objectives.outcome.fixed !== undefined;},
        message: 'Please enter a value for the fixed budget.',
        condition: function(){return $scope.params.objectives.funding === 'constant';}
      },
      variableBudget: {
        valid: function(){ return validateVariableBudgets()},
        message: "Please enter a budget for each year.",
        condition: function(){return $scope.params.objectives.funding === 'variable';}
      },
      budgetType: {
        valid: function(){return $scope.params.objectives.funding!==undefined;},
        message: "Please pick at least one budget type."
      },
      objectivesToMinimizeCount:{
        valid:function(){return validateObjectivesToMinimize().valid;},
        message: "You must pick at least one objective to minimize."
      },
      objectivesOutcomeWeights:{
        valid:function(){return validateOutcomeWeights().valid;},
        message: "You must specify the weighting parameters for all objectives to minimize."
      }
    };

    $scope.objectivesToMinimize = [
      {
        name:"Cumulative new HIV infections",
        slug:"inci",
        title: "New infections weighting"
      },
      {
        name:"Cumulative DALYs",
        slug: "daly",
        title:"DALYs weighting"
      },
      {
        name:" Cumulative AIDS-related deaths",
        slug:"death",
        title:"Deaths weighting"
      },
      {
        name:"Total HIV-related costs",
        slug:"cost",
        title:"Costs weighting"
      }
    ];

    /* If some of the budgets are undefined, return false */
    function validateVariableBudgets() {
      return _(_($scope.params.objectives.outcome.variable).toArray()).some(function (budget) {return budget === undefined;}) === false;
    }

    function validateYears(){
       if($scope.params.objectives.year!==undefined){
         var start = parseInt($scope.params.objectives.year.start);
         var end = parseInt($scope.params.objectives.year.end);
         var until = parseInt($scope.params.objectives.year.until);
         return {
          start:start,
          end: end,
          until: until,
          valid: (isNaN(start) ||  isNaN(end) || isNaN(until) || end <= start || until <= start) === false
        };
       }
       return {
        valid:false
      };
    }

    function validateObjectivesToMinimize(){
      var checkedPrograms = _($scope.objectivesToMinimize).filter(function (a) {
        return $scope.params.objectives.outcome[a.slug] === true;
      });
      return {
        checkedPrograms : checkedPrograms,
        valid: checkedPrograms.length > 0
      };
    }

    function validateOutcomeWeights(){
      var checkedPrograms = _($scope.objectivesToMinimize).filter(function (a) {
        return $scope.params.objectives.outcome[a.slug] === true &&
          !($scope.params.objectives.outcome[a.slug+'weight']!==undefined &&
          $scope.params.objectives.outcome[a.slug+'weight']>0);
      });
      return {
        checkedPrograms : checkedPrograms,
        valid: checkedPrograms.length === 0
      };
    }

    function checkValidation(){
      errorMessages = [];
      _($scope.validations).each(function(validation){
        if(validation.valid()!==true && (validation.condition === undefined || validation.condition() === true)){
          errorMessages.push({message:validation.message});
        }
      });
    }

    $scope.validateYears = validateYears;
    $scope.validateVariableBudgets = validateVariableBudgets;
    $scope.validateObjectivesToMinimize = validateObjectivesToMinimize;
    $scope.validateOutcomeWeights = validateOutcomeWeights;

    /**
     * Returns true if at least one chart is available
     */
    $scope.someGraphAvailable = function() {
      return !(_.isEmpty($scope.state.radarCharts)) ||
        !(_.isEmpty($scope.state.optimisationGraphs)) ||
        !(_.isEmpty($scope.state.financialGraphs)) ||
        !(_.isEmpty($scope.state.pieCharts)) ||
        $scope.state.stackedBarChart !== undefined ||
        $scope.state.outcomeChart !== undefined;
    };

    /**
     * Update the variables depending on the range in years.
     */
    $scope.updateYearRange = function () {
      // only for variable funding the year range is relevant to produce the loop & col
      if ($scope.params.objectives.funding === undefined || $scope.params.objectives.funding !== 'variable') {
        return;
      }

      // reset data
      $scope.params.objectives.outcome.variable = {};
      $scope.yearLoop = [];
      $scope.yearCols = [];

      var validatedYears = validateYears();
      if (validatedYears.valid === false) {
        return;
      }

      // initialize data
      var years = _.range(validatedYears.start, validatedYears.end + 1);
      $scope.yearLoop = _(years).map(function (year) {
        return {year: year};
      });

      var cols = 5;
      var rows = Math.ceil($scope.yearLoop.length / cols);
      $scope.yearCols = _(_.range(0, rows)).map(function (col, index) {
        return {start: index * cols, end: (index * cols) + cols};
      });
    };

    /**
     * If the string is undefined return empty, otherwise just return the string
     * @param str
     * @returns {string}
     */
    function strOrEmpty(str){
      return _(str).isUndefined() ? '' : str;
    }

    /**
     * Join the word with a comma between them, except for the last word
     * @param arr
     * @param prop if it's not undefined it will pick that specific property from the object
     * @param quote should the sentence be quoted or not
     * @param before add something before each word
     * @param after add something after each word
     * @returns {string}
     */
    function joinArrayAsSentence(arr, prop, quote, before, after){
      quote = quote ? '"':'';
      before = strOrEmpty(before);
      after = strOrEmpty(after);
      return quote + _.compact(_(arr).map(function (val) {var p = (prop ? val[prop] : val);return p ? (before + strOrEmpty(p) + after ) : undefined;})).join(", ") + quote;
    }

    function constructOptimizationMessage() {
      $scope.optimizationMessage = _.template("Optimizing <%= checkedPrograms %> over years <%= startYear %> to <%= endYear %> with <%= budgetLevel %>.", {
        checkedPrograms : joinArrayAsSentence(validateObjectivesToMinimize().checkedPrograms, 'name', true),
        startYear: $scope.params.objectives.year.start,
        endYear:$scope.params.objectives.year.end,
        budgetLevel: $scope.params.objectives.funding === 'variable' ?
          //get budgets list and join it as a sentence
          " budget level " + joinArrayAsSentence(_.compact(_($scope.params.objectives.outcome.variable).toArray()), undefined, false, "$") : //variable budgets
          " fixed budget of $" + $scope.params.objectives.outcome.fixed + " per year" //fixed budgets
      });
    }

    $scope.setActiveTab = function(tabNum){
      if(tabNum === 3){
      /*Prevent going to third tab if something is invalid in the first tab.
        Cannot just use $scope.OptimizationForm.$invalid for this because the validation of the years and the budgets is done in a different way. */
        checkValidation();
        if(errorMessages.length > 0){
          modalService.informError(errorMessages, 'Cannot view results');
          return;
        }
        constructOptimizationMessage();
      }
      $scope.activeTab = tabNum;
    };

    $scope.initTimer = function(status) {
      if ( !angular.isDefined( optimizationTimer ) ) {
        // Keep polling for updated values after every 5 seconds till we get an error.
        // Error indicates that the model is not optimizing anymore.
        optimizationTimer = $interval(checkWorkingOptimization, 10000, 0, false);
        $scope.optimizationStatus = status;
        $scope.errorText = '';
        // start cfpLoadingBar loading
        // calculate the number of ticks in timelimit
        var val = ($scope.params.timelimit * 1000) / 250;
        // callback function in start to be called in place of _inc()
        cfpLoadingBar.start(function () {
          if (cfpLoadingBar.status() >= 0.95) {
            return;
          }
          var pct = cfpLoadingBar.status() + (0.95/val);
          cfpLoadingBar.set(pct);
        });
      }
    };

    $scope.startOptimization = function () {
      $http.post('/api/analysis/optimization/start', $scope.params, {ignoreLoadingBar: true})
        .success(function (data, status, headers, config) {
          if (data.status == "OK" && data.join) {
            $scope.initTimer(statusEnum.RUNNING);
          } else {
            console.log("Cannot poll for optimization now");
          }
        });
    };

    $scope.checkExistingOptimization = function(newTab, oldTab) {
      if(newTab !=3) {
        stopTimer();
      } else {
        $scope.initTimer(statusEnum.CHECKING);
      }
    };

    function checkWorkingOptimization() {
      $http.get('/api/analysis/optimization/working', {ignoreLoadingBar: true})
        .success(function(data, status, headers, config) {
          if (data.status == 'Done') {
            stopTimer();
          } else {
            if (data.status == 'Running') $scope.optimizationStatus = statusEnum.RUNNING;
            if (data.status == 'Stopping') $scope.optimizationStatus = statusEnum.STOPPING;
          }
          updateGraphs(data); // otherwise they might never get updated!
        })
        .error(function(data, status, headers, config) {
          if (data && data.exception) {
            $scope.errorText = data.exception;
          }
          stopTimer();
        });
    }

    $scope.stopOptimization = function () {
      modalService.confirm(
        function (){
          $http.get('/api/analysis/optimization/stop')
          .success(function(data) {
            // Do not cancel timer yet, if the optimization is running
            if ($scope.optimizationStatus) {
              $scope.optimizationStatus = statusEnum.REQUESTED_TO_STOP;
            }
          });
        },
        function (){},
        'Yes, Stop Optimization',
        'No',
        'Warning, optimization has not converged. Results cannot be used for analysis.',
        'Warning!'
      );
    };

    function stopTimer() {
      if ( angular.isDefined( optimizationTimer ) ) {
        $interval.cancel(optimizationTimer);
        optimizationTimer = undefined;
        $scope.optimizationStatus = statusEnum.NOT_RUNNING;
        cfpLoadingBar.complete();
      }
    }

    $scope.$on('$destroy', function() {
      // Make sure that the interval is destroyed too
      stopTimer();
    });

    $scope.saveOptimization = function () {
      var doSave = function (name, params) {
        $http.post('/api/analysis/optimization/save', {
          name: name, objectives: params.objectives, constraints: params.constraints
        })
          .success(function (data) {
            if (data.optimizations) {
              $scope.initOptimizations(data.optimizations, name);
            }
          });
      };

      modalService.showSaveOptimization($scope.state.activeOptimizationName,
        function (optimizationName) {
          doSave(optimizationName, $scope.params);
        }
      );
    };

    $scope.deleteOptimization = function (optimizationName) {
      $http.post('/api/analysis/optimization/remove/' + optimizationName)
        .success(function(data){
          $scope.initOptimizations(data.optimizations, undefined);
        });
    };

    $scope.revertOptimization = function () {
      $http.post('/api/analysis/optimization/revert')
        .success(function(){ console.log("OK");});
    };

    // The graphs are shown/hidden after updating the graph type checkboxes.
    $scope.$watch('types', drawGraphs, true);

    $scope.yearLoop = [];
    $scope.yearCols = [];


    /**
     * Returns true if the start & end year are required.
     */
    $scope.yearsAreRequired = function () {
      if (!$scope.params.objectives.funding || $scope.params.objectives.funding !== 'variable') {
        return false;
      }
      if (!$scope.params.objectives.year ||
          !$scope.params.objectives.year.start ||
          !$scope.params.objectives.year.end){
        return true;
      }
      return false;
    };

    /**
     * Update the variables depending on the range in years.
     */
    $scope.updateYearRange = function () {

      // only for variable funding the year range is relevant to produce the loop & col
      if ( !$scope.params.objectives.funding || $scope.params.objectives.funding !== 'variable') {
        return;
      }

      // reset data
      $scope.params.objectives.outcome.variable = {};
      $scope.yearLoop = [];
      $scope.yearCols = [];

      // parse years
      if ($scope.params.objectives.year === undefined) {
        return;
      }
      var start = parseInt($scope.params.objectives.year.start);
      var end = parseInt($scope.params.objectives.year.end);
      if ( isNaN(start) ||  isNaN(end) || end <= start) {
        return;
      }

      // initialize data
      var years = _.range(start, end + 1);
      $scope.yearLoop = _(years).map(function (year) { return { year: year}; });

      var cols = 5;
      var rows = Math.ceil($scope.yearLoop.length / cols);
      $scope.yearCols = _(_.range(0, rows)).map(function(col, index) {
        return {start: index*cols, end: (index*cols)+cols };
      });

    };

    /**
     * Collects all existing charts in the $scope.chartsForDataExport variable.
     */
    var updateChartsForDataExport = function() {
      $scope.chartsForDataExport = [];

      if ( $scope.state.pieCharts && !$scope.types.plotUncertainties ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.pieCharts);
      }

      if ( $scope.state.radarCharts && $scope.types.plotUncertainties ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.radarCharts);
      }

      if ( $scope.state.stackedBarChart ) {
        $scope.chartsForDataExport.push($scope.state.stackedBarChart);
      }

      if ( $scope.state.outcomeChart ) {
        $scope.chartsForDataExport.push($scope.state.outcomeChart);
      }

      if ( $scope.state.multipleBudgetsChart ) {
        $scope.chartsForDataExport.push($scope.state.multipleBudgetsChart);
      }

      if ( $scope.state.optimisationGraphs ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.optimisationGraphs);
      }

      if ( $scope.state.financialGraphs ) {
        $scope.chartsForDataExport = $scope.chartsForDataExport.concat($scope.state.financialGraphs);
      }

    };

    $scope.optimizationByName = function(name) {
      return _($scope.optimizations).find(function(item) {
        return item.name == name;
      });
    };

    /**
     * Changes active constrains and objectives to the values in provided optimization
     * @param optimization {Object}
     */
    $scope.applyOptimization = function(name) {
      var optimization = $scope.optimizationByName(name);
      _.extend($scope.params.objectives, optimization.objectives);
      _.extend($scope.params.constraints, optimization.constraints);
      if (optimization.result) {
        updateGraphs(optimization.result);
      }
      constructOptimizationMessage();
    };

    // apply default optimization on page load
    $scope.initOptimizations = function(optimizations, name) {
      if (!optimizations) return;

      $scope.optimizations = angular.copy(optimizations);

      var nameExists = name && _.some(_($scope.optimizations), function(item) {
        return item.name == name;
      });

      if (nameExists) {
        $scope.state.activeOptimizationName = name;
      } else {
        $scope.state.activeOptimizationName = undefined;
        var optimization = _($scope.optimizations).first();
        if (optimization) {
          $scope.state.activeOptimizationName = optimization.name;
        }
      }
      $scope.applyOptimization($scope.state.activeOptimizationName);
    };

    // apply existing optimization data, if present
    if (optimizations && optimizations.data) {
      $scope.initOptimizations(optimizations.data.optimizations);
    }

    $scope.updateTimelimit = function () {
      if ($scope.state.isTestRun) {
        $scope.params.timelimit = 60;
      } else {
        $scope.params.timelimit = 3600;
      }
    };

    $scope.$watch('state.pieCharts', updateChartsForDataExport, true);
    $scope.$watch('state.outcomeChart', updateChartsForDataExport, true);
    $scope.$watch('state.radarCharts', updateChartsForDataExport, true);
    $scope.$watch('state.optimisationGraphs', updateChartsForDataExport, true);
    $scope.$watch('state.financialGraphs', updateChartsForDataExport, true);
    $scope.$watch('state.stackedBarChart', updateChartsForDataExport, true);
    $scope.$watch('state.multipleBudgetsChart', updateChartsForDataExport, true);
    $scope.$watch('types.plotUncertainties', updateChartsForDataExport, true);
    $scope.$watch('activeTab', $scope.checkExistingOptimization, true);

  });
});
