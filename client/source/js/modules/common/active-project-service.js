/**
 * activeProject is a factory that can set what's the project that should be currently in use by the UI
 * and tell you if there is any.
 */

define([
  'angular',
  '../common/local-storage-service' 
], function (angular) {
  'use strict';

  return angular.module('app.active-project', [
    'app.local-storage'
    ])
    .factory('activeProject', [ 
      '$http', 'localStorage', 'UserManager',
      function ($http, localStorage, UserManager) {
        var project = {
          setActiveProjectFor: function (projectName, projectId, user) { 
            // Sets the active project to be projectName for the given user.
            project.name = projectName;
            project.id   = projectId;
            $http.defaults.headers.common.project = project.name;
            $http.defaults.headers.common['project-id'] = project.id;
            localStorage[project.getProjectKeyFor(user)] = JSON.stringify({'name':project.name,'id':project.id});
          },
          loadProjectFor: function (user) { 
            // Load the active project for the given user.
            // Do nothing if no project found for that user.
            if(!project.hasProjectFor(user)) { return; }
            var loaded_project = JSON.parse(project.getProjectFor(user));
            project.name = loaded_project.name;
            project.id = loaded_project.id;
            $http.defaults.headers.common.project = project.name;
            $http.defaults.headers.common['project-id'] = project.id;
          },
          getProjectKeyFor: function (user) {
            // Answers the key used to locally store this project as active for the given user.
            return 'activeProjectFor:'+ user.id;
          },
          getProjectFor: function (user) {
            return localStorage[project.getProjectKeyFor(user)];
          },
          getProjectForCurrentUser: function (user) {
            var openProjectStr = this.getProjectFor(UserManager.data);
            return openProjectStr ? JSON.parse(openProjectStr) : void 0;
          },
          getProjectIdForCurrentUser: function (user) {
            var openProjectStr = this.getProjectFor(UserManager.data);
            var openProject = openProjectStr ? JSON.parse(openProjectStr) : void 0;
            return openProject ? openProject.id : void 0;
          },
          ifActiveResetFor: function (projectName, projectId, user) {
            // If projectName is active, reset it for the given user.
            if (project.id === projectId) {
              project.resetFor(user);
            }
          },
          resetFor: function (user) { 
            // Resets the projectName as the active project for the given user.
            delete project.name;
            delete project.id;
            delete $http.defaults.headers.common.project;
            delete $http.defaults.headers.common['project-id'];
            localStorage.removeItem(project.getProjectKeyFor(user));
          },  
          isSet: function() {
            return (project.name !== null && project.name !== undefined && project.id !== null && project.id !== undefined);
          },
          hasProjectFor: function (user) {
            // Answers true if there is a local project stored for the given user.
            var foundOrNot = project.getProjectFor(user);
            if (foundOrNot !== null && foundOrNot !== undefined) {
              try {
                JSON.parse(foundOrNot);
                return true;
              } catch (exception) {
                return false;
              }
            }
          }
        };

        return project;

    }]);

});
