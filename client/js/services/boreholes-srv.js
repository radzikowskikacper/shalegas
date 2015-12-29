/**
 * @file boreholes-srv.js
 * @brief AngularJS services for boreholes, asynchronous communication with server
 */

angular.module('boreholesServices', [])
.service('Boreholes', ['$http', 
    function($http){
		this.baseURL = client_server_prefix +'/ajax/boreholes/';//defined in version.js
	    this.version = -1;
	
	    this.get = function(id) {
	        url = this.baseURL;
	        if(id !== undefined) {
	            url += id + '/';
	        }
	        return $http.get(url);
	    };
	
	    this.add = function(data) {
	        return createHttp($http, 'POST', this.baseURL, JSON.stringify(data), 'application/json' );
	    };
	
	    this.modify = function(data) {
	        return createHttp($http, 'PUT', this.baseURL + data.id + '/', JSON.stringify(data), 'application/json' );
	    };
	
	    this.remove = function(id) {
	        return createHttp($http, 'DELETE', this.baseURL + id + '/', null, 'application/json');
	    };
	}]
)
.service('Similarity', ['$http', 
    function($http){
		this.baseURL = client_server_prefix +'/ajax/similarities/';
	
		this.get = function(borehole_id, data){
			return createHttp($http, 'GET', this.baseURL + borehole_id + '/', data);
		};
	}]
);