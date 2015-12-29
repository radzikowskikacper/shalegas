/**
 * @file test02_boreholes_ctrl.js
 * @brief Unit tests for boreholes controllers
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

var bhCtrls = angular.injector(['ng', 'boreholesControllers']);

module('boreholesControllersSpec',
        {
            setup: function()
                {
                    modal_errwin_data = null;

                    test_boreholes = prepareTestData();

                    scope = bhCtrls.get('$rootScope').$new();
                    controller = bhCtrls.get('$controller');
                    filter = bhCtrls.get('$filter');
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

function check_boreholes(scope) {
    //check array size
    equal(scope.boreholes.length, test_boreholes.boreholes.length);

    deepEqual(scope.boreholes, test_boreholes.boreholes);
};

//prepare data
function prepareTestData()
{
    var test_data = [];

    for(var i = 0; i < test_bh_num; ++i) {
        test_data.push({'id' : i, 'name' : test_bh_name + i, 'description' : test_description + i,
                             'latitude' : test_latitude + i, 'longitude' : test_longitude + i})
    }

    return {'boreholes_version' : test_bh_version, 'boreholes' : test_data};
}

test('boreholesControllerSpec_fetchBoreholes', function()
    {
        //locals used in tests
        var location = appinj.get('$location');

        //simulate GET
        httpbackend.expectGET('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
        controller('boreholesController', {$scope : scope, $location : location, Boreholes : Bhs, $modal : fakeModal});
        httpbackend.flush();

        deepEqual(scope.opts, {0 : {'title' : 'test_borehole0'}, 1 : {'title' : 'test_borehole1'}, 2 : {'title' : 'test_borehole2'}});
        //check every property in received data
        check_boreholes(scope);
        //check if data version in service was set correctly
        equal(Bhs.version, test_bh_version);

        //erase data
        scope.boreholes = [];

        //simulate angularJS broadcast after which the proper request should be sent
        httpbackend.expectGET('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
        scope.$broadcast('OUTDATED');
        httpbackend.flush();

        //check if data was correctly pulled
        check_boreholes(scope);

        //testing $scope.showDetails
        scope.showDetails(1);

        //user should be redirected to details page
        equal(location.path(), '/boreholes/1/pictures');
    });

test('boreholesControllerSpec_showAddition', function() {
    httpbackend.expectGET('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
    controller('boreholesController', {$scope : scope, $location : location, Boreholes : Bhs, $modal : fakeModal});
    httpbackend.flush();

    //testing scope.toggleBoreholeAdding
    scope.toggleBoreholeAdding();

    ok(scope.additionForm)

    //testing failed addition
    httpbackend.expectPOST('srvsweetspot/ajax/boreholes/').respond(500, test_error_content);
    scope.addBorehole(scope.bh);
    httpbackend.flush();

    //error window should appear, with a proper error to be resolved
    ok(angular.isObject(scope.errwin));
    equal(modal_errwin_data.resolve.content(), 'test_error_content');

    scope.boreholes = [];

    //test successfull addition
    httpbackend.expectPOST('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
    scope.addBorehole(scope.bh)
    httpbackend.flush();

    //test if data received length matches
    equal(scope.boreholes.length, test_bh_num);
});

test('boreholesControllerSpec_deleteBorehole', function(){
    //simulate GET
    httpbackend.expectGET('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
    controller('boreholesController', {$scope : scope, $location : location, Boreholes : Bhs, $modal : fakeModal});
    httpbackend.flush();

    //test_error_content = angular.copy(test_boreholes);
    //test_error_content.boreholes = test_error_content.boreholes.splice(0, 2);

    //simulate failed delete
    httpbackend.expectDELETE('srvsweetspot/ajax/boreholes/2/').respond(500, 'no_borehole');
    scope.deleteBorehole(2);
    httpbackend.flush();

    //error dialog should appear, with proper error to be resolved
    ok(angular.isObject(scope.errwin));

    test_boreholes_2 = prepareTestData();
    test_boreholes_2.boreholes = _.filter(test_boreholes_2.boreholes, function(bh) { return bh.id != 2; });
    //simulate successfull deletion
    httpbackend.expectDELETE('srvsweetspot/ajax/boreholes/2/').respond(200, test_boreholes_2);
    scope.deleteBorehole(2);
    httpbackend.flush();

    //scope.boreholes_data should be overridden by data returned from server
    equal(scope.boreholes.length, test_bh_num - 1);
});

test('boreholeControllerSpec_boreholeModification', function(){
	httpbackend.expectGET('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
    controller('boreholesController', {$scope : scope, $location : location, Boreholes : Bhs, $modal : fakeModal,
    									$timeout : appinj.get('$timeout')});
    httpbackend.flush();

    ok(!scope.modificationForm);
    test_boreholes.boreholes = test_boreholes.boreholes[0];

    ok(angular.isUndefined(scope.borehole));
    httpbackend.expectGET('srvsweetspot/ajax/boreholes/' + test_id + '/').respond(200, test_boreholes);
    scope.toggleBoreholeModification(test_id);
    httpbackend.flush();
    
    ok(scope.modificationForm);
    deepEqual(scope.borehole, test_boreholes.boreholes);
    deepEqual(scope.borehole_copy, test_boreholes.boreholes);
    
    delete scope.borehole;
    
    scope.toggleBoreholeModification(test_id);
    ok(angular.isUndefined(scope.borehole));
    
    //modify borehole data
    //test_error_content = angular.copy(test_borehole);
    //test_error_content.boreholes[0].name += '_modified';
    scope.borehole_copy.name += '_modified';
    scope.borehole_copy.id = 1;

    //simulate failed modification
    httpbackend.expectPUT('srvsweetspot/ajax/boreholes/1/').respond(500, test_error_content);
    scope.modifyBorehole(scope.borehole_copy);
    httpbackend.flush();
    
    //error window should appear, with a proper error
    equal(scope.errorMsg, 'Error');
/*    setTimeout(function() {
    	equal(scope.errorMsg, '');
		start();
    }, 3000);
*/
    //simulare successfull modification
    httpbackend.expectPUT('srvsweetspot/ajax/boreholes/1/').respond(200, test_boreholes);
    httpbackend.expectGET('srvsweetspot/ajax/boreholes/').respond(200, test_boreholes);
    scope.modifyBorehole(scope.borehole_copy);
    httpbackend.flush();
});

