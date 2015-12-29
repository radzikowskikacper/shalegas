/**
 * @file user-ctrl.js
 * @brief AngularJS controllers for user managment 
 */

angular.module('userControllers', [])
.controller('profileController', ['$scope', '$rootScope', '$modal', 'User', '$stateParams', '$location',
    function($scope, $rootScope, $modal, User, $stateParams, $location){
        $scope.uid = $stateParams.userId;
        $scope.password_data = {};
        $scope.client_settings = angular.copy($scope.client_settings);
        $scope.editPersonalMode = false;

        User.get($scope.uid).success(function(data){
            $scope.profile_data = data;
        });

        $scope.$watch('profile_data', function(){ 
            $scope.profile_data_copy = angular.copy($scope.profile_data); 
        });
        
        $scope.saveClientSettings = function(){
        	$rootScope.$broadcast('CLIENT_SETTINGS_CHANGED', $scope.client_settings);
        };

        $scope.togglePersonalModification = function(){
            $scope.editPersonalMode = ! $scope.editPersonalMode;
            $scope.profile_data_copy = angular.copy($scope.profile_data);
        };

        $scope.savePersonalModification = function(){
            var new_profile_data = _.chain($scope.profile_data_copy).pick('first_name', 'last_name', 'readwrite').extend({id: $scope.uid}).value();
            User.modify(new_profile_data).success(function(data){ 
                $scope.editPersonalMode = false;
                $scope.profile_data = data;
                $scope.profile_data_copy = angular.copy($scope.profile_data);
            }).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };

        $scope.togglePasswordModification = function(){
            $scope.editPasswordMode = !$scope.editPasswordMode;
            $scope.password_data = {};
        };

        $scope.savePasswordModification = function(){
            var new_profile_data = _.chain($scope.password_data).pick('old_password', 'new_password').extend({id: $scope.uid}).value();
            User.modify(new_profile_data).success(function(data){ 
                $scope.editPasswordMode = false;
            }).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };
        
        $scope.deleteAccount = function(){
            displayPrompt($scope, $modal, 'DELETION_PROMPT', 'PROMPT');

            $scope.errwin.result.then(function(){
                User.delete($scope.uid).success(function(){
                	$location.path('/management/users');
                });
            });
        };

        $scope.isEmpty = function(form){
            return false;
        };
	}]
)
.controller('usersController', ['$scope', 'User', '$translatePartialLoader', '$translate', '$modal', '$location',
    function($scope, User, $translatePartialLoader, $translate, $modal, $location){
	    $scope.additionForm = false;
	    $scope.newUser = {};
		
		User.get().success(function(data){
	        $scope.users = data;
	    });
	    
	    $scope.toggleUserAddition = function(){
	    	$scope.additionForm = !$scope.additionForm;
	    };
	    
	    $scope.showProfile = function(id){
	        $location.path('profile/' + id);
	    };
	    
	    $scope.addUser = function(data){
	    	User.add(data).success(function(data){
	    		$scope.users = data;
	    	    $scope.additionForm = false;
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
	}]
)
.controller('loginController', ['$scope', '$rootScope', '$modalInstance', 'User', '$modal',
    function($scope, $rootScope, $modalInstance, User, $modal){
        $scope.creds = {
        	login: '',
        	password: ''
        };

        $scope.ok = function(){
        	User.login($scope.creds).success(function(data){
        		$modalInstance.close(data);
            }).error(function(e){
                displayPrompt($scope, $modal, e);
                $modalInstance.dismiss(e);
            });
        };

        $scope.cancel = function(){
            $modalInstance.dismiss('cancel');
        };
	}]
)
.directive('ssUserModifyForm', function(){
    return {
        scope: {
            user: '=',
            readOnlyMode: '=?'
        },
        templateUrl : 'partials/forms/personal-data.html'
    };
})
.directive('ssPasswordModifyForm', function(){
    return {
        scope : {
            user: '='
        },
        templateUrl : 'partials/forms/password-mod.html',
    };
})
.directive('equal', ['$parse', function($parse){
    return {
        require: 'ngModel',
        link: function(scope, el, attrs, ngModel){
            var setValidity = function(val1, val2) {
                ngModel.$setValidity('equal', val1 == val2);
            }
            ngModel.$parsers.unshift(function(viewValue) {
                var pass = $parse(attrs.equal)(scope)
                setValidity(viewValue, pass);
                return viewValue;
            });
            scope.$watch(attrs.equal, function(pass) {
                if(ngModel.$pristine) return;
                setValidity(ngModel.$viewValue, pass);
            });
        }
    };
}])
.directive('notEqual', ['$parse', function($parse){
    return {
        require: 'ngModel',
        link: function(scope, el, attrs, ngModel){
            var setValidity = function(val1, val2) {
                ngModel.$setValidity('notEqual', val1 != val2);
            }
            ngModel.$parsers.unshift(function(viewValue){
                var pass = $parse(attrs.notEqual)(scope)
                setValidity(viewValue, pass);
                return viewValue;
            });
            scope.$watch(attrs.notEqual, function(pass){
                if(ngModel.$pristine) return;
                setValidity(ngModel.$viewValue, pass);
            });
        }
    };
}])
.directive('ssUserForm', function(){
    return {
        restrict: 'A',
        scope: {
            user: '=',
        },
        templateUrl: 'partials/forms/user-add.html'
    };
});