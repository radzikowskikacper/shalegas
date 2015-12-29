/**
 * @file test04_user_ctrl.js
 * @brief Unit tests for user management controllers
 */

var userCtrls = angular.injector(['ng', 'userControllers']);

var test_password = "test_password";
var test_first_name = "test_first_name";
var test_last_name = "test_last_name";

var test_name = 'test_name';
var test_section = 'test_section';
var test_unit = 'test_unit';

var meaningsService = appinj.get('Meanings');
var sectionsService = appinj.get('Sections');

module('userControllersSpec',
           {
               setup: function()
               {
                   scope = userCtrls.get('$rootScope').$new();
                   controller = userCtrls.get('$controller');
                   test_dict = {'id' : test_id, 'username' : test_username};
               },

               teardown : function()
               {
                   httpbackend.verifyNoOutstandingExpectation();
                   httpbackend.verifyNoOutstandingRequest();
               }
           });

test('profileControllerSpec', function() {
    var modal_init_data,
    modal = prepareFakeModal(function(init) { modal_init_data = init; });
    test_dict['id'] = test_id;
    test_dict['first_name'] = test_first_name;
    test_dict['last_name'] = test_last_name;
    httpbackend.expectGET('srvsweetspot/ajax/users/' + test_id + '/').respond(200, test_dict);
    controller('profileController', {User : userService, $scope : scope, $modal : modal, $stateParams : {userId : test_id},
    	$location : appinj.get('$location')});
    httpbackend.flush();
    scope.$apply();
    deepEqual(scope.profile_data, test_dict);
    deepEqual(scope.profile_data_copy, test_dict);
    ok(angular.isFunction(scope.togglePasswordModification));
    ok(angular.isFunction(scope.togglePersonalModification));

    scope.togglePasswordModification();
    ok(scope.editPasswordMode);

    // simulate bad respnse for user modification
    httpbackend.expectPUT('srvsweetspot/ajax/users/' + test_id + '/').respond(500, test_dict);
    scope.savePasswordModification();
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    ok(scope.editPasswordMode);

    scope.errwin.close();

    // simulate good respnse for user modification
    httpbackend.expectPUT('srvsweetspot/ajax/users/' + test_id + '/').respond(200, test_dict);
    scope.savePasswordModification();
    httpbackend.flush();
    ok(!scope.editPasswordMode);

    //showPersonalModification should show instance of modal dialog, resolving username, id, first and last name
    scope.togglePersonalModification();
    ok(scope.editPersonalMode);

    delete test_dict['new_password'];
    delete test_dict['old_password'];
    test_dict['first_name'] = test_first_name + '_modified';
    test_dict['last_name'] = test_last_name;
    httpbackend.expectPUT('srvsweetspot/ajax/users/' + test_id + '/').respond(500, test_dict);
    scope.savePersonalModification();
    httpbackend.flush();
    ok(angular.isObject(scope.errwin));
    ok(scope.editPersonalMode);

    scope.errwin.close();

    httpbackend.expectPUT('srvsweetspot/ajax/users/' + test_id + '/').respond(200, test_dict);
    scope.savePersonalModification();
    httpbackend.flush();
    ok(!scope.editPersonalMode);
    deepEqual(scope.profile_data, test_dict);

    //simulate deleting
    scope.deleteAccount();

    //prompt should appear
    ok(angular.isObject(scope.errwin));
    equal(modal_init_data.resolve.type(), 'PROMPT');
    equal(modal_init_data.resolve.content(), 'DELETION_PROMPT');

    httpbackend.expectDELETE('srvsweetspot/ajax/users/' + test_id + '/').respond(200);
    scope.errwin.close();
    httpbackend.flush();
    
    var triggered = 0;
    scope.$on('CLIENT_SETTINGS_CHANGED', function(event, args){
    	triggered = args;
    });

    scope.saveClientSettings();
    deepEqual(triggered, scope.client_settings);
    
    ok(!scope.isEmpty());
});

module('userControllersSpec',
        {
            setup: function()
            {
            	Sections = appinj.get('Sections');
                scope = userCtrls.get('$rootScope').$new();
                controller = userCtrls.get('$controller');
                test_dict = {'id' : test_id, 'username' : test_username};
                translatePartialLoader = appinj.get('$translatePartialLoader');
                translate = appinj.get('$translate');
            },

            teardown : function()
            {
                httpbackend.verifyNoOutstandingExpectation();
                httpbackend.verifyNoOutstandingRequest();
            }
        });

test('usersControllerSpec', function() {
    var test_users = [],
    	location = appinj.get('$location'),
    	modal_init_data,
    	modal = prepareFakeModal(function(init) { modal_init_data = init;});

    for(i = 0; i < 3; ++i)
        test_users.push({'id' : i, 'username' : test_username + i, 'first_name' : test_first_name + i, 'last_name' : test_last_name + i});

    httpbackend.expectGET('srvsweetspot/ajax/users/').respond(200, test_users);
    
    controller('usersController', {$scope : scope, User : userService, $location : location, 
    	$translatePartialLoader : translatePartialLoader, $modal : modal, $translate : translate});
    httpbackend.flush();

    ok(!scope.additionForm);
    deepEqual(scope.users, test_users);

    scope.showProfile(test_id);
    equal(location.path(), '/profile/' + test_id);
    
    scope.toggleUserAddition();
    ok(scope.additionForm);
    
    httpbackend.expectPOST('srvsweetspot/ajax/users/').respond(500, 'test_err');
    scope.addUser({login : 'login'});
    httpbackend.flush();
    ok(angular.isDefined(scope.errwin));
    equal(modal_init_data.resolve.content(), 'test_err');
    
    deepEqual(scope.users, test_users);
    httpbackend.expectPOST('srvsweetspot/ajax/users/').respond(200, 'test_cont');
    scope.addUser({login : 'login'});
    httpbackend.flush();
    equal(scope.users, 'test_cont');
});

test('loginControllerSpec', function(){
         expect(6);

         var stat, //status passed as parameter to modal.close()
         reason, //status passed as parameter to modal.dismiss()
         modal_data; //modal init data passed as parameter to modal.open()

         var fakeModal = prepareFakeModal(function(d){ modal_data=d; }, function(s){ stat=s; }, function(r){ reason=r; });

         controller('loginController', {$scope : scope, $modalInstance : fakeModal.open(), $modal : fakeModal,
                                        User : userService});

         //initial credentials should be empty
         equal(scope.creds['login'], '');
         equal(scope.creds['password'], '');

         //simulate login cancel
         scope.cancel();
         equal(reason, 'cancel');

         //incorrect login
         httpbackend.expectPOST('srvsweetspot/ajax/users/login/').respond(500, test_error_content);
         scope.ok();
         httpbackend.flush();

         //make sure error modal window appeared, and error is correctly resolved from it
         ok(angular.isObject(scope.errwin));
         deepEqual(modal_data.resolve.content(), test_error_content);

         //simulate correct login
         scope.creds = {login : test_username, password: test_password};
         httpbackend.expectPOST('srvsweetspot/ajax/users/login/', scope.creds).respond(200, {'username' : scope.creds.login});
         scope.ok();
         httpbackend.flush();

         //username received from server should match the one, that was sent
         equal(stat['username'], test_username);
     });