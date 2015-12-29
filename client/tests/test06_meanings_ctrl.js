/**
 * @file test06_meanings_ctrl.js
 * @brief Unit tests for meanings and sections management 
 */

var test_bh_num = 3;
var test_id = 1;
var test_bh_version = 2;
var test_bh_name = "test_borehole";
var test_latitude = 12;
var test_longitude = 23;
var test_description = "test_description";
var test_value = 5;
var test_section = 'test_section';
var test_depth = 34;

var mnCtrls = angular.injector(['ng', 'meaningsControllers']);

module('meaningsControllersSpec',
        {
            setup: function()
                {
                    modal_errwin_data = null;

                    test_boreholes = prepareTestData();

                    scope = mCtrls.get('$rootScope').$new();
                    controller = mnCtrls.get('$controller');
                    filter = mnCtrls.get('$filter');
                    Bhs = appinj.get('Boreholes');
                    Meanings = appinj.get('Meanings');
                    Measurements = appinj.get('Measurements');
                    http = appinj.get('$http');
                    log = appinj.get('$log');
                    
                    fakeModal = prepareFakeModal(function(data){
                        modal_errwin_data = data;
                    });

                    $compile = bhCtrls.get('$compile');
                    ss_decimal = angular.element('<input type="text" ng-model="decvalue" ss-decimal/>');
                    $compile(ss_decimal)(scope);
                    scope.$digest();

                    translatePartialLoader = appinj.get('$translatePartialLoader');
                    translate = appinj.get('$translate');
                },

            teardown : function()
                {
                    httpbackend.verifyNoOutstandingExpectation();
                    httpbackend.verifyNoOutstandingRequest();
                }
        });

test('meaningsControllerSpec', function(){
    var test_meanings = [];
    var location = appinj.get('$location');
    var modal_data;
    var modal = prepareFakeModal(function(init){ modal_data = init });
    
    for(i = 0; i < 3; ++i){
        temp = {'name' : test_section + i};
        temp['meanings'] = {'id' : i, 'name' : test_name + i, 'section' : test_section + i, 'unit' : test_unit + i};
        test_meanings.push(temp);
    }
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/').respond(200, test_meanings);
    controller('meaningsController', {$scope : scope, Meanings : meaningsService, $location : location, 
        $translatePartialLoader : translatePartialLoader, $modal : modal, $translate : translate});
    httpbackend.flush();
    
    deepEqual(scope.meanings, test_meanings);
    ok(!scope.additionForm);
    
    scope.toggleAddition();
    ok(angular.isObject(scope.newMeaning));
    ok(scope.additionForm);
    
    var test_meaning = {type : true, name : 'test_name', unit : 'test_unit', 'dictvals' : [{'value' : '%'}, '&']};
    httpbackend.expectPOST('srvsweetspot/ajax/meanings/').respond(200, 'test_content');
    scope.addMeaning(test_meaning);
    httpbackend.flush();
    deepEqual(test_meaning, {type : true, name : 'test_name', unit : 'test_unit', 'dictvals' : ['%', '&']});
    equal(scope.meanings, 'test_content');
    ok(!scope.additionForm);
    
    scope.toggleAddition();
    ok(!angular.isObject(scope.errwin));
    httpbackend.expectPOST('srvsweetspot/ajax/meanings/').respond(500, 'test_error');
    scope.addMeaning({});
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    equal(modal_data.resolve.type(), 'ERROR');
    equal(modal_data.resolve.content(), 'test_error');
    
    scope.errwin.close();
    
    httpbackend.expectDELETE('srvsweetspot/ajax/meanings/' + test_id + '/').respond(200, 'test_content2');
    scope.deleteMeaning(test_id);
    httpbackend.flush();
    equal(scope.meanings, 'test_content2');
    
    httpbackend.expectDELETE('srvsweetspot/ajax/meanings/' + test_id + '/').respond(500, 'test_error2');
    scope.deleteMeaning(test_id);
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    equal(modal_data.resolve.type(), 'ERROR');
    equal(modal_data.resolve.content(), 'test_error2');
    
    scope.showMeaning(test_id);
    equal(location.path(), '/management/meanings/' + test_id);
})

