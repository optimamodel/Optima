define(['./module', 'angular', 'underscore'], function (module, angular, _) {

  'use strict';

  module.controller(
    'ProjectOpenController',
    function ($scope, $http, activeProject, projects, modalService,
        fileUpload, UserManager, projectApiService, $state, $upload,
        $modal, toastr) {

      function initialize() {
        $scope.sortType = 'name'; // set the default sort type
        $scope.sortReverse = false;  // set the default sort order
        $scope.activeProjectId = activeProject.getProjectIdForCurrentUser();
        loadProjects(projects.data.projects);
        setActiveProject();
      }

      function setActiveProject() {
        $scope.project = null;
        _.each($scope.projects, function(project) {
          if ($scope.activeProjectId === project.id) {
            $scope.project = project;
          }
        });
      }

      function loadProjects(projects) {
        $scope.projects = _.map(projects, function(project) {
          project.creationTime = Date.parse(project.creationTime);
          project.updatedTime = Date.parse(project.updatedTime);
          project.dataUploadTime = Date.parse(project.dataUploadTime);
          return project;
        });
        console.log('projects', $scope.projects);
      }

      $scope.filterByName = function(project) {
        if ($scope.searchTerm) {
          return project.name.toLowerCase().indexOf($scope.searchTerm.toLowerCase()) !== -1;
        }
        return true;
      };

      $scope.updateSorting = function(sortType) {
        if ($scope.sortType === sortType) {
          $scope.sortReverse = !$scope.sortReverse;
        } else {
          $scope.sortType = sortType;
        }
      };

      $scope.selectAll = function() {
        _.forEach($scope.projects, function(project) {
          project.selected = $scope.allSelected;
        });
      };

      $scope.deleteSelected = function() {
        const selectedProjectIds = _.filter($scope.projects, function(project) {
          return project.selected;
        }).map(function(project) {
          return project.id;
        });
        projectApiService.deleteSelectedProjects(selectedProjectIds)
          .success(function () {
            $scope.projects = _.filter($scope.projects, function(project) {
              return !project.selected;
            });
            _.each(selectedProjectIds, function(projectId) {
              activeProject.ifActiveResetFor(projectId, UserManager.data);
            });
          });
      };

      $scope.downloadSelected = function() {
        const selectedProjectsIds = _.filter($scope.projects, function(project) {
          return project.selected;
        }).map(function(project) {
          return project.id;
        });
        projectApiService.downloadSelectedProjects(selectedProjectsIds)
          .success(function (response) {
            saveAs(new Blob([response], { type: "application/octet-stream", responseType: 'arraybuffer' }), 'portfolio.zip');
          });
      };

      $scope.open = function (name, id) {
        $scope.activeProjectId = id;
        setActiveProject();
        activeProject.setActiveProjectFor(name, id, UserManager.data);
      };

      function getUniqueName(name, otherNames) {
        var i = 0;
        var uniqueName = name;
        while (_.indexOf(otherNames, uniqueName) >= 0) {
          i += 1;
          uniqueName = name + ' (' + i + ')';
        }
        return uniqueName;
      }

      $scope.copy = function(name, id) {
        var otherNames = _.pluck($scope.projects, 'name');
        var newName = getUniqueName(name, otherNames);
        projectApiService.copyProject(id, newName).success(function (response) {
          projectApiService.getProjectList()
            .success(function(response) {
              toastr.success('Copied project ' + newName);
              loadProjects(response.projects);
            });
        });
      };

      /**
       * Opens to edit an existing project using name and id in /project/create screen.
       */
      $scope.edit = function (name, id) {
        activeProject.setActiveProjectFor(name, id, UserManager.data);
        $state.go('project.edit');
      };

      /**
       * Regenerates workbook for the given project.
       */
      $scope.workbook = function (name, id) {
        // read that this is the universal method which should work everywhere in
        // http://stackoverflow.com/questions/24080018/download-file-from-a-webapi-method-using-angularjs
        window.open(projectApiService.getSpreadsheetUrl(id), '_blank', '');
      };

      function isExistingProjectName(projectName) {
        var projectNames = _.pluck($scope.projects, 'name');
        return _(projectNames).contains(projectName);
      }

      function getUniqueName(fname) {
        var fileName = fname.replace(/\.prj$/, "").replace(/\.xlsx$/, "");
        // if project name taken, try variants
        var i = 0;
        var result = fileName;
        while (isExistingProjectName(result)) {
          i += 1;
          result = fileName + " (" + i + ")";
        }
        return result;
      }

      $scope.uploadProject = function() {
        angular
          .element('<input type="file">')
          .change(function (event) {
            var file = event.target.files[0];
            $upload
              .upload({
                url: '/api/project/data',
                fields: {name: getUniqueName(file.name)},
                file: file
              })
              .success(function (data, status, headers, config) {
                var name = data['name'];
                var projectId = data['id'];
                toastr.success('Project uploaded');
                activeProject.setActiveProjectFor(
                  name, projectId, UserManager.data);
                $state.reload();
              });
          })
          .click();
      };

      $scope.uploadProjectFromSpreadsheet = function() {
        angular
          .element('<input type="file">')
          .change(function (event) {
            var file = event.target.files[0];
            $upload
              .upload({
                url: '/api/project/data',
                fields: {name: getUniqueName(file.name), xls: true},
                file: file
              })
              .success(function (data, status, headers, config) {
                var name = data['name'];
                var projectId = data['id'];
                activeProject.setActiveProjectFor(
                  name, projectId, UserManager.data);
                toastr.success('Project created from spreadsheet');
                $state.reload();
              });
          })
          .click();
      };

      $scope.uploadSpreadsheet = function (name, id) {
        angular
          .element('<input type="file">')
          .change(function (event) {
            $upload
              .upload({
                url: '/api/project/' + id + '/spreadsheet',
                file: event.target.files[0]
              })
              .success(function (response) {
                toastr.success('Spreadsheet uploaded for project');
                $state.reload();
              });

          })
          .click();
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

      $scope.editProjectName = function(project) {
        var otherNames = _.pluck($scope.projects, 'name');
        otherNames = _.without(otherNames, project.name)
        openEditNameModal(
          function(name) {
            project.name = name;
            projectApiService
              .updateProject(
                project.id,
                {
                  project: project,
                  isSpreadsheet: false,
                  isDeleteData: false,
                })
              .success(function () {
                project.name = name;
                toastr.success('Renamed project');
                $state.reload();
              });
          },
          'Edit project name',
          "Enter project name",
          project.name,
          "Name already exists",
          otherNames);
      };

      /**
       * Gets the data for the given project `name` as <name>.json  file.
       */
      $scope.getData = function (name, id) {
        projectApiService.getProjectData(id)
          .success(function (response, status, headers, config) {
            var blob = new Blob([response], { type: 'application/octet-stream' });
            saveAs(blob, (name + '.prj'));
          });
      };

      /**
       * Upload data spreadsheet for a project.
       */
      $scope.setData = function (name, id, file) {
        var message = 'Warning: This will overwrite ALL data in the project ' + name + '. Are you sure you wish to continue?';
        modalService.confirm(
          function (){ fileUpload.uploadDataSpreadsheet($scope, file, projectApiService.getDataUploadUrl(id), false); },
          function (){},
          'Yes, overwrite data',
          'No',
          message,
          'Upload data'
        );
      };

      /**
       * Upload project data.
       */
      $scope.preSetData = function(name, id) {
        angular
          .element('<input type=\'file\'>')
          .change(function(event){
          $scope.setData(name, id, event.target.files[0]);
        }).click();
      };

      /**
       * Removes the project.
       */
      var removeProject = function (name, id, index) {
        projectApiService.deleteProject(id).success(function (response) {
          $scope.projects = _($scope.projects).filter(function (item) {
            return item.id != id;
          });
          activeProject.ifActiveResetFor(id, UserManager.data);
        });
      };

      /**
       * Opens a modal window to ask the user for confirmation to remove the project and
       * removes the project if the user confirms.
       * Closes it without further action otherwise.
       */
      $scope.remove = function ($event, name, id, index) {
        if ($event) { $event.preventDefault(); }
        var message = 'Are you sure you want to permanently remove project "' + name + '"?';
        modalService.confirm(
          function (){ removeProject(name, id, index); },
          function (){  },
          'Yes, remove this project',
          'No',
          message,
          'Remove project'
        );
      };

      initialize();
  });

});

