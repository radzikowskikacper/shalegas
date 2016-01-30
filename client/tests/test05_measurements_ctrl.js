/**
 * @file test05_measurements_ctrl.js
 * @brief Unit tests for measurements management 
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

var mCtrls = angular.injector(['ng', 'measurementsControllers']);

module('measurementsControllersSpec',
        {
            setup: function()
                {
                    modal_errwin_data = null;

                    test_boreholes = prepareTestData();

                    scope = mCtrls.get('$rootScope').$new();
                    controller = mCtrls.get('$controller');
                    filter = mCtrls.get('$filter');
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

test('dataControllerSpec', function(){
	scope.filters = {mon : false, meanings : [1], son: false, stratigraphy : [1]};
	scope.query = {stop_depth : 5000 };
	scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };

	httpbackend.expectGET('srvsweetspot/ajax/data?start_depth=0&stop_depth=3500&type=ALL_BHS').respond(200, 'test_content');
	controller('dataController', {$scope : scope, Data : appinj.get('Data')});
	scope.$apply();
	httpbackend.flush();
	
	equal(scope.limit, 0);
	scope.increaseLimit();
	equal(scope.limit, 30);
	scope.increaseLimit();
	equal(scope.limit, 35);

	httpbackend.expectGET('srvsweetspot/ajax/data?start_depth=0&stop_depth=3500&type=ALL_BHS').respond(200, 'test_content');
	scope.filters.mon = !scope.filters.mon;
	scope.$apply();
	httpbackend.flush();

	httpbackend.expectGET('srvsweetspot/ajax/data?start_depth=0&stop_depth=3500&type=ALL_BHS').respond(200, 'test_content');
	scope.filters.meanings.push(5);
	scope.$apply();
	httpbackend.flush();
	
	delete scope.query.stop_depth;
	scope.filters.mon = !scope.filters.mon;
	scope.$apply();
});

test('boreholeTablesControllerSpec', function(){
	scope.query = {start_depth : 0, stop_depth : 3500};
	scope.filters = {mon : false, meanings : [], son: false, stratigraphy : [1]};
	scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };
	scope.borehole_id = test_id;
	
	httpbackend.expectGET('srvsweetspot/ajax/tables/' + test_id + '/?start_depth=0&stop_depth=3500').respond(200, 'test_content');
	controller('boreholeTablesController', {$scope : scope, Tables : appinj.get('Tables')});
	scope.$apply();
	httpbackend.flush();
	
	equal(scope.measurements, 'test_content');
	
    httpbackend.expectGET('srvsweetspot/ajax/tables/' + test_id + '/?start_depth=0&stop_depth=3500').respond(200);
    scope.query.start_depth++;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/tables/' + test_id + '/?start_depth=0&stop_depth=3500').respond(200);
    scope.query.stop_depth++;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/tables/' + test_id + '/?start_depth=0&stop_depth=3500').respond(200);
    scope.filters.mon = !scope.filters.mon;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/tables/' + test_id + '/?start_depth=0&stop_depth=3500').respond(200);
    scope.filters.meanings.push('a');
    scope.$apply();
    httpbackend.flush();
    
    ok(angular.isUndefined(scope.error));
    httpbackend.expectGET('srvsweetspot/ajax/tables/' + test_id + '/?start_depth=0&stop_depth=3500').respond(500, 'error');
    scope.filters.meanings.push('a');
    scope.$apply();
    httpbackend.flush();
    equal(scope.error, 'error');

    delete scope.query.stop_depth;
    scope.$apply();
    
    equal(scope.limit, 0);
    scope.increaseLimit();
    equal(scope.limit, 30);
    scope.increaseLimit();
    equal(scope.limit, 35);
	
});

test('boreholeStatigraphyControllerSpec', function(){
	var modal_init_data,
	modal = prepareFakeModal(function(init) { modal_init_data = init; });
	
	scope.borehole_id = test_id;
	scope.query = {start_depth : 0, stop_depth : 3500};
	scope.filters = {on : false, meanings : []};
	scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };
	scope.dictvals = {};
	
    scope.prepareQuery = function(type, data){
    	var temp = {'query' : scope.prepareFilters(type)};
    	for(i in data)
    		temp[i] = data[i];
    	return temp;
    };
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/?filter=STRAT').respond(200, [{'id' : 3}, {'id' : 4}]);
	httpbackend.expectGET('srvsweetspot/ajax/stratigraphy/' + test_id + '/?start_depth=0&stop_depth=3500&type=STRAT').respond(200, 
			{'header' : [{id: 12}, {id:13}], 'data' : [1, 2, 3, 4]});
	httpbackend.expectGET('srvsweetspot/ajax/meanings/3/').respond(200, 'a');
	httpbackend.expectGET('srvsweetspot/ajax/meanings/4/').respond(200, 'b');
	controller('boreholeStratigraphyController', {$scope : scope, Stratigraphy : appinj.get('Stratigraphy'), $modal : modal,
		Meanings : Meanings});
	scope.$apply();
	httpbackend.flush();

	deepEqual(scope.dicts, ['a', 'b']);
	deepEqual(scope.stratigraphy, {'header' : [{id: 12}, {id:13}], 'data' : [1, 2, 3, 4]});
	
	httpbackend.expectPOST('srvsweetspot/ajax/stratigraphy/' + test_id + '/').respond(500, 'test_error_content');
	scope.addStratigraphy({12 : 3, 13 : 5});
	httpbackend.flush();
	ok(angular.isDefined(scope.errwin));
	equal(modal_init_data.resolve.content(), 'test_error_content');

	httpbackend.expectPOST('srvsweetspot/ajax/stratigraphy/' + test_id + '/').respond(200);
	scope.addStratigraphy({12 : 3, 13 : 5});
	httpbackend.flush();
});

test('boreholeChartsControllerSpec', function(){
	scope.query = {start_depth : 0, stop_depth : 3500};
	scope.filters = {mon : false, meanings : [], son: false, stratigraphy : [1]};
	scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };
	scope.borehole_id = test_id;

	httpbackend.expectGET('srvsweetspot/ajax/charts/' + test_id + '?lang=en&start_depth=' + scope.query.start_depth + 
    		'&stop_depth=' + scope.query.stop_depth).respond(200, 
    				[{name : 'test_name1', unit : 'test_unit1', data : [[1, 2], [2, 3]]}, 
    				 {name : 'test_name2', unit : 'test_unit1', data : [[4, 5], [6, 7]]}]);
    controller('boreholeChartsController', {$scope : scope, $filter : filter, $translate : translate,
    	Charts : appinj.get('Charts')});
    scope.$apply();

    httpbackend.flush();
    ok(!scope.unit_pair);
    equal(scope.charts[0].name, 'test_name1');
    equal(scope.charts[0].unit, 'test_unit1');
    deepEqual(scope.charts[0].data, [[1, 2], [2, 3]]); 
    deepEqual(scope.charts[1].data, [[4, 5], [6, 7]]); 
    
    scope.charts = [{unit : 'test_unit1', names : ['test_name1', 'test_name2'], data : [[[1, 2]], [[2, 3]]]},
                    {unit : 'test_unit2', names : ['test_name3', 'test_name4'], data : [[[3, 4]], [[5, 6]]]}]
    scope.unit_pair = true;    
    scope.drawCharts();
    
    httpbackend.expectGET('srvsweetspot/ajax/charts/' + test_id + '?lang=en&start_depth=' + scope.query.start_depth +
    		'&stop_depth=' + scope.query.stop_depth + '&unit_pair=true').respond(200);
    scope.query.start_depth++;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/charts/' + test_id + '?lang=en&start_depth=0&stop_depth=3500&unit_pair=true').respond(200);
    scope.query.stop_depth++;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/charts/' + test_id + '?lang=en&start_depth=0&stop_depth=3500&unit_pair=true').respond(200);
    scope.filters.mon = !scope.filters.mon;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/charts/' + test_id + '?lang=en&start_depth=0&stop_depth=3500&unit_pair=true').respond(200);
    scope.filters.meanings.push('a');
    scope.$apply();
    httpbackend.flush();
    
    ok(angular.isUndefined(scope.error));
    httpbackend.expectGET('srvsweetspot/ajax/charts/' + test_id + '?lang=en&start_depth=0&stop_depth=3500&unit_pair=true').respond(500, 'error');
    scope.filters.meanings.push('a');
    scope.$apply();
    httpbackend.flush();
    equal(scope.error, 'error');

    delete scope.query.stop_depth;
    scope.$apply();
    
    equal(scope.limit, 5);
    scope.increaseLimit();
    equal(scope.limit, 10);
});

test('boreholeImportExportController', function(){
    var modal_init_data,
    modal = prepareFakeModal(function(init) { modal_init_data = init; });

    controller('boreholeImportExportController', {$scope : scope, Measurements : Measurements, $modal : modal,
    	Meanings : appinj.get('Meanings')});
	
    scope.showCsvModal(test_id);
    deepEqual(modal_init_data, {
		templateUrl: 'partials/csv_modal.html',
	    controller: 'csvUploadController',
	    keyboard : false,
	    backdrop : 'static',
	    scope : scope
	});
    
    scope.showExportModal();
    deepEqual(modal_init_data, {
		templateUrl: 'partials/export_modal.html',
		controller: 'exportController',
		keyboard : false,
		backdrop : 'static',
		scope : scope
	});
});

test('boreholeMeasurementsController', function(){
    var modal_init_data,
    modal = prepareFakeModal(function(init) { modal_init_data = init; });
    scope.query = {start_depth : 0, stop_depth : 3500};
    scope.filters = {mon : false, meanings : [], son: true, stratigraphy : [1]};
    scope.borehole_id = test_id;
    scope.prepareFilters = function(type){ return {start_depth : 0, stop_depth : 3500, type : type}; };
    scope.prepareQuery = function(type, data){
    	var temp = {'query' : scope.prepareFilters(type)};
    	for(i in data)
    		temp[i] = data[i];
    	return temp;
    };
    scope.makePath = function(){return 'path';};
    scope.imgHeight = 500;

    httpbackend.expectGET('srvsweetspot/ajax/meanings/?filter=PICT').respond(200, [{'meanings' : [1, 2, 3]}, {'meanings' : [4, 5, 6]}]);
    httpbackend.expectGET('srvsweetspot/ajax/meanings/?filter=NDICT').respond(200, [{meanings : [1, 2]}, {meanings : [3, 4]}]);
    httpbackend.expectGET('srvsweetspot/ajax/meanings/?filter=DICT').respond(200, [{meanings : [5, 6]}, {meanings : [7, 8]}]);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=' + scope.query.start_depth + 
    		'&stop_depth=' + scope.query.stop_depth + '&type=NDICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=' + scope.query.start_depth + 
    		'&stop_depth=' + scope.query.stop_depth + '&type=DICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=' + scope.query.start_depth + 
    		'&stop_depth=' + scope.query.stop_depth + '&type=PICT').respond(200, []);
        
    controller('boreholeMeasurementsController', {$scope : scope, $log : appinj.get('$log'), Meanings : appinj.get('Meanings'), 
    	Measurements : Measurements, $modal : modal, $translate : translate, Images : appinj.get('Images'),
    	formDataObject : appinj.get('formDataObject'), $filter : appinj.get('$filter')});
    
    scope.$apply();
    httpbackend.flush();

    deepEqual(scope.dictionary_meanings, [5, 6, 7, 8]);
    deepEqual(scope.real_meanings, [1, 2, 3, 4]);
    deepEqual(scope.pict_meanings, [1, 2, 3, 4, 5, 6]);
    equal(scope.limit, 20);
    scope.increaseLimit();
    equal(scope.limit,40);
    
    deepEqual(scope.newValue, {});

    test_data = {'depth_from' : test_depth, 'drilling_depth' : test_depth + 10, 'value' : test_value, 
    		'meaning' : {'name' : test_bh_name, 'section' : test_section}};
    
    scope.newValue = test_data;
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(200, 'test_data');
    scope.addValue(scope.newValue);
    httpbackend.flush();
    deepEqual(scope.newValue, {});

    equal(scope.real_measurements, 'test_data');
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/10/').respond(200, {unit : '%'});
    scope.newValue.meaning = 10;
    scope.$apply();
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(500, 'test_error');
    scope.addValue(scope.newValue);
    httpbackend.flush();
    equal(scope.valueUnit, '%');
    
    ok(angular.isObject(scope.errwin));
    equal(modal_init_data.resolve.content(), 'test_error');
    
    delete scope.errwin;

    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/' + test_id + '/').respond(200, 'test_data1');
    scope.deleteValue(test_id);
    httpbackend.flush();
    
    equal(scope.real_measurements, 'test_data1');
    
    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/' + test_id + '/').respond(500, 'test_error1');
    scope.deleteValue(test_id);
    httpbackend.flush();

    ok(angular.isObject(scope.errwin));
    equal(modal_init_data.resolve.content(), 'test_error1');
   
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(200, 'test_data2');
    scope.addDictionary(scope.newDictionary);
    httpbackend.flush();
    equal(scope.dictionary_measurements, 'test_data2');
 
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(500, 'test_error2');
    scope.addDictionary(scope.newDictionary);
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    equal(modal_init_data.resolve.content(), 'test_error2');
    
    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/' + test_id + '/').respond(200, 'test_data3');
    scope.deleteDictionary(test_id);
    httpbackend.flush();
    equal(scope.dictionary_measurements, 'test_data3');

    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/' + test_id + '/').respond(500, 'test_error3');
    scope.deleteDictionary(test_id);
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    equal(modal_init_data.resolve.content(), 'test_error3');

    httpbackend.expectGET('srvsweetspot/ajax/meanings/' + test_id + '/').respond(200, 'test_data5');
    scope.newDictionary.meaning = test_id;
    scope.$apply();
    httpbackend.flush();
    equal(scope.dictvals, 'test_data5');

    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=' + scope.query.start_depth +
    		'&stop_depth=' + scope.query.stop_depth + '&type=NDICT').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=' + scope.query.start_depth + 
    		'&stop_depth=' + scope.query.stop_depth + '&type=DICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=PICT').respond(200);
    scope.query.start_depth++;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=NDICT').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=DICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=PICT').respond(200);
    scope.query.stop_depth++;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=NDICT').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=DICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=PICT').respond(200);
    scope.filters.mon = !scope.filters.mon;
    scope.$apply();
    httpbackend.flush();
    
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=NDICT').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=DICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=PICT').respond(200);
    scope.filters.meanings.push('a');
    scope.$apply();
    httpbackend.flush();
    
    ok(angular.isUndefined(scope.rerror));
    ok(angular.isUndefined(scope.gerror));
    ok(angular.isUndefined(scope.derror));
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=NDICT').respond(500, 'er1');
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=DICT').respond(500, 'er2');
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=PICT').respond(500, 'er3');
    scope.filters.stratigraphy.push('a');
    scope.$apply();
    httpbackend.flush();
    
    equal(scope.rerror, 'er1');
    equal(scope.derror, 'er2');
    equal(scope.gerror, 'er3');

    delete scope.query.stop_depth;
    scope.$apply();
    
    scope.prepareFilters = function(){
    	scope.query = {filter : [1, 2, 3, 0]};
    	return scope.query;
    };
    
    scope.getMeasurementsImage();
    equal(scope.path, 'path&filter=1&filter=2&filter=3&filter=0');
    scope.prepareFilters = function(type){ return {start_depth : 0, stop_depth : 3500, type : type}; };

    ok(scope.isInvalid({'$invalid' : true}));
    ok(!scope.isInvalid({'$invalid' : false}));
    
    delete scope.query.stop_depth;
    
    scope.shown.push(5);
    ok(scope.shownId(5));
    ok(!scope.shownId(4));
    
    scope.toggleShow(7);
    ok(scope.shownId(7));
    scope.toggleShow(7);
    ok(!scope.shownId(7));    
    
    httpbackend.expectGET('srvsweetspot/ajax/meanings/5/').respond(200, {'unit' : '$'});
    scope.newGraphics.meaning = 5;
    scope.$apply();
    httpbackend.flush();
    equal(scope.graphicsUnit, '$');    
    
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(200, 'test_content2');
    scope.addGraphics({a : 5, b : 6});
    httpbackend.flush();
    equal(scope.pict_measurements, 'test_content2');
    
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(500, 'test_error');
    scope.addGraphics();
    httpbackend.flush();
    equal(modal_init_data.resolve.content(), 'test_error');
    
    httpbackend.expectPOST('srvsweetspot/ajax/measurements/' + test_id + '/').respond(530, 'test_error22');
    scope.addGraphics();
    httpbackend.flush();
    
    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/' + test_id + '/').respond(200, 'test_content3');
    scope.deleteGraphics(test_id);
    httpbackend.flush();
    equal(scope.pict_measurements, 'test_content3');

    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/' + test_id + '/').respond(500, 'test_content4');
    scope.deleteGraphics(test_id);
    httpbackend.flush();
    equal(modal_init_data.resolve.content(), 'test_content4');

	scope.showMeaningChoice();
    deepEqual(modal_init_data, {
		templateUrl: 'partials/delete_by_meaning_modal.html',
		controller: 'exportController',
		keyboard : false,
		backdrop : 'static',
		scope : scope
	});
	scope.filters.mon = false;
	scope.$apply();
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=NDICT').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=DICT').respond(200, []);
    httpbackend.expectGET('srvsweetspot/ajax/measurements/' + test_id + '/?start_depth=0&stop_depth=3500&type=PICT').respond(200);
	scope.meaning_selection_modal.close();
	httpbackend.flush();
});

test('boreholePhotosControllerSpec', function(){
    var modal_init_data,
    modal = prepareFakeModal(function(init) { modal_init_data = init; });
    scope.query = {start_depth : 250, stop_depth : 4500};
    scope.imgHeight = 100;
    scope.filters = {on : false, meanings : []};
    scope.borehole_id = test_id;
    //scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };
    scope.version = {image_width_px : 200, image_height_px : 1059};
    scope.step = 4;
	scope.makePath = function(prefix, borehole_id, begin, end, height, width) {
        if(!end)
        	return;            	

		var addr =  "/srvsweetspot/ajax/%prefix/%boreholeId/%begin-%end/%width-%height";
		return addr.replace('%prefix', prefix).replace("%boreholeId", borehole_id).
		replace("%begin", begin).replace('%width', width).replace("%end", end).replace('%height', height) + 
        '/?' + new Date().getTime();
	};

	httpbackend.expectGET("srvsweetspot/ajax/image?borehole_id=%id&start_depth=%s&stop_depth=%e".replace('%id', test_id).replace('%s',
			scope.query.start_depth).replace('%e', scope.query.stop_depth)).respond(200);
    controller('boreholePhotosController', {$scope : scope, $log : log, 
    	$http : http, $modal : modal, $translate : appinj.get('$translate'), $filter : appinj.get('$filter'), formDataObject : appinj.get('formDataObject'),
    	createXhr : appinj.get('createXhr'), Images : appinj.get('Images'), Sysinfo : appinj.get('Sysinfo')});
    scope.$apply();
    httpbackend.flush();
    deepEqual(scope.new_entry, {
            borehole_id : test_id,
            image_path : ''
        });

    equal(scope.limit, 10);
    scope.increaseLimit();
    equal(scope.limit, 20);

    httpbackend.expectGET("srvsweetspot/ajax/image?borehole_id=%id&start_depth=%s&stop_depth=%e".replace('%id', test_id).replace('%s',
			scope.query.start_depth).replace('%e', scope.query.stop_depth)).respond(200);
    scope.getPictures();
    httpbackend.flush();
    
    ok(angular.isUndefined(scope.fullimg));
    scope.getFullImage();
    ok(scope.full_img_path.indexOf('/srvsweetspot/ajax/borehole_image/' + test_id + '/250-251/18-100' + '/?') != -1);
    deepEqual(scope.fullimg, {zoom : false, height : 100, start : 250, width : 18});

    scope.getFullImage(true);
    ok(scope.fullimg.zoom);
    ok(scope.full_img_path.indexOf('/srvsweetspot/ajax/borehole_image/' + test_id + '/250-251/0-0' + '/?') != -1);
    scope.getFullImage(true);
    ok(!scope.fullimg.zoom);
    ok(scope.full_img_path.indexOf('/srvsweetspot/ajax/borehole_image/' + test_id + '/250-251/18-100' + '/?') != -1);
    
    httpbackend.expectPUT('srvsweetspot/ajax/image').respond(500);
    ok(angular.isUndefined(scope.errwin));
    scope.regenerateHelperPhotos();
    httpbackend.flush();
    ok(angular.isDefined(scope.errwin));
    
    httpbackend.expectPUT('srvsweetspot/ajax/image').respond(200);
    scope.regenerateHelperPhotos();
    httpbackend.flush();
    
    scope.modalInstance.close('test');
    equal(modal_init_data.resolve.content(), 'test');
    
    httpbackend.expectGET("srvsweetspot/ajax/image?borehole_id=%id&start_depth=%s&stop_depth=%e".replace('%id', test_id).replace('%s',
			scope.query.start_depth).replace('%e', scope.query.stop_depth)).respond(200);
    scope.modalInstance.close('ok');
    httpbackend.flush();
    
    httpbackend.expectPOST('srvsweetspot/ajax/image').respond(500, 'test_err');
    scope.addEntry({});
    scope.errwin.close();
    httpbackend.flush();
    
    httpbackend.expectPOST('srvsweetspot/ajax/image').respond(415, 'test err');
    httpbackend.expectGET("srvsweetspot/ajax/image?borehole_id=%id&start_depth=%s&stop_depth=%e".replace('%id', test_id).replace('%s',
			scope.query.start_depth).replace('%e', scope.query.stop_depth)).respond(200);
    scope.addEntry({});
    scope.errwin.close();
    httpbackend.flush();

    httpbackend.expectPOST('srvsweetspot/ajax/image').respond(200);
    httpbackend.expectGET("srvsweetspot/ajax/image?borehole_id=%id&start_depth=%s&stop_depth=%e".replace('%id', test_id).replace('%s',
			scope.query.start_depth).replace('%e', scope.query.stop_depth)).respond(200);
    scope.addEntry({});
    scope.errwin.close();
    httpbackend.flush();
    
    httpbackend.expectDELETE('srvsweetspot/ajax/image/' + test_id).respond(200);
    httpbackend.expectGET("srvsweetspot/ajax/image?borehole_id=%id&start_depth=%s&stop_depth=%e".replace('%id', test_id).replace('%s',
			scope.query.start_depth).replace('%e', scope.query.stop_depth)).respond(200);
    scope.removeEntry(test_id);
    scope.errwin.close();
    httpbackend.flush();
    
    scope.query.start_depth = scope.query.stop_depth - 1;
    scope.$apply();
    ok(scope.full_img_path.indexOf('/srvsweetspot/ajax/borehole_image/' + test_id + '/4499-4500/18-100' + '/?') != -1);
    
    delete scope.query.stop_depth;
    
    scope.sendArchive(test_id, 'path');
    equal(scope.progress, 0);
});

test('csvUploadControllerSpec', function(){
    scope.archive = {'path' : 'path'};

    httpbackend.expectGET('srvsweetspot/ajax/meanings/').respond(200, [{'meanings' : [1, 2, 3]}, {'meanings' : [4, 5, 6]}]);
	controller('csvUploadController', {$scope : scope, $translate : translate, $modalInstance : fakeModal.open(), createXhr : appinj.get('createXhr'),
		Meanings : Meanings});
	httpbackend.flush();
	
    deepEqual(scope.modalData, {'column' : 1});
    deepEqual(scope.sections, [1, 2, 3, 4, 5, 6]);
    
    scope.modalData.meaning = {'id' : 1};
    scope.ok();
    
    scope.cancel();
});

test('exportModal', function() {
	var modal_init_data;
    var modal = prepareFakeModal(function(init) { modal_init_data = init; });
	scope.borehole_id = 1;
	translate.use('en');
	httpbackend.expectGET('srvsweetspot/ajax/meanings/').respond(200, [{meanings : [1, 2]}, {meanings : [3, 4]}]);
	controller('exportController', {$scope : scope, $filter : appinj.get('$filter'), $modalInstance : fakeModal.open(), 
    	$modal : modal, Meanings : appinj.get('Meanings'), $translate : translate, Measurements : appinj.get('Measurements')});
	httpbackend.flush();
	
	deepEqual(scope.exportData, {});
	scope.ok();
	
	scope.exportData.begin = 100;
	scope.exportData.end = 200;
	scope.meanings = [{ticked : true, id : 1}, {id : 2, ticked :false}];
	httpbackend.expectPOST('srvsweetspot/ajax/measurements/export/1/100-200/en').respond(200, {filename : 'filename'});
	scope.ok();
	httpbackend.flush();
	httpbackend.expectPOST('srvsweetspot/ajax/measurements/export/1/100-200/en').respond(500, test_error_content);
	scope.ok();
	httpbackend.flush();
	
	scope.cancel();

	scope.prepareFilters = function(){ return {start_depth : 0, stop_depth : 3500}; };
    scope.prepareQuery = function(type, data){
    	var temp = {'query' : scope.prepareFilters(type)};
    	for(i in data)
    		temp[i] = data[i];
    	return temp;
    };
    scope.borehole_id = 2;
    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/2').respond(200);
	scope.deleteByMeaning();
	httpbackend.flush();

    httpbackend.expectDELETE('srvsweetspot/ajax/measurements/2').respond(500);
	scope.deleteByMeaning();
	httpbackend.flush();
});

test('modalController', function(){
	controller('modalController', {$scope : scope, $modalInstance : fakeModal.open(), Images : appinj.get('Images')});
	deepEqual(scope.progress, {max : 100, state : 0});
	
	httpbackend.expectGET('srvsweetspot/ajax/image/progress').respond(200, {status : 'Ok', progress : 20});
	scope.intervalFc();
	httpbackend.flush();
	equal(scope.progress.state, 20);
	
	httpbackend.expectGET('srvsweetspot/ajax/image/progress').respond(200, {status : 'Finished'});
	scope.intervalFc();
	httpbackend.flush();
	
	httpbackend.expectGET('srvsweetspot/ajax/image/progress').respond(200, {status : 'Size'});
	scope.intervalFc();
	httpbackend.flush();

	httpbackend.expectGET('srvsweetspot/ajax/image/progress').respond(200, {status : 'test'});
	scope.intervalFc();
	httpbackend.flush();

	httpbackend.expectGET('srvsweetspot/ajax/image/progress').respond(200, {status : 'no_archive'});
	scope.intervalFc();
	httpbackend.flush();

	httpbackend.expectPOST('srvsweetspot/ajax/image/cancel').respond(200);
	scope.cancel();
	httpbackend.flush();
});