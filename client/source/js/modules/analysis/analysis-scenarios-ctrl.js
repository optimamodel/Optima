define(['./module', 'angular', 'underscore'], function (module, angular, _) {
    'use strict';

    module.controller('AnalysisScenariosController', function ($scope, $http, $modal, meta, scenarioParamsResponse) {

        var linesGraphOptions, linesGraphData, responseData, availableScenarioParams;

        // initialize all necessary data for this controller
        var initialize = function() {

          // transform scenarioParams to use attribute `names` instead of `keys`
          // it is the same for the data we have to send to run scenarios
          availableScenarioParams = _(scenarioParamsResponse.data.params).map(function(parameters) {
            return { name: parameters.name, names: parameters.keys };
          });

          $scope.scenarios = [
            {active: true, name: '100% condom use in KAPs', pars: [
              { names: ['condom','reg'], pops: 0, startyear: 2010, endyear: 2015, startval: -1, endval: 1},
              { names: ['condom','cas'], pops: 0, startyear: 2010, endyear: 2015, startval: -1, endval: 1},
              { names: ['condom','com'], pops: 1, startyear: 2010, endyear: 2015, startval: -1, endval: 1},
              { names: ['condom','com'], pops: 5, startyear: 2010, endyear: 2015, startval: -1, endval: 1}
            ]}
          ];

          $scope.runScenariosOptions = {
            dosave: false
          };

          $scope.types = [
            { id: 'prev', name: 'Prevalence', active: true, byPopulation: true, total: false },
            { id: 'daly', name: 'DALYs', active: false, byPopulation: false, total: false },
            { id: 'death', name: 'Deaths', active: false, byPopulation: false, total: false },
            { id: 'inci', name: 'New infections', active: false, byPopulation: false, total: false },
            { id: 'dx', name: 'Diagnoses', active: false, byPopulation: false, total: false },
            { id: 'tx1', name: 'First-line treatment', active: false, byPopulation: false, total: false },
            { id: 'tx2', name: 'Second-line treatment', active: false, byPopulation: false, total: false }
          ];


          linesGraphOptions = {
            height: 200,
            width: 320,
            margin: {
              top: 20,
              right: 10,
              bottom: 45,
              left: 70
            },
            xAxis: {
              axisLabel: 'Year',
              tickFormat: function (d) {
                return d3.format('d')(d);
              }
            },
            yAxis: {
              axisLabel: '',
              tickFormat: function (d) {
                return d3.format(',.2f')(d);
              }
            }
          };

          linesGraphData = {
            lines: [],
            scatter: []
          };
        };

        /*
         * Returns an array containing arrays with [x, y] for d3 line data.
         */
        var generateLineData = function(xData, yData) {
          return _(yData).map(function (value, i) {
            return [xData[i], value];
          });
        };

        /*
         * Returns an graph based on the provided yData.
         *
         * yData should be an array where each entry contains an array of all
         * y-values from one line.
         */
        var generateGraph = function(type, yData, xData, title) {
          var graph = {
            options: angular.copy(linesGraphOptions),
            data: angular.copy(linesGraphData),
            type: type,
            title: title
          };

          _(yData).each(function(lineData) {
            graph.data.lines.push(generateLineData(xData, lineData));
          });

          return graph;
        };

        /*
         * Regenerate graphs based on the response and type settings in the UI.
         */
        var updateGraphs = function (response) {
          if (!response) {
            return graphs;
          }

          var graphs = [];

          _($scope.types).each(function (type) {

            var data = response[type.id];

            // generate graphs showing the overall data for this type
            if (type.total) {
              var title = data.tot.title;
              var graph = generateGraph(type, data.tot.data, response.tvec, title);
              graph.options.xAxis.axisLabel = data.xlabel;
              graph.options.yAxis.axisLabel = data.tot.ylabel;
              graphs.push(graph);
            }

            // generate graphs for this type for each population
            if (type.byPopulation) {
              _(data.pops).each(function (population, populationIndex) {

                var title = population.title;
                var graph = generateGraph(type, population.data, response.tvec, title);
                graph.options.xAxis.axisLabel = data.xlabel;
                graph.options.yAxis.axisLabel = population.ylabel;
                graphs.push(graph);
              });
            }
          });

          $scope.graphs = graphs;
        };

        /*
         * Returns a collection of entries where all non-active antries are filtered
         * out and the active attribute is removed from each of these entries.
         */
        var toCleanArray = function (collection) {
          return _(collection).chain()
          .where({ active: true })
          .map(function (item) {
            return _(item).omit(['active', '$$hashKey']);
          })
          .value();
        };


        $scope.runScenarios = function () {
          $scope.runScenariosOptions.scenarios = toCleanArray($scope.scenarios);
          $http.post('/api/analysis/scenarios/run', $scope.runScenariosOptions)
            .success(function(data) {
              responseData = data;
              updateGraphs(responseData);
            });
        };

        // Helper function to open a population modal
        var openScenarioModal = function(scenario) {
          return $modal.open({
            templateUrl: 'js/modules/analysis/analysis-scenarios-modal.html',
            controller: 'AnalysisScenariosModalController',
            resolve: {
              scenario: function () {
                return scenario;
              },
              availableScenarioParams: function() {
                return availableScenarioParams;
              },
              populationNames: function() {
                return meta.pops.long;
              }
            }
          });
        };

        $scope.openAddScenarioModal = function ($event) {
            if ($event) {
                $event.preventDefault();
            }

            var scenario = {};
            return openScenarioModal(scenario).result.then(
                function (newscenario) {
                    newscenario.active = true;
                    newscenario.pars = newscenario.pars || [];
                    $scope.scenarios.push(newscenario);
                });
        };

        $scope.openEditScenarioModal = function ($event, scenario) {
            if ($event) {
                $event.preventDefault();
            }

            return openScenarioModal(scenario).result.then(
                function (newscenario) {
                    scenario.active = true;
                    _(scenario).extend(newscenario);
                });
        };

        $scope.onGraphTypeChange = function (type) {
          type.active = type.total || type.byPopulation;
          updateGraphs(responseData);
        };

        initialize();

    });

});
