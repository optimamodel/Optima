define([
  'angular',
  'ui.router',
  '../project/project-api-service',
  '../resources/model',
  '../charts/export-all-charts-directive',
], function (angular) {
  'use strict';

  return angular.module('app.model', [
    'app.export-all-charts',
    'app.resources.model',
    'ui.router',
  ])
    .config(function ($stateProvider) {
      $stateProvider
        .state('model', {
          url: '/model',
          abstract: true,
          template: '<div ui-view=""></div>'
        })
        .state('model.manual', {
          url: '/manual',
          templateUrl: 'js/modules/model/calibration.html',
          controller: 'ModelCalibrationController',
          resolve: {
            parameters: function (Model) {
              //return Model.getCalibrateParameters().$promise;
            },
            meta: function (Model) {
              // return Model.getKeyDataMeta().$promise;
            },
            info: function (projectApiService) {
              return projectApiService.getActiveProject();
            }
          }
        })
    });
});
