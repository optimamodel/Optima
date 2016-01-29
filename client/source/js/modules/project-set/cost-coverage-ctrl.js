define(['./module', 'underscore'], function (module, _) {
  'use strict';

  module.controller('ModelCostCoverageController', function ($scope, $http, $state, activeProject, modalService, projectApiService) {

    var vm = this;

    /* VM vars */
    vm.openProject = activeProject.data;
    vm.activeTab = 'outcome';
    vm.fakeParams = [/* ToDo: replace with api data */
      {
        name: 'First'
      },
      {
        name: 'Second',
        coverage: true
      },
      {
        name: 'Third'
      }
    ]
    vm.post = {}
    vm.tabs = [
      {
        name: 'Define cost functions',
        slug: 'cost'
      },
      {
        name: 'Define outcome functions',
        slug: 'outcome'
      },
      {
        name: 'View summary',
        slug: 'summary'
      }
    ]
    vm.years = [{
      /* ToDo: replace with api data */
      id: 1
    }]

    /* VM functions */
    vm.populateProgramDropdown = populateProgramDropdown;
    vm.addYear = addYear;
    vm.selectTab = selectTab;
    vm.deleteYear = deleteYear;
    vm.submit = submit;

    /* Function definitions */

    function submit() {
      if (vm.TableForm.$invalid) {
        console.error('form is invalid!');
        return false;
      }

      console.log('submitting', vm.post);
    }

    function deleteYear(yearIndex) {
      vm.years = _.reject(vm.years, function (year, index) {
        return index === yearIndex
      });
    }

    function populateProgramDropdown() {
      vm.programs = vm.selectedProgramSet.programs;
    };

    function selectTab(tab) {
      vm.activeTab = tab;
    }

    function addYear() {
      vm.years.push({id: _.random(1, 10000)})
      /* ToDo: replace with api data */
    }

    /* Initialize */

    // Do not allow user to proceed if spreadsheet has not yet been uploaded for the project
    if (!vm.openProject.has_data) {
      modalService.inform(
        function () {
        },
        'Okay',
        'Please upload spreadsheet to proceed.',
        'Cannot proceed'
      );
      $state.go('project.open')
      return;
    }

    $http.get('/api/project/' + vm.openProject.id + '/progsets')
      .success(function (response) {
        if (response.progsets) {
          vm.programSetList = response.progsets;
        }
      });

    $http.get('/api/project/' + vm.openProject.id + '/parsets').success(function (response) {
      vm.parsets = response.parsets;
    });

  });

});
