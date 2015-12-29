/**
 * @file meanings-srv.js
 * @brief AngularJS services for meanings and sections
 */ 

angular.module('meaningsServices', ['ngResource'])
.service('Meanings', ['$http',
    function($http){
		this.url = client_server_prefix + '/ajax/meanings/';
		
		this.add = function(data){
			return createHttp($http, 'POST', this.url, JSON.stringify(data), 'application/json');
		};
		
		this.modify = function(data){
			return createHttp($http, 'PUT', this.url + data.id + '/', JSON.stringify(data), 'application/json');
		};
		
		this.remove = function(id){
			return createHttp($http, 'DELETE', this.url + id + '/', null, 'application/json');
		};
		
		this.get = function(id){
			return createHttp($http, 'GET', id ? (this.url + id + '/') : this.url);
		};
		
		this.getByType = function(type){
			return createHttp($http, 'GET', this.url, {'filter' : type});
		}
	}]
)
.service('Sections', ['$http',
    function($http){
		this.url = client_server_prefix + '/ajax/meanings/sections/';
		
		this.add = function(data) {
			return createHttp($http, 'POST', this.url, JSON.stringify(data), 'application/json');
		};
		
		this.modify = function(old_name, data) {
			return createHttp($http, 'PUT', this.url + old_name + '/', JSON.stringify(data), 'application/json');
		};
		
		this.remove = function(id) {
			return createHttp($http, 'DELETE', this.url + id + '/', null, 'application/json');
		};
		
		this.get = function(id) {
			return createHttp($http, 'GET', id ? (this.url + id + '/') : this.url);
		};
	}]
);