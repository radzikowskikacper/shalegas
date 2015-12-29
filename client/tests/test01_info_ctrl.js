/**
 * @file test01_info_ctrl.js
 * @brief Unit tests for support controllers
 */

//angular application injectors
var appinj = angular.injector(['ngMock', 'ng', 'sweetspotApp']);
var infoCtrls = angular.injector(['ng', 'infoControllers']);
var httpbackend = appinj.get('$httpBackend');
var userService = appinj.get('User');

//data prepared for tests
var test_username = "test_username";

var test_error_content = "test_error_content";

//simulate dictionaries
httpbackend.whenGET('lang/en/main.json').respond(200, []);
httpbackend.whenGET('lang/en/meanings.json').respond(200, []);
httpbackend.whenGET('partials/forms/meaning-mod.html').respond(200, []);

//fake modal class, simulating angular modal window
function FakeModal(close_clbk, dismiss_clbk) {
    this.resolve = null;
    this.reject = null;
    that = this;

    this.close = function(status) {
        if(close_clbk !== null && close_clbk !== undefined)
            close_clbk(status);

        if(this.resolve != null)
            this.resolve(status);
    };

    this.dismiss = function(reason) {
        if(dismiss_clbk !== null && dismiss_clbk !== undefined)
            dismiss_clbk(reason);

        if(this.reject != null)
            this.reject(reason);
    };

    this.result = {
        then : function(succ_clbk, err_clbk) {
            that.resolve = succ_clbk;
            that.reject = err_clbk;
        }
    };
}

function prepareFakeModal(open_clbk, close_clbk, dismiss_clbk) {
    return {
        open : function(init_data) {
            if(open_clbk != null)
                open_clbk(init_data);

            return new FakeModal(close_clbk, dismiss_clbk);
        }
    };
}

module('infoControllersSpec',
       {
           setup: function()
           {
               scope = infoCtrls.get('$rootScope').$new();
               controller = infoCtrls.get('$controller');
               
               translate = appinj.get('$translate');
           },

           teardown : function()
           {
               httpbackend.verifyNoOutstandingExpectation();
               httpbackend.verifyNoOutstandingRequest();
           }
       });

test('errorControllerSpec', function()
     {
         var stat, //status passed as parameter to modal.close()
         fakeModal = prepareFakeModal(null, function(s){ stat = s; });

         controller('promptController',{ $scope : scope, type : 'error',
                                        $modalInstance : fakeModal.open(), content : test_error_content, type : 'error'});

         equal(scope.content, test_error_content);

         //simulate calling ok() on modal window
         scope.ok();
         equal(stat, 'ok');
     });

test('resetControllerSpec', function(){
    var modal_init_data,
    fakeModal = prepareFakeModal(function(init) { modal_init_data = init; });
    
    httpbackend.expectGET('srvsweetspot/ajax/reset/').respond(200, 'test_content');
    controller('resetController', {$scope : scope, Reset : appinj.get('Reset'), $modal : fakeModal});
    httpbackend.flush();
    
    equal(scope.dump_files, 'test_content');
    
    httpbackend.expectPOST('srvsweetspot/ajax/reset/').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/reset/').respond(200);
    scope.doDump();
    httpbackend.flush();
    
    equal(modal_init_data.resolve.content(), 'DUMP_SUCCESS');

    httpbackend.expectPOST('srvsweetspot/ajax/reset/').respond(500, 'test_error');
    scope.doDump();
    httpbackend.flush();
    
    equal(modal_init_data.resolve.content(), 'test_error');
    
    httpbackend.expectDELETE('srvsweetspot/ajax/reset/').respond(200);
    httpbackend.expectGET('srvsweetspot/ajax/reset/').respond(200);
    scope.doDelete();
    httpbackend.flush();

    httpbackend.expectDELETE('srvsweetspot/ajax/reset/').respond(500, 'error');
    scope.doDelete();
    httpbackend.flush();
    
    equal(modal_init_data.resolve.content(), 'error');
    
    httpbackend.expectPUT('srvsweetspot/ajax/reset/').respond(200);
    scope.doReset();

    equal(modal_init_data.resolve.content(), 'DUMP_WARNING');
    scope.errwin.resolve();
    httpbackend.flush();
    
    equal(modal_init_data.resolve.content(), 'RESTORE_SUCCESS');

    httpbackend.expectPUT('srvsweetspot/ajax/reset/').respond(500, 'test_error');
    scope.doReset();
    scope.errwin.resolve();
    httpbackend.flush();
    
    equal(modal_init_data.resolve.content(), 'test_error');
});

