/**
 * @file sysinfo-srv.js
 * @brief AngularJS services for support (version, current time, user management)
 */

angular.module('sysinfoServices', [])
.config(function($httpProvider){
	$httpProvider.interceptors.push(function($q, $window){
		return {
			'request' : function(config){
				angular.element('#request_gear').show();
				return config;
			},
			'response' : function(response){
				angular.element('#request_gear').hide();
				return response;
			},
			'responseError' : function(rejection){
				angular.element('#request_gear').hide();
				return $q.reject(rejection);
			}
		};
	});
})
.service('Sysinfo', ['$http', 
    function($http){
		this.url = client_server_prefix + '/ajax/'; //defined in version.js
	
		this.getVersion = function(){
			return createHttp($http, 'GET', this.url + 'version/get/');
		};
	
		this.getCurrent = function(){
			return createHttp($http, 'GET', this.url + 'current/get/');
		};
		
		this.getLogs = function(lines){
			return createHttp($http, 'GET', this.url + 'log/' + lines);
		};
	}]
)
.service('User', ['$http', 
    function($http){
		this.url = client_server_prefix + '/ajax/users/';
		
		this.login = function(credentials) {
			return createHttp($http, 'POST', this.url + 'login/', JSON.stringify(credentials), 'application/json' );
		};
	
		this.logout = function(){
			return createHttp($http, 'POST', this.url + 'logout/', null, 'application/json' );
		};
	
		this.modify = function(data){
			return createHttp($http, 'PUT', this.url + data.id + '/', JSON.stringify(data), 'application/json');
		};
	
		this.delete = function(id){
			return createHttp($http, 'DELETE', this.url + id + '/', null, 'application/json');
		};
	
		this.get = function(id){
			return createHttp($http, 'GET', id ? (this.url + id + '/') : this.url);
		};
		
		this.add = function(data){
			return createHttp($http, 'POST', this.url, JSON.stringify(data), 'application/json');
		};
	}]
)
.service('Reset', ['$http',
    function($http){
		this.url = client_server_prefix + '/ajax/reset/';
		
		this.showFiles = function(){
			return createHttp($http, 'GET', this.url);
		};
		
		this.dump = function(){
			return createHttp($http, 'POST', this.url);
		};
		
		this.restore = function(fname){
			return createHttp($http, 'PUT', this.url, JSON.stringify(fname), 'application/json');
		};
		
		this.delete = function(fname){
			return createHttp($http, 'DELETE', this.url, JSON.stringify(fname), 'application/json');
		};		
	}]
);