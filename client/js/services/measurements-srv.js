/**
 * @file measurements-srv.js
 * @brief AngularJS services for measurements
 */

angular.module('measurementsServices', ['ngResource'])
.service('Data', ['$http', 
    function($http){
		this.url = client_server_prefix + '/ajax/data';
		
		this.get = function(data){
			data['type'] = 'ALL_BHS';
			return createHttp($http, 'GET', this.url, data);
		};
	}]
)
.service('Tables', ['$http', 
    function($http){
		this.url = client_server_prefix + '/ajax/tables/';
		
		this.get = function(bid, data){
			//data['type'] = 'TABLE';
			return createHttp($http, 'GET', this.url + bid + '/', data);
		};
	}]
)
.service('Stratigraphy', ['$http', 
    function($http){
		this.url = client_server_prefix + '/ajax/stratigraphy/';
		
		this.get = function(bid, data){
			data['type'] = 'STRAT';
			return createHttp($http, 'GET', this.url + bid + '/', data);
		};
		
		this.add = function(bid, data){
			//data['type'] = 'STRAT';
			return createHttp($http, 'POST', this.url + bid + '/', JSON.stringify(data), 'application/json');
		};
	}]
)
.service('Charts', ['$http', 
    function($http){
		this.url = client_server_prefix + '/ajax/charts/';
		
		this.get = function(bid, data){
			return createHttp($http, 'GET', this.url + bid, data);
		};
	}]
)
.service('Measurements', ['$http',
    function($http){
		this.url = client_server_prefix + '/ajax/measurements/';
		
		this.get = function(bid, data){		
			return createHttp($http, 'GET', bid ? (this.url + bid + '/') : this.url, data);
		};
			
		this.add = function(bid, data, formDataObject){
			return createHttp($http, 'POST', this.url + bid + '/', data, formDataObject ? 'application/x-www-form-urlencoded' : 'application/json', formDataObject);
		};
		
		this.remove = function(vid, data){
			return createHttp($http, 'DELETE', this.url + vid + '/', JSON.stringify(data), 'application/json');
		};

		this.deleteByMeaning = function(borehole_id, data){
		    return createHttp($http, 'DELETE', this.url + borehole_id, JSON.stringify(data), 'application/json');
		};

		this.export = function(borehole_id, begin, end, lang, data) {
			var url = this.url + "export/%boreholeId/%begin-%end/%lang";
			url = url.replace("%boreholeId", borehole_id).replace("%begin", begin).replace("%end", end)
			.replace("%lang", lang);
			return createHttp($http, 'POST', url, JSON.stringify(data), 'application/json');
		};
	}]
)
.factory('Images', ['$resource', 'formDataObject',
    function($resource, formDataObject){
    	return $resource('srvsweetspot/ajax/image/:measurementId', undefined, {
    		'add' : {
    			method : 'POST',
    			headers : {
    				'X-CSRFToken' : getCookie('csrftoken'),
    				'Content-Type' : 'application/x-www-form-urlencoded'
    			},
    			transformRequest : formDataObject,
    			isArray : false
    		},
    		'regenerate' : {
    			method : 'PUT', 
    			headers : {
    				'X-CSRFToken' : getCookie('csrftoken')
    			}
    		},
    		'getProgress' : {
    			method : 'GET',
    			url : client_server_prefix + '/ajax/image/progress'
    		},
    		'cancelUpload' : {
    			method : 'POST',
    			headers : {
    				'X-CSRFToken' : getCookie('csrftoken'),
    				'Content-Type' : 'application/json'
    			},
    			url : client_server_prefix + '/ajax/image/cancel' 
    		},
    		'delete' : {
    			method : 'DELETE',
    			headers : {
    				'X-CSRFToken' : getCookie('csrftoken'),
    				'Content-Type' : 'application/json'
    			}
    		}
    	});
    }]
);