test('navbarControllerSpec', function()
    {
        expect(6);

        var fakeModal = prepareFakeModal();

        httpbackend.expectGET('lang/pl/main.json').respond(500, []);
        controller('navbarController', {$scope : scope, $modal : fakeModal, $translate : appinj.get('$translate'),
                                  User : userService, $location : appinj.get('$location')});

        //initial language array should not be empty
        ok(scope.langs.length > 0);

        //open login window...
        scope.loginWindow();
        ok(angular.isObject(scope.loginwind));
        //and close it, as it was server response
        scope.loginwind.close({'username' : test_username});

        //successfull window closing should cause setting scope.username and scope.logged
        equal(scope.user_data.username, test_username);
        ok(scope.logged);

        //simulate failed logout
        httpbackend.expectPOST('srvsweetspot/ajax/users/logout/').respond(500);
        scope.logout();
        httpbackend.flush();
        //should be still logged
        ok(scope.logged);

        //simulate correct logout
        httpbackend.expectPOST('srvsweetspot/ajax/users/logout/').respond(200);
        scope.logout();
        httpbackend.flush();
        //no longer logged in
        ok(!scope.logged);
});

//function for sysinfoController creation
function createSysinfoController(scope) {
    controller('sysinfoController', {
        $scope : scope,
        $timeout : appinj.get('$timeout'),
        Boreholes : appinj.get('Boreholes'),
        Sysinfo : appinj.get('Sysinfo'),
        $translate : translate,
        $translatePartialLoader : appinj.get('$translatePartialLoader')
    });
};

test('logControllerSpec', function(){
	httpbackend.expectGET('srvsweetspot/ajax/log/100').respond(200, 'test_logs');
	controller('logController', {$scope : scope, Sysinfo : appinj.get('Sysinfo')});
	scope.$apply();
	httpbackend.flush();
	
	equal(scope.line_num, 100);
	equal(scope.logs, 'test_logs');
});

