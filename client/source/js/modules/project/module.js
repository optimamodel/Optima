define(['angular', 'ui.router', '../common/active-project-service'], function (angular) {
  'use strict';

  return angular.module('app.project', ['app.active-project', 'ui.router'])

    .config(function ($stateProvider) {

      $stateProvider
        .state('home', {
          url: '/',
          templateUrl: 'js/modules/project/manage-projects.html',
          controller: 'ProjectOpenController',
          resolve: {
            projects: function (projectApi) {
              return projectApi.getProjectList();
            }
          }
        })
        .state('project', {
          url: '/project',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('project.create', {
          url: '/create',
          templateUrl: 'js/modules/project/create-or-edit.html',
          controller: 'ProjectCreateOrEditController',
          resolve: {
            populations: function(projectApi) {
              return projectApi.getPopulations();
            },
            info: function() {
              return undefined;
            },
            projects: function (projectApi) {
              return projectApi.getProjectList();
            }
          }
        })
        .state('project.edit', {
          url: '/edit',
          templateUrl: 'js/modules/project/create-or-edit.html',
          controller: 'ProjectCreateOrEditController',
          resolve: {
            populations: function(projectApi) {
              return projectApi.getPopulations();
            },
            info: function (projectApi) {
              return projectApi.getActiveProject();
            },
            projects: function (projectApi) {
              return projectApi.getProjectList();
            }
          }
        })
    });
});