test('meaningDetailsController', function(){
    var test_meaning = {'name' : test_name, 'section' : test_section, 'unit' : test_unit};
    var modal_data;
    var location = appinj.get('$location');
    var modal = prepareFakeModal(function(data){ modal_data = data; });
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/' + test_id + '/').respond(200, test_meaning);
    controller('meaningDetailsController', {$scope : scope, Meanings : meaningsService, $location : location, 
        $translatePartialLoader : translatePartialLoader, $modal : modal, $translate : 
            translate, $stateParams : {meaningId : test_id}});
    httpbackend.flush();
    
    deepEqual(scope.meaning, test_meaning);
    ok(!scope.editMode);
    
    scope.toggleMeaningEdit();
    ok(scope.editMode);
    
    httpbackend.expectPUT('srvsweetspot/ajax/meanings/' + test_id + '/').respond(200, 'test_content');
    scope.modifyMeaning({'id' : test_id});
    httpbackend.flush();
    
    equal(location.path(), '/management/meanings');
    
    var test_meaning = {name : 'test_name', unit : 'test_unit', id : test_id, 'dictvals' : ['%', '&']};
    httpbackend.expectPUT('srvsweetspot/ajax/meanings/' + test_id + '/').respond(500, 'test_error');
    scope.dict = true;
    scope.modifyMeaning(test_meaning);
    httpbackend.flush();
    
    deepEqual(test_meaning, {unit : 'test_unit', name : 'test_name', id : test_id, 'dictvals' : ['%', '&']});
    ok(angular.isObject(scope.errwin));
    equal(modal_data.resolve.type(), 'ERROR');
    equal(modal_data.resolve.content(), 'test_error');
});

test('sectionsControllerSpec', function(){
    var modal_data;
    var modal = prepareFakeModal(function(data){ modal_data = data; });
    var test_sections = [test_section + '1', test_section + '2'];
    var location = appinj.get('$location');
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/sections/').respond(200, test_sections);
    
    controller('sectionsController', {$scope : scope, Sections : Sections, $translate : translate,
        $translatePartialLoader : translatePartialLoader, $modal : modal, $location : location});
    httpbackend.flush();
    deepEqual(scope.sections, test_sections);
    
    ok(!scope.additionForm);
    scope.toggleAddition();
    ok(scope.additionForm);
    
    scope.showSection(test_id);
    equal(location.path(), '/management/sections/' + test_id);
    
    httpbackend.expectDELETE('srvsweetspot/ajax/meanings/sections/' + test_id + '/').respond(200, test_sections.slice(0, 1));
    scope.deleteSection(test_id);
    httpbackend.flush();
    deepEqual(scope.sections, test_sections.slice(0, 1));
    
    httpbackend.expectDELETE('srvsweetspot/ajax/meanings/sections/' + test_id + '/').respond(500, 'test_error');
    scope.deleteSection(test_id);
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    equal(modal_data.resolve.content(), 'test_error');
    
    httpbackend.expectPOST('srvsweetspot/ajax/meanings/sections/').respond(200, test_sections);
    scope.addSection({name : test_name});
    httpbackend.flush();
    deepEqual(scope.sections, test_sections);
    
    httpbackend.expectPOST('srvsweetspot/ajax/meanings/sections/').respond(500, 'test_error2');
    scope.addSection({name : test_name});
    httpbackend.flush();
    
    ok(angular.isObject(scope.errwin));
    equal(modal_data.resolve.content(), 'test_error2');
});

test('sectionDetailsController', function(){
    var modal_data;
    var modal = prepareFakeModal(function(data){ modal_data = data; });
    var location = appinj.get('$location');

    controller('sectionDetailsController', {$scope : scope, Sections : Sections, $translate : translate, $stateParams : {sectionId : test_id}, 
        $translatePartialLoader : translatePartialLoader, $modal : modal, $location : location});

    deepEqual(scope.name, {name : test_id});
    equal(scope.old, test_id);
    ok(!scope.editMode);

    scope.toggleSectionEdit();
    ok(angular.isObject(scope.errwin));
    equal(modal_data.resolve.content(), 'TRANSLATION_WARNING');
    
    scope.errwin.resolve();
    ok(scope.editMode);
    delete scope.errwin;
    modal_data = null;
    
    scope.toggleSectionEdit();
    ok(angular.isUndefined(scope.errwin));
    ok(!scope.editMode);
    
    httpbackend.expectPUT('srvsweetspot/ajax/meanings/sections/' + test_id + '/').respond(200);
    scope.modifySection('test_data');
    httpbackend.flush();
    equal(location.path(), '/management/sections');
    
    httpbackend.expectPUT('srvsweetspot/ajax/meanings/sections/' + test_id + '/').respond(500, 'error');
    scope.modifySection('test_data');
    httpbackend.flush();
    ok(angular.isObject, scope.errwin);
    equal(modal_data.resolve.content(), 'error');
});