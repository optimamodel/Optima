define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelViewCalibrationController', function ($scope, $http, meta, info, modalService) {

    var plotTypes, effectNames;

    var initialize =function () {
      $scope.meta = meta;

      // show message "calibrate the model" and disable the form elements
      $scope.projectInfo = info;
      $scope.needData = !$scope.projectInfo.has_data;
      
      if ( !$scope.needData ) {
        $scope.initializePrograms();
        $scope.selectedProgram = $scope.programs[0];
        $scope.displayedProgram = null;

        $scope.coParams = [];

        $scope.hasCostCoverResponse = false;

      }
      
      // model parameters
      $scope.defaultSaturationCoverageLevel = 90;
      $scope.defaultKnownCoverageLevel = 20;
      $scope.defaultKnownFundingValue = 800000;
      $scope.defaultXAxisMaximum = 7000000;
      $scope.behaviorWithoutMin = 0.3;
      $scope.behaviorWithoutMax = 0.5;
      $scope.behaviorWithMin = 0.7;
      $scope.behaviorWithMax = 0.9;

      plotTypes = ['plotdata', 'plotdata_cc', 'plotdata_co'];

      resetGraphs();
    };

    /**
    * Creates the models of the programs for this controller.
    * If the backend do not present values for the categories, we'll use 'Others' as default.
    */
    $scope.initializePrograms = function () {
      $scope.programs = _(meta.progs.long).map(function (name, index) {
        var categories;
        categories = meta.progs.categories;
        if(!categories) { // create default categories if absent
          categories = [];
          _.times(meta.progs.long.length, function (n){
            categories.push('Others')
          });}
          
        return {
          name: name,
          acronym: meta.progs.short[index],
          category: categories[index]
        };
      });
      /** Dec 26 2014
       * fix/306-2-fix-plotting-of-default-ccocs
       * Default null value for selectedProgram
       */
      $scope.programs.unshift({name:'-- No program selected --',category:null, acronym:null});
    };


    var resetGraphs= function () {
      $scope.graphs = {
        plotdata: [],
        plotdata_cc: {},
        plotdata_co: []
      };
    };

    var getLineScatterOptions = function (options, xLabel, yLabel) {
      var defaults = {
        height: 300,
        width: 450,
        margin: {
          top: 20,
          right: 20,
          bottom: 60,
          left: 100
        },
        xAxis: {
          axisLabel: xLabel || 'X',
          tickFormat: function (d) {
            // Cliff requested to lower case the unit suffixed values.
            // e.g. 100M -> 100m
            return d3.format('s')(d).toLowerCase();
          }
        },
        yAxis: {
          axisLabel: yLabel || 'Y'
        }
      };

      return _(angular.copy(defaults)).extend(options);
    };

    /* Methods
     ========= */

    /**
     * Calculates graphs objects of types plotdata and plotdata_co
     * returns ready to draw Graph object
     * @param graphData - api reply
     * @returns {{options, data: {lines: Array, scatter: Array}}}
     */
    var setUpPlotdataGraph = function (graphData) {

      var graph = {
        options: getLineScatterOptions({
          width: 300,
          height: 200,
          margin: {
            top: 20,
            right: 5,
            bottom: 40,
            left: 60
          },
          linesStyle: ['__blue', '__black __dashed', '__black __dashed']
        }, graphData.xlabel, graphData.ylabel),
        data: {
          lines: [],
          scatter: []
        },
        title: graphData.title
      };

      // quit if data is empty - empty graph placeholder will be displayed
      if (!graphData.ylinedata) {
        return graph;
      }

      var numOfLines = graphData.ylinedata.length;

      _(graphData.xlinedata).each(function (x, index) {
        var y = graphData.ylinedata;
        for (var i = 0; i < numOfLines; i++) {
          if (!graph.data.lines[i]) {
            graph.data.lines[i] = [];
          }

          graph.data.lines[i].push([x, y[i][index]]);
        }
      });

      _(graphData.xscatterdata).each(function (x, index) {
        var y = graphData.yscatterdata;

        if (y[index]) {
          graph.data.scatter.push([x, y[index]]);
        }
      });

      return graph;
    };

    /**
     * Generates ready to plot graph for a cost coverage.
     */
    var prepareCostCoverageGraph = function (data) {
      var graph = {
        options: getLineScatterOptions({}, data.xlabel, data.ylabel),
        data: {
          // there is a single line for that type
          lines: [[]],
          scatter: []
        }
      };

      _(data.xlinedata).each(function (x, index) {
        var y = data.ylinedata;
        graph.data.lines[0].push([x, y[index]]);
      });

      _(data.xscatterdata).each(function (x, index) {
        var y = data.yscatterdata;

        if (y[index]) {
          graph.data.scatter.push([x, y[index]]);
        }
      });

      return graph;
    };

    /**
     * Receives graphs data with plot type to calculate,
     * calculates all graphs of given type and writes them to $scope.graphs[type]
     * @param data - usually api request with graphs data
     * @param type - string
     */
    var prepareGraphsOfType = function (data, type) {
      if (type === 'plotdata_cc') {
        $scope.graphs[type] = prepareCostCoverageGraph(data);
      } else if (type === 'plotdata' || type === 'plotdata_co') {
        _(data).each(function (graphData) {
          $scope.graphs[type].push(setUpPlotdataGraph(graphData));
        });
      }
    };

    var setUpCOParamsFromEffects = function (effectNames) {
      $scope.coParams = _(effectNames).map(function (effect) {
        return [
          effect[2][0][0],
          effect[2][0][1],
          effect[2][1][0],
          effect[2][1][1]
        ];
      });
    };

    var convertFromPercent = function (value) {
      return value / 100;
    };

    var costCoverageParams = function () {
      return [
        convertFromPercent($scope.saturationCoverageLevel),
        convertFromPercent($scope.knownCoverageLevel),
        $scope.knownFundingValue,
        $scope.xAxisMaximum
      ];
    };

    /**
     * Returns the current parameterised plot model.
     */
    var getPlotModel = function() {
      return {
        progname: $scope.selectedProgram.acronym,
        ccparams: costCoverageParams(),
        coparams: [
          $scope.behaviorWithoutMin,
          $scope.behaviorWithoutMax,
          $scope.behaviorWithMin,
          $scope.behaviorWithMax
        ]
      };
    };

    /**
     * Retrieve and update graphs based on the provided plot models.
     */
    var retrieveAndUpdateGraphs = function (model) {
      // validation on Cost-coverage curve plotting options
      if ( !model.ccparams[0] || !model.ccparams[1] || !model.ccparams[2] || !model.ccparams[3] ){
        var message = 'Cost-coverage curve plotting options cannot be empty!';
        modalService.inform(
          function (){ null }, 
          'Okay',
          message, 
          'Error!'
        ); 
        return;
      }
      
      /**
       * stop further execution and return in case of null selectedProgram
       */
      if ( $scope.selectedProgram.acronym === null ) {
        return;
      }

      $http.post('/api/model/costcoverage', model).success(function (response) {
        if (response.status === 'OK') {

          $scope.displayedProgram = angular.copy($scope.selectedProgram);
          effectNames = response.effectnames;
          setUpCOParamsFromEffects(response.effectnames);
          $scope.hasCostCoverResponse = true;


          resetGraphs();
          _(plotTypes).each(function (plotType) {
            prepareGraphsOfType(response[plotType], plotType);
          });
        }
      });
    };

    $scope.changeProgram = function() {
      $scope.hasCostCoverResponse = false;
    }

    /**
     * Retrieve and update graphs based on the current plot models.
     */
    $scope.generateCurves = function () {
      var model = getPlotModel();
      retrieveAndUpdateGraphs(model);
    };

    $scope.uploadDefault = function () {
      var message = 'Upload default cost-coverage-outcome curves will be available in a future version of Optima. We are working hard in make it happen for you!';
      modalService.inform(
        function (){ null }, 
        'Okay',
        message, 
        'Thanks for your interest!'
      );      
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     *
     * The plot model gets saved in the backend.
     */
    $scope.saveModel = function () {
      var model = getPlotModel(model);
      model.doSave = true;
      model.all_coparams = $scope.coParams;
      model.all_effects = effectNames;
      retrieveAndUpdateGraphs(model);
    };

    /**
     * Retrieve and update graphs based on the current plot models.
     *
     * The plot model gets reverted in the backend.
     */
    $scope.revertModel = function () {
      var model = getPlotModel(model);
      model.doRevert = true;
      retrieveAndUpdateGraphs(model);
    };

    /**
     * POST /api/model/costcoverage/effect
     *   {
     *     "progname":<chosen progname>
     *     "effectname":<effectname for the given row>,
     *     "ccparams":<ccparams>,
     *     "coparams":<coprams from the corresponding coparams block>
     *   }
     */
    $scope.updateCurve = function (graphIndex) {
      $http.post('/api/model/costcoverage/effect', {
        progname: $scope.displayedProgram.acronym,
        ccparams: _(costCoverageParams()).map(parseFloat),
        coparams: _($scope.coParams[graphIndex]).map(parseFloat),
        effectname: effectNames[graphIndex]
      }).success(function (response) {
        $scope.graphs.plotdata[graphIndex] = setUpPlotdataGraph(response.plotdata);
        $scope.graphs.plotdata_co[graphIndex] = setUpPlotdataGraph(response.plotdata_co);
      });
    };

    initialize();

  });
});