test('boreholesControllerSpec_cm2mFilter', function(){
    equal(filter('cm2m')('1000'), 10);
    equal(filter('cm2m')('100'), 1);
    equal(filter('cm2m')('0'), 0);
    equal(filter('cm2m')('150'), 1.5);
});

test('boreholesControllerSpec_ssDecimal', function(){
    scope.decvalue = '10.52';
    ok(ss_decimal.hasClass('ng-valid'));
});

test('boreholeDetailsControllerSpec', function() {
	var location = appinj.get('$location');
	var test_borehole = {'id' : test_id, 'name' : test_bh_name, 'latitude' : test_latitude,
            'longitude' : test_longitude, 'description' : test_description},
    test_borehole = {'boreholes_version' : test_bh_version, 'boreholes' : [test_borehole]};
	
	scope.query = {start_depth : 0};
	//httpbackend.expectGET('srvsweetspot/ajax/meanings/').respond(200, [{meanings : [1, 2]}, {meanings : [3, 4]}]);
	httpbackend.expectGET('srvsweetspot/ajax/boreholes/1/').respond(200, test_borehole);
    controller('boreholeDetailsController', {$scope : scope, $location : location, Boreholes : Bhs, $stateParams : {boreholeId : test_id},
    										$translatePartialLoader : translatePartialLoader, $translate : translate,
    										Meanings : Meanings});
	
    httpbackend.flush();
    
    scope.$apply();

    equal(scope.borehole_id, test_id);

    scope.$broadcast('SetDepthEvent', {begin : 100, end : 150, step : 5});
    equal(scope.query.start_depth, 100);
    equal(scope.query.stop_depth, 150);
    equal(scope.step, 5);

    ok(scope.makePath('borehole_image', test_id, 1200, 1300, 1234, 100).indexOf( 
    		"/srvsweetspot/ajax/borehole_image/" + test_id + "/1200-1300/100-1234" + '/?') != -1);

    ok(scope.makePath('measurements/intervals', test_id, 1200, 1300, 1234, 123).indexOf( 
    		"/srvsweetspot/ajax/measurements/intervals/" + test_id + "/1200-1300/123-1234" + '/?') != -1);
    
    ok(angular.isUndefined(scope.makePath('borehole_image', test_id, 0)));
    ok(angular.isUndefined(scope.makePath('borehole_image', test_id, 0, undefined, 120)));    
    
    scope.goToList();
    equal(location.path(), '/boreholes');
});

test('boreholeSimilarityController', function(){
    scope.query = {start_depth : 250, stop_depth : 3500};
    scope.filters = {on : false, meanings : []};
    scope.borehole_id = test_id;
    scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };
    scope.borehole_id = test_id;
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/?filter=STRAT').respond(200, [1, 2, 3]);
    controller('boreholeSimilarityController', {$scope : scope, Similarity : appinj.get('Similarity'), Meanings : Meanings});	
    scope.$apply();
    httpbackend.flush();
    deepEqual(scope.stratigraphy, [1, 2, 3]);
    
    scope.filters.meanings.push(1);
	scope.$apply();

	httpbackend.expectGET('srvsweetspot/ajax/meanings/13/').respond(200, {'dictvals' : [{'id' : 3, 'value' : 'test_value3'},
	                                                                                    {'id' : 4, 'value' : 'test_value4'}]});
    scope.stratigraphy_level = 13;
    scope.filters.meanings.push(2);
	scope.$apply();
	httpbackend.flush();
	deepEqual(scope.dictvals, [{'id' : 3, 'value' : 'test_value3'}, {'id' : 4, 'value' : 'test_value4'}]);

	httpbackend.expectGET('srvsweetspot/ajax/similarities/' + test_id + '/?epochs=3&epochs=4&start_depth=0&stop_depth=3500&stratigraphy_level=13').respond(200, 
    		[{name : 'a', similarity : 10}, {name : 'b', similarity : 5}]);
    scope.epochs.push(3, 4);
	scope.$apply();
	httpbackend.flush();

	httpbackend.expectGET('srvsweetspot/ajax/similarities/' + test_id + '/?epochs=3&epochs=4&start_depth=0&stop_depth=3500&stratigraphy_level=13').respond(200, 
    		[{name : 'a', similarity : 10}, {name : 'b', similarity : 5}]);
    scope.filters.on = true;
    scope.filters.meanings.push(6);
	scope.$apply();
	httpbackend.flush();

	deepEqual(scope.similarities, [{name : 'a', similarity : 10}, {name : 'b', similarity : 5}]);
	
	scope.epochs = [];
	scope.toggleEpoch(5);
	deepEqual(scope.epochs, [5]);
	scope.toggleEpoch(6);
	deepEqual(scope.epochs, [5, 6]);
	scope.toggleEpoch(5);
	deepEqual(scope.epochs, [6]);
	scope.toggleEpoch(6);
	deepEqual(scope.epochs, []);	
});

test('rangeFilterSpec', function(){
	var $filter = appinj.get('$filter');
	
	deepEqual($filter('range')([], 5), [0, 1, 2, 3, 4]);
	deepEqual($filter('range')([], 3), [0, 1, 2]);
});