/**
 * @file utils.js
 * @brief Common functions used in application
 */

function getCookie(name) {
    var cookieValue = null;
    if(document.cookie && document.cookie != ''){
    	var cookies = document.cookie.split(';');
    	
        for(var i = 0; i < cookies.length; i++){
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if(cookie.substring(0, name.length + 1) == (name + '=')){
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
}

// helping function to create $http object
function createHttp($http, method, url, data, content_type, transform_request){
	if(method != 'GET')
		return $http({
	        method : method,
	        url: url,
	        data : data,
	        headers : {
	            'X-CSRFToken' : getCookie('csrftoken'),
	            'Content-Type': content_type
	        },
	        transformRequest   : transform_request
	    });
	else
		return $http({
	        method : method,
	        url: url,
	        params : data,
	        headers : {
	            'X-CSRFToken' : getCookie('csrftoken'),
	            'Content-Type': content_type
	        },
	        transformRequest   : transform_request
	    });		
}

function displayPrompt($scope, $modal, content, type){
    $scope.errwin = $modal.open({
        templateUrl: 'partials/error.html',
        controller: 'promptController',
        resolve: {
            content : function() { return content; },
            type : function() { return type === undefined ? 'ERROR' : type; }
        }
    });
}

function decimal2degrees(decimal){
    var min = ((decimal - Math.floor(decimal)) * 60).toFixed(2);
    var sec = (min - Math.floor(min)) * 60;
    return _.object(['deg', 'min', 'sec'], _.map([decimal, min, sec.toFixed(2)], Math.floor));
}