test('sysinfoControllerSpec_getCurrent', function() {
    //test current data
    var test_current_data = {'boreholes_version' : -1, 'paramsVer' : 1, 'time' : '2014-04-19 21:53:46'},
    flag = false;

    translate.use('en');
    createSysinfoController(scope);
    scope.$apply();

    ok(angular.isUndefined(scope.depth_range['max']));
    
    scope.filters.mon = false;
    var temp = scope.prepareFilters();
    equal(temp['start_depth'], 0);

    scope.version = {borehole_max_height : 5000};
    scope.$apply();
    equal(scope.depth_range.max, 5000);

    temp = scope.prepareFilters();
    equal(temp['start_depth'], 0);
    equal(temp['stop_depth'], 5000);
    
    scope.filters.mon = true;
    scope.filters.meanings.push({'id' : test_bh_name});

    temp = scope.prepareFilters();
    equal(temp.start_depth, 0);
    equal(temp.stop_depth, 5000);
    deepEqual(temp.filter, [test_bh_name]);
    
    scope.filters.meanings = [];
    temp = scope.prepareFilters('TABLE');
    equal(temp.type, 'TABLE');
    equal(temp.start_depth, 0);
    equal(temp.stop_depth, 5000);
    deepEqual(temp.filter, [0]);
    
    scope.filters.meanings.push({'id' : test_bh_name}, {'id' : test_bh_name + '1'});
    temp = scope.prepareFilters();
    equal(temp.start_depth, 0);
    equal(temp.stop_depth, 5000);
    deepEqual(temp.filter, [test_bh_name, test_bh_name + '1']);

    scope.filters.meanings = [{'id' : test_bh_name + '1'}];
    temp = scope.prepareFilters()
    equal(temp.start_depth, 0);
    equal(temp.stop_depth, 5000);
    deepEqual(temp.filter, [test_bh_name + '1']);
    
    scope.filters.mon = false;
    scope.filters.son = true;
    temp = scope.prepareFilters();
    deepEqual(temp.strat, [0]);

    scope.filters.stratigraphy.push({id : 5});
    
    temp = scope.prepareFilters();
    deepEqual(temp.strat, [5]);

    scope.filters.meanings = [{'id' : test_bh_name + '1'}, {'id' : test_bh_name}];
    scope.filters.on = false;
    ok(angular.isUndefined, scope.prepareFilters()['filter']);
    
    temp = scope.prepareQuery(undefined, {'a' : 5, 'b' : 6})
    equal(temp.a, 5);
    equal(temp.b, 6);
    equal(temp.query.start_depth, 0);
    equal(temp.query.stop_depth, 5000);
    

    //initially the server activity icon should be red
    equal(scope.status_icon, 'rdot');

    //simulate server response
    httpbackend.expectGET('srvsweetspot/ajax/current/get/').respond(200, test_current_data);
    scope.getCurrent();
    httpbackend.flush();

    //the icon should be green now
    equal(scope.status_icon, 'gdot')
    //and current data should match the one from server
    deepEqual(scope.current, test_current_data);
    ok(scope.client_ver.length > 0);

    //simulate OUTDATED event - boreholes_version received from server does not match the one in browser
    var unregister = scope.$on('OUTDATED', function()
        {
            flag = true;
        });

    test_current_data['versions'] = {'boreholes' : 3, 'params' : 1};
    httpbackend.expectGET('srvsweetspot/ajax/current/get/').respond(200, test_current_data);
    scope.getCurrent();
    httpbackend.flush();

    //OUTDATED event should have been receiver
    ok(flag);

    //unregister event
    unregister();

    //simulate response to logged user's getCurrent
    test_current_data['username'] = test_username;
    httpbackend.expectGET('srvsweetspot/ajax/current/get/').respond(200, test_current_data);
    scope.getCurrent();
    httpbackend.flush();

    //credentials should match
    ok(scope.logged);
    equal(scope.user_data.username, test_username);

    //simulate sudden server crash
    httpbackend.expectGET('srvsweetspot/ajax/current/get/').respond(500);
    scope.getCurrent();
    httpbackend.flush();

    //icon should be changed to red
    equal(scope.status_icon, 'rdot');
});

test('sysinfoControllerSpec_getVersion', function() {
    var test_version_data = {'paramsVer' : 1, 'server' : '0.02.171',
            'database' : 'PostgreSQL 9.1.13 on x86_64-unknown-linux-gnu'};

    createSysinfoController(scope);
    equal(scope.versions.params(), 0);

    //simulate getVersion request
    httpbackend.expectGET('srvsweetspot/ajax/version/get/').respond(200, test_version_data);
    scope.getVersion();
    httpbackend.flush();

    //data received should match
    deepEqual(scope.version, test_version_data);
    
    deepEqual(scope.client_settings, {refresh_interval : 5000, equal_depths: false});
    scope.$broadcast('CLIENT_SETTINGS_CHANGED', {refresh_interval : 1000, equal_depths: true});
    deepEqual(scope.client_settings, {refresh_interval : 1000, equal_depths: true});
    
    scope.$broadcast('LOGGED_OUT');
    equal(scope.versions.params(), 0);
});

test('formDataObjectSpec', function(){
	formDataObject = appinj.get('formDataObject');
	formDataObject({'a' : 5, 'b' : 6}, function(){
		return {'Content-Type' : 5,
				'Content-Length' : 6};
	});
	expect(0);
});

test('createXHRSpec', function(){
	xhr = appinj.get('createXhr');
	promise = xhr(client_server_prefix + '/ajax/image/archive/' + test_id, {'a' : 5, 'b' : 6}, 'json');
	
	promise.then(function(){}, function(){}, function(){});
	promise.success(function(){});
	promise.error(function(){});
	promise.progress(function(){});
	expect(0);
});

test('toDegreesSpec', function(){
	filter = appinj.get('$filter');
	
	equal(filter('toDegrees')(123), "123° 0' 0\"");
	equal(filter('toDegrees')(23.5), "23° 30' 0\"");
	equal(filter('toDegrees')(13.2), "13° 12' 0\"");
	
});