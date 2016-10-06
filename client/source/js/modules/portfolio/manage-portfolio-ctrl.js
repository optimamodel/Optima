define(
  ['./module', 'angular', 'underscore'], function (module, angular, _) {

    'use strict';

    module.controller(
      'PortfolioController',
      function (
        $scope, $http, activeProject, modalService, fileUpload,
        UserManager, $state, toastr, globalPoller, $modal) {

        function initialize() {

          $scope.objectiveKeyLabels = [
            {'key': 'start', 'label':'Start year' },
            {'key': 'end', 'label': 'End year'},
            {'key': 'budget', 'label': 'Budget'},
            {'key': 'deathweight', 'label': 'Death weight'},
            {'key': 'inciweight', 'label': 'Incidence weight'},
          ];

          $scope.isSelectNewProject = false;
          $scope.state = {
            portfolio: undefined,
            gaoptim: undefined
          };

          reloadPortfolio();
        }

        function loadPortfolios(portfolios) {
          var currentPortfolioId = null;
          if (!_.isUndefined($scope.state.portfolio)) {
            currentPortfolioId = $scope.state.portfolio.id;
          }
          $scope.portfolios = portfolios;
          $scope.state.portfolio = _.findWhere($scope.portfolios, {id: currentPortfolioId});
          if (!$scope.state.portfolio) {
            $scope.state.portfolio = $scope.portfolios[0];
          }
          $scope.setActiveGaoptim();
        }

        $scope.setActiveGaoptim = function() {
          console.log('setActiveGaoptim');
          var currentGaoptimId = null;
          if (!_.isUndefined($scope.state.gaoptim)) {
            currentGaoptimId = $scope.state.gaoptim.id;
          }
          $scope.state.gaoptim = _.findWhere($scope.state.portfolio.gaoptims, {id: currentGaoptimId});
          if (!$scope.state.gaoptim) {
            $scope.state.gaoptim = $scope.state.portfolio.gaoptims[0];
          }
          $http
            .get(getCheckFullGaUrl())
            .success(function(response) {
              if (response.status === 'started') {
                initFullGaPoll();
              }
            });
          _.each($scope.state.portfolio.projects, function(project) {
            $scope.bocStatusMessage[project.id] = project.boc;
            $http
              .get(getCheckProjectBocUrl(project.id))
              .success(function(response) {
                if (response.status === 'started') {
                  initProjectBocPoll(project.id);
                }
              });
          });
        };

        function openEditNameModal(
           acceptName, title, message, name, errorMessage, invalidNames) {

          var modalInstance = $modal.open({
            templateUrl: 'js/modules/portfolio/portfolio-modal.html',
            controller: [
              '$scope', '$document',
              function($scope, $document) {

                $scope.name = name;
                $scope.title = title;
                $scope.message = message;
                $scope.errorMessage = errorMessage;

                $scope.checkBadForm = function(form) {
                  var isGoodName = !_.contains(invalidNames, $scope.name);
                  form.$setValidity("name", isGoodName);
                  return !isGoodName;
                };

                $scope.submit = function() {
                  acceptName($scope.name);
                  modalInstance.close();
                };

                function onKey(event) {
                  if (event.keyCode == 27) {
                    return modalInstance.dismiss('ESC');
                  }
                }

                $document.on('keydown', onKey);
                $scope.$on(
                  '$destroy',
                  function() { $document.off('keydown', onKey); });

              }
            ]
          });

          return modalInstance;
        }

        $scope.createPortfolio = function() {
          openEditNameModal(
            function(name) {
              $http
                .post(
                  '/api/portfolio', {name: name})
                .success(function(response) {
                  console.log('created portfolio', response);
                  $scope.portfolios.push(response);
                  $scope.state.portfolio = response;
                  loadPortfolios($scope.portfolios);
                  toastr.success('Created portfolio');
                });
            },
            'Create portfolio',
            "Enter portfolio name",
            "",
            "Name already exists",
            _.pluck($scope.portfolios, 'name'));
        };

        $scope.deletePortfolio = function() {
          $http
            .delete('/api/portfolio/' + $scope.state.portfolio.id)
            .success(loadPortfolios);
        };

       function reloadPortfolio() {
          $scope.bocStatusMessage = {};
          globalPoller.stopPolls();
          $http
            .get('/api/portfolio')
            .success(loadPortfolios);
        }

        function getCheckFullGaUrl() {
          return "/api/task/" + $scope.state.portfolio.id
              + "/type/portfolio-" + $scope.state.gaoptim.id;
        }

        function getCheckProjectBocUrl(projectId) {
          return "/api/task/" + projectId
                + "/type/gaoptim-" + $scope.state.gaoptim.id;
        }

        $scope.calculateAllBocCurves = function() {
          console.log('run BOC curves', $scope.state.portfolio);
          $http
            .post(
              "/api/portfolio/" + $scope.state.portfolio.id
              + "/gaoptim/" + $scope.state.gaoptim.id,
              {maxtime: $scope.state.bocMaxtime})
            .success(function() {
              _.each($scope.state.portfolio.projects, function(project) {
                initProjectBocPoll(project.id);
              });
            });
        };

        $scope.deleteProject = function(projectId) {
          $http
            .delete(
              '/api/portfolio/' + $scope.state.portfolio.id
                + '/project/' + projectId)
            .success(function() {

            });
        };

        $scope.runFullGa = function() {
          $http
            .get(getCheckFullGaUrl())
            .success(function(response) {
              console.log('start job response', response);
              if (response.status != 'started') {
                $http
                  .post(
                    "/api/minimize/portfolio/" + $scope.state.portfolio.id
                    + "/gaoptim/" + $scope.state.gaoptim.id,
                    {maxtime: $scope.state.maxtime})
                  .success(function() {
                    initFullGaPoll();
                  });
              }
            });
        };

        function initProjectBocPoll(projectId) {
          globalPoller.startPoll(
            projectId,
            getCheckProjectBocUrl(projectId),
            function(response) {
              if (response.status === 'completed') {
                $scope.bocStatusMessage[projectId] = "calculated";
                reloadPortfolio();
                toastr.success('BOC calculation finished');
              } else if (response.status === 'started') {
                var start = new Date(response.start_time);
                var now = new Date(response.current_time);
                var diff = now.getTime() - start.getTime();
                var seconds = parseInt(diff / 1000);
                $scope.bocStatusMessage[projectId] = "running for " + seconds + " s";
              } else {
                $scope.bocStatusMessage[projectId] = 'failed';
                $scope.state.portfolio.isRunnable = true;
              }
            }
          );
        }

        function initFullGaPoll() {
          globalPoller.startPoll(
            $scope.state.gaoptim.id,
            getCheckFullGaUrl(),
            function(response) {
              if (response.status === 'completed') {
                $scope.statusMessage = "";
                reloadPortfolio();
                toastr.success('GA Optimization completed');
              } else if (response.status === 'started') {
                var start = new Date(response.start_time);
                var now = new Date(response.current_time);
                var diff = now.getTime() - start.getTime();
                var seconds = parseInt(diff / 1000);
                $scope.statusMessage = "Optimization running for " + seconds + " s";
              } else {
                $scope.statusMessage = 'Optimization failed';
                $scope.state.portfolio.isRunnable = true;
              }
            }
          );
        }

        $scope.savePortfolio = function() {
          $http
            .post(
              "/api/portfolio/" + $scope.state.portfolio.id,
              angular.copy($scope.state.portfolio))
            .success(function(response) {
              console.log(response);
              toastr.success('saved objectives')
            });
        };

        $scope.addProject = function() {
          $scope.isSelectNewProject = true;
          $http
            .get('/api/project')
            .success(function(response) {
              var selectedIds = _.pluck($scope.state.portfolio.projects, "id");
              $scope.projects = [];
              _.each(response.projects, function(project) {
                var isSelected = _.contains(selectedIds, project.id);
                if (project.isOptimizable) {
                  $scope.projects.push({
                    'name': project.name,
                    'id': project.id,
                    'selected': isSelected
                  })
                }
              });
              console.log("$scope.projects", $scope.projects);
            });
        };

        $scope.dismissAddProject = function() {
          $scope.isSelectNewProject = false;
        };

        $scope.saveSelectedProject = function() {
          $scope.isSelectNewProject = false;
          var selectedIds = _.pluck($scope.state.portfolio.projects, "id");
          console.log("selectedIds", selectedIds);
          console.log("$scope.projects", $scope.projects);
          _.each($scope.projects, function(project) {
            if (!_.contains(selectedIds, project.id)) {
              if (project.selected) {
                console.log('new project', project.name);
                $scope.state.portfolio.projects.push({
                  "id": project.id,
                  "name": project.name,
                  "boc": "none"
                });
              }
            }
          });

          console.log($scope.state.portfolio.projects)
          $scope.savePortfolio();
          toastr.success('stop adding')
        };

        $scope.hasNoResults = function() {
          if (_.isUndefined($scope.state.portfolio)) {
            return true;
          }
          return !($scope.state.portfolio.outputstring);
        };

        $scope.exportResults = function() {
          if ($scope.state.portfolio.outputstring) {
            var blob = new Blob(
              [$scope.state.portfolio.outputstring], {type: 'application/octet-stream'});
            saveAs(blob, ('result.csv'));
          }
        };

        initialize();

      }
    );

  }
);