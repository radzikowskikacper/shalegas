/**
 * @file app.js
 * @brief Main module of SweetSpot client application. It contains the angular module with application and routing configuration
 */

angular.module( 'sweetspotApp',
                         ['pascalprecht.translate',
                             'boreholesServices', 'sysinfoServices', 'measurementsServices', 'meaningsServices',
                             'boreholesControllers', 'infoControllers', 'userControllers', 'meaningsControllers', 'measurementsControllers', 
                             'ui.router', 'ui.chart', 'multi-select', 'infinite-scroll'])
.config(['$stateProvider', '$urlRouterProvider', '$translateProvider', '$translatePartialLoaderProvider',
    function($stateProvider, $urlRouterProvider, $translateProvider, $translatePartialLoader){
		$urlRouterProvider.otherwise("/boreholes");
		// konfiguracja podstron
		$stateProvider.state('boreholes-state', {
				url: "/boreholes", 
				templateUrl: "partials/boreholes.html",
				controller : 'boreholesController'
			}
		)
		.state('borehole-details-state', {
			   	url: '/boreholes/:boreholeId',
			   	templateUrl: 'partials/borehole_details.html',
			   	controller: 'boreholeDetailsController'
			}
		)
		.state('borehole-details-state.charts', {
		   		url: '/charts',
			    templateUrl: 'partials/borehole_details_charts.html',
			    controller: 'boreholeChartsController'
			}
		)
		.state('borehole-details-state.measurements', {
		    	url: '/measurements',
			   	templateUrl: 'partials/borehole_details_measurements.html',
			   	controller: 'boreholeMeasurementsController'
			}
		)
		.state('borehole-details-state.pictures', {
				url: '/pictures',
			    templateUrl: 'partials/borehole_details_photos.html',
			    controller: 'boreholePhotosController'
			}
		)
		.state('borehole-details-state.similarity', {
			   	url: '/similarity',
			   	templateUrl: 'partials/borehole_details_similarity.html',
			   	controller: 'boreholeSimilarityController'
			}
		)
		.state('borehole-details-state.importexport', {
			   	url: '/importexport',
			   	templateUrl: 'partials/borehole_details_importexport.html',
			   	controller: 'boreholeImportExportController'
			}
		)
		.state('borehole-details-state.tables', {
			   	url: '/tables',
			   	templateUrl: 'partials/borehole_details_tables.html',
			   	controller: 'boreholeTablesController'
			}
		)
		.state('borehole-details-state.stratigraphy', {
				url: '/stratigraphy',
			    templateUrl: 'partials/borehole_details_stratigraphy.html',
			    controller: 'boreholeStratigraphyController'
			}
		)
		.state('data-state', {
			  	url: '/data',
			   	templateUrl: 'partials/data.html',
			   	controller: 'dataController'
			}
		)			    
		.state('profile-details-state', {
			    url: '/profile/:userId',
			    templateUrl: 'partials/profile.html',
		        controller: 'profileController'
			}
		)
		.state('management-state', {
			    url: "/management",
			    templateUrl: "partials/management.html"
			}
		)
		.state('management-state.users', {
			 	url: "/users",
			   	templateUrl : "partials/management_users.html",
				controller: 'usersController'
			}
		)
		.state('management-state.meanings', {
			  	url: "/meanings",
			   	templateUrl : "partials/management_meanings.html",
			   	controller: 'meaningsController'
			}
		)
		.state('management-state.sections', {
			  	url: "/sections",
			   	templateUrl : "partials/management_sections.html",
			   	controller: 'sectionsController'
			}
		)
		.state('management-state.logs', {
			  	url: "/logs",
			   	templateUrl : "partials/management_logs.html",
			   	controller: 'logController'
			}
		)
		.state('management-state.reset', {
			  	url: "/reset",
			   	templateUrl : "partials/management_reset.html",
			   	controller: 'resetController'
			}
		)
		.state('management-state.sections-details', {
			   	url : '/sections/:sectionId',
			   	templateUrl : 'partials/management_section_details.html',
			   	controller: 'sectionDetailsController'
			}
		)
		.state('management-state.meanings-details', {
				url: '/meanings/:meaningId',
				templateUrl : 'partials/management_meaning_details.html',
				controller: 'meaningDetailsController'
			}
		)
		.state('about-state', {
				url: "/about",
				templateUrl: "partials/about.html"
			}
		)
		.state('map-state', {
				templateUrl: "partials/map.html",
				url: '/map',
				controller: 'boreholesController'
			}
		)
		.state('help-state', {
				url: "/help",
				templateUrl : 'partials/help.html'
			}
		);
	
		// pliki z tlumaczeniami
		$translateProvider.useLoader('$translatePartialLoader', 
			{
				urlTemplate: 'lang/{lang}/{part}.json'
			}
		);
				   
		$translatePartialLoader.addPart('main');
	}
])
.directive('ssFile', 
	function($log){
    	return {
    		scope: {
    			path: '=path'
    		},
    		restrict: 'E',
    		template: '<input type="file"/>',
    		link: function(scope, el, attrs){
    				el.bind('change', function(ev){
    					var file = ev.target.files[0];
    					scope.path = file;// ? file.name : undefined;
    					$log.info('path = ' + file);
    					scope.$apply();
    				});
    		}
    	};
	}
)
.factory('formDataObject', ['$log', 
    function($log){
    	return function(data, headersGetter){
	        var fd = new FormData();
	        $log.info('Adding data');
	        angular.forEach(data, function(value, key){
	        	$log.info('key: ' + key + ', val: ' + value);
	        	fd.append(key, value);
	        });
	        var headers = headersGetter();
	        delete headers['Content-Type'];
	        return fd;
    	};
	}]
)
.factory('createXhr', ['$q', 
    function($q){
    	return function(addr, data, content_type){
    		var def = $q.defer();
    		
    		var createXhrPromise = function(promise){
    			var oldThen = promise.then;
    			promise.then  = function(succ, err, prog){
    				return createXhrPromise(oldThen(succ, err, prog));
    			};
    			
    			promise.success = function(cb){ 
    				return this.then(function(e){
    					cb(e.target.response, e.target.status, e);
    				}, null, null);
    			};
    			
    			promise.error = function(cb){ 
    				return this.then(null, function(e){
    					cb(e.target.response, e.target.status, e);
    				}, null);
    			};
            
    			promise.progress = function(cb){ 
    				return this.then(null, null, function(e){
    					var progress = -1;
	                    if (e.lengthComputable){
	                        progress = Math.round((100 * e.loaded) / e.total);
	                    }
	                    cb(e, progress);
    				});
    			};                 
    			
    			return promise;
    		};

    		var xhr = new XMLHttpRequest;

	        // Adding listeners
	        xhr.upload.addEventListener("progress", def.notify, false);
	        xhr.addEventListener("load", def.resolve, false);
	        xhr.addEventListener("error", def.reject, false);
	
	        xhr.open('POST', addr, true);
	        xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));

	        var form = new FormData();
	        angular.forEach(data, function(value, key){
	        	form.append(key, value);
	        });

	        xhr.send(form);

	        return createXhrPromise(def.promise);
    	};
	}]
)
.filter('toDegrees', function(){
    return function(str){
        degs = decimal2degrees(str);
        return ('' + degs.deg + '° ' + degs.min + "' " + degs.sec + '"');
    };
})
.directive('ssPosition', ['$log', '$parse', 
    function($log, $parse){
		return {
	        scope: true,
	        restrict: 'E',
	        require: 'ngModel',
	        replace: true,
	        templateUrl: 'partials/position.html',
	        link: function(scope, el, attrs, ctrl){
	            ctrl.$setViewValue($parse(attrs.ngModel)(scope));
	            $log.info('initilizing with ' + ctrl.$modelValue);
	            scope.degrees = decimal2degrees(ctrl.$modelValue);
	            scope.required = attrs.required;

	            scope.recalculate = function(){
	                _.each(scope.degrees, function(val, key, obj){
	                    	if(isNaN(parseFloat(val)))	
	                    		obj[key] = 0; 
	                });

	                var out = ((3600 * parseFloat(scope.degrees.deg) + 60 * parseFloat(scope.degrees.min) + parseFloat(scope.degrees.sec) + 0.5) / 3600.0).toString();
	                ctrl.$setViewValue(out);
	            };

	            ctrl.$render = function(){
	                scope.degrees = decimal2degrees(ctrl.$viewValue);
	            };
	        }
		};
	}]
)
.directive('ssAdd', function(){
    return {
        restrict: 'AE',
        transclude: true,
        replace: true,
        template: '<button type="button" class="btn btn-success btn-sm"><span class="glyphicon glyphicon-plus-sign"></span> <span ng-transclude></span></button>',
    };
})
.directive('ssRemove', function(){
    return {
        restrict: 'AE',
        transclude: true,
        replace: true,
        template: '<button type="button" class="btn btn-danger btn-sm"><span class="glyphicon glyphicon-remove-sign"></span> <span ng-transclude></span></button>',
    };
})
.directive('ssModify', function(){
    return {
        restrict: 'AE',
        transclude: true,
        replace: true,
        template: '<button type="button" class="btn btn-default btn-sm"><span class="glyphicon glyphicon-edit"></span> <span ng-transclude></span></button>',
    };
})
.directive('ssEditable', function(){
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        scope: {
            editable: '=?',
            readOnlyText: '@'
        },
        
        template: '<span style="display:inline-block;"></span>',
        link: function(scope, el, attrs, ctrl, transFn){
            if(scope.editable === undefined || scope.editable == '')
                scope.editable = false;

            scope.$watch('editable', function(){
                console.log('przemiana!');
                el.empty();
                // Zrobione, zeby transcludowane podelementy mialy scope rodzica, a nie wlasny, odizolowany
                transFn(el.scope(), function(clone){
                    if(scope.editable)
                        el.removeClass('viewable').addClass('editable').append(clone);
                    else
                        el.removeClass('editable').addClass('viewable').append(scope.readOnlyText);
                });
            });

            scope.$watch('readOnlyText', function(v) {
                if(!scope.editable) 
                    el.empty().append(v);
            });
        }
    };
})
.directive('ssDecimal', ['$parse', 
    function($parse){
		return {
			require: 'ngModel',
			link: function(scope, el, attrs, ngModel){
	            var setValidity = function(val){
	                ngModel.$setValidity('decimal', /^\d+([.]\d\d?)?$/.test(val));
	            };

	            ngModel.$parsers.unshift(function(viewValue){
	                setValidity(viewValue);
	                return viewValue;
	            });
	            
	            scope.$watch(attrs.ngModel, function(){
	                if(ngModel.$pristine) return;
	                setValidity(ngModel.$viewValue);
	            });
			}
		};
	}]
)
.directive('showTail', function(){
    return function(scope, elem, attr){
        scope.$watch(function (){
            return elem[0].value;
        },
        function (e) {
            elem[0].scrollTop = elem[0].scrollHeight;
        });
    };
})
.filter('range', function(){
	return function(input, total){
		total = parseInt(total);
		for (var i=0; i<total; i++)
			input.push(i);
		return input;
	};
});