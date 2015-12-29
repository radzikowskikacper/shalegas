/**
 * @file boreholes-ctrl.js
 * @brief AngularJS controllers for boreholes
 */

angular.module('boreholesControllers', [ 'ui.bootstrap', 'google-maps'])
.controller('boreholesController', ['$scope', '$location', 'Boreholes', '$modal', '$log', '$timeout',
	function($scope, $location, Boreholes, $modal, $log, $timeout){
		var initialBorehole = {
            latitude : 51.828988, 
            longitude: 20.489502
        };
		$scope.newBorehole = angular.copy(initialBorehole);
    	$scope.boreholes = [];
        $scope.additionForm = false;
        $scope.modificationForm = false;
        $scope.map_options = {
            zoom : 6 ,
            // Poland 51.828988,20.489502
            center: {latitude : 51.828988, longitude: 20.489502}
        };

		var updateBoreholes = function(data){
			$scope.boreholes = data.boreholes;
			$scope.opts = {};
			for(b in $scope.boreholes)
				$scope.opts[$scope.boreholes[b].id] = {'title' : $scope.boreholes[b].name};

            Boreholes.version = data.boreholes_version;
        };

        var fetchBoreholes = function(){
            Boreholes.get().success(updateBoreholes);
        };
                
        $scope.toggleBoreholeAdding = function(){
        	$scope.additionForm = ! $scope.additionForm; 
        	$scope.newBorehole = angular.copy(initialBorehole);
        };

        $scope.addBorehole = function(bh){
            Boreholes.add(bh).success(function(d){ 
                $scope.additionForm = false; 
                updateBoreholes(d); 
            }).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };

        $scope.deleteBorehole = function(id){
            Boreholes.remove(id).success(updateBoreholes).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };

        $scope.showDetails = function(id){
            $location.path('boreholes/' + id + '/pictures');
            $scope.$apply();
        };
        
        $scope.toggleBoreholeModification = function(id){
        	if($scope.modificationForm){
        		$scope.modificationForm = false;
        		return;
        	}
        	
        	Boreholes.get(id).success(function(data){ 
					$scope.borehole = data.boreholes; 
        			$scope.borehole_copy = angular.copy($scope.borehole);
        			$scope.modificationForm = true;
        		}
        	);
        };

    	$scope.modifyBorehole = function(bh){
    		$log.log('Modyfinig');
    		Boreholes.modify(bh)
    		.success(function(data){
    			$scope.modificationForm = false;
    			fetchBoreholes();
    		})
    		.error(function(data){
    			$scope.errorMsg = 'Error';
    			$timeout(function(){
    				$scope.errorMsg = '';
    			}, 2500);
    		});
    	};

        fetchBoreholes();
        $scope.$on('OUTDATED', fetchBoreholes);
        $scope.$on('LOGGED_IN', fetchBoreholes);
        $scope.$on('LOGGED_OUT', function(){ updateBoreholes([]); });
    }]
)
.controller('boreholeDetailsController', ['$rootScope', '$scope', '$stateParams', '$location', 'Boreholes',
	function($rS, $scope, $stateParams, $location, Boreholes){
		$scope.borehole_id = $stateParams.boreholeId;
				
		$scope.makePath = function(prefix, borehole_id, begin, end, height, width){
            if(!end)
            	return;            	

			var addr =  "/srvsweetspot/ajax/%prefix/%boreholeId/%begin-%end/%width-%height";
			return addr.replace('%prefix', prefix).replace("%boreholeId", borehole_id).
			replace("%begin", begin).replace('%width', width).replace("%end", end).replace('%height', height) + 
            '/?' + new Date().getTime();
		};
	    
	    Boreholes.get($scope.borehole_id).success(function(data){ 
	    		$scope.borehole_name = data.boreholes.name; 
	    	});

		$scope.goToList = function(){
            $location.path('boreholes');
        };
    	
    	$scope.$on('SetDepthEvent', function(event, data){
    		$scope.query.start_depth = data.begin;
    		$scope.query.stop_depth = data.end;

    		$scope.imgHeight = data.height;
    		$scope.step = data.step;
    	});
    }]
)
.controller('boreholeSimilarityController', ['$scope', 'Similarity', 'Meanings',
    function($scope, Similarity, Meanings){
	    $scope.isNan = isNaN;
	    $scope.epochs = [];
	    
	    $scope.$watch('stratigraphy_level', function(){
            if(!$scope.stratigraphy_level)
            	return;
            
    	    $scope.epochs = [];
    	    $scope.similarities = [];
	    	Meanings.get($scope.stratigraphy_level).success(function(data){
	    		$scope.dictvals = data.dictvals;
	    	});
	    });
	    
	    Meanings.getByType('STRAT').success(function(data){
	    	$scope.stratigraphy = data;
	    });

	    $scope.toggleEpoch = function(id){
	    	var index;
	    	if((index = $scope.epochs.indexOf(id)) > -1)
	    		$scope.epochs.splice(index, 1);
	    	else
	    		$scope.epochs.push(id);
	    };
	    
	    $scope.$watchCollection(function() { return [$scope.epochs.length, $scope.filters.mon, $scope.filters.meanings.length]; }, 
	    	function(){
	            if(!$scope.epochs.length){
	        	    $scope.similarities = [];
	            	return;
	            }

	            var filters = $scope.prepareFilters();
	            filters['stratigraphy_level'] = $scope.stratigraphy_level;
	            filters['epochs'] = $scope.epochs;
	            
	            Similarity.get($scope.borehole_id, filters).success(function(data){
	            	$scope.similarities = data;
	            });
	        }                          
	    );
	}]
)
.directive('ssStratigraphyFilter', function(){
	return {
		scope : {
			filters : '='
			
		},
		restrict : 'E',
		templateUrl : 'partials/stratigraphy_filter.html',
		controller : ['$scope', 'Meanings', 
		    function($scope, Meanings){
			    $scope.toggleFilterStratigraphy = function(name){
			        for(var m in $scope.filters.stratigraphy)
			        	if($scope.filters.stratigraphy[m].id == name.id){
			        		$scope.filters.stratigraphy.splice(m, 1);
			        		return;
			        	}
			        $scope.filters.stratigraphy.push(name);
			    };
		    
			    $scope.epochSelected = function(dict){
		    		for(var i in $scope.filters.stratigraphy)
		    			if($scope.filters.stratigraphy[i].dict_id == dict.id)
		    				return true;
		    		return false;
		    	};
		    	
		    	$scope.toggleEpoch = function(name){
		    		var brk = false;
		    		
		    		for(var m in name.dictvals)
		        		for(var i in $scope.filters.stratigraphy)
		        			if($scope.filters.stratigraphy[i].id == name.dictvals[m].id){
		        				brk = true;
		        				$scope.filters.stratigraphy.splice(i, 1);
		        			}
		    		
		    		if(brk)
		    			return;
		    		
		    		for(var m in name.dictvals)
		    			$scope.toggleFilterStratigraphy(name.dictvals[m]);
		    	};
		    	
			    Meanings.getByType('STRAT').success(function(data){
			    	$scope.dicts = [];
			    	for(d in data)
			    		Meanings.get(data[d].id).success((function(local_i){
							return function(data2){
								$scope.dicts.push(data2);
							};
			    		})(d));
			    });
			}]
	};
})
.directive('ssMeaningFilter', function(){
	return {
		scope : {
			filters : '='
		},
		restrict : 'E',
		templateUrl : 'partials/meaning_filter.html',
		controller : ['$scope', '$window', 'Meanings', 
		    function($scope, $window, Meanings){
			    $scope.toggleFilterMeaning = function(name){
			        for(var m in $scope.filters.meanings)
			        	if($scope.filters.meanings[m].id == name.id){
			        		$scope.filters.meanings.splice(m, 1);
			        		return;
			        	}
			        $scope.filters.meanings.push(name);
			    };
		    
			    $scope.sectionSelected = function(name){
		    		for(var i in $scope.filters.meanings)
		    			if($scope.filters.meanings[i].section == name.name)
		    				return true;
		    		return false;
		    	};
		    	
		    	$scope.toggleSection = function(name){
		    		var brk = false;
		    		
		    		for(var m in name.meanings)
		        		for(var i in $scope.filters.meanings)
		        			if($scope.filters.meanings[i].id == name.meanings[m].id){
		        				brk = true;
		        				$scope.filters.meanings.splice(i, 1);
		        			}
		    		
		    		if(brk)
		    			return;
		    		
		    		for(var m in name.meanings)
		    			$scope.toggleFilterMeaning(name.meanings[m]);
		    	};
		    	
			    Meanings.get().success(function(data){
			    	$scope.sections = data;
			    });
			}]
	};
})
.directive('ssBoreholeForm', function(){
    return {
        restrict: 'A',
        scope: {
            bh: '=',
            readOnlyMode: '=?'
        },
        templateUrl: 'partials/forms/borehole-mod.html',
        controller: ['$scope', '$attrs', function(scope, attrs){
            scope.map = attrs.map_options || {};
            if(scope.map.zoom === undefined) {
                scope.map.zoom = 10;
            }
            if(scope.map.center === undefined) {
                scope.map.center = angular.copy(scope.bh);
                scope.$watch('bh', function() { scope.map.center = angular.copy(scope.bh); });
            }

            scope.mapClick = function(map, eventName, mouseEv) {
                if(scope.readOnlyMode) return;

                var p = mouseEv[0].latLng;
                scope.bh.latitude = p.lat();
                scope.bh.longitude = p.lng();
                scope.$apply();
            };
        }]
    };
})
.directive('ssDepthControl', function(){
	return {
		scope : {
			init : '='
		},
		restrict : 'E',
		templateUrl : 'partials/depth_control.html',
		controller : ['$scope', '$window', function($scope, $window){	
			console.log('enter');
			$scope.Math = Math;
			$scope.max_per_page = Math.floor($window.innerHeight / 40);
			$scope.first = 0;
			$scope.step_index = $scope.init.rounds.length - 1;
			
			var emitRefreshSignal = function(begin, end, height){
				$scope.$emit('SetDepthEvent', {'begin' : begin, 'end' : end, 'height' : height, 'step' : $scope.step});
			};
			
			var refreshControl = function(){
				$scope.step = $scope.init.rounds[$scope.step_index];
				$scope.btn_num = Math.min($scope.max_per_page, Math.ceil(($scope.init.max - $scope.first) / $scope.step));

				if($scope.btn_num < $scope.max_per_page){
					$scope.first = Math.max(0, $scope.init.max - $scope.max_per_page * $scope.step);
					$scope.btn_num = Math.min($scope.max_per_page, Math.ceil(($scope.init.max - $scope.first) / $scope.step));
				}
				console.log('emit');
				emitRefreshSignal($scope.first, Math.min($scope.first + $scope.btn_num * $scope.step, $scope.init.max), $scope.btn_num * 34);
			};
			
			$scope.$watch('init.max', refreshControl);
			refreshControl();
			
			$scope.$on('ClickDepthButton', function(event, data){
				if($scope.step_index){
					$scope.first = data.begin;
					--$scope.step_index;
					refreshControl();
				}
				else
					emitRefreshSignal(data.begin, data.begin + 1, $window.innerHeight * 0.8);
				event.stopPropagation();
			});
			
			$scope.zoomOut = function(){
				if($scope.step_index < $scope.init.rounds.length - 1){
					$scope.first -= ($scope.first % $scope.init.rounds[++$scope.step_index]);
					refreshControl();
				}
			};
			
			$scope.next = function(step){
				if($scope.first + $scope.btn_num * $scope.step < $scope.init.max){
					$scope.first += (step || $scope.max_per_page) * $scope.step;
					refreshControl();
				}
			};
			
			$scope.previous = function(step){
				if($scope.first){
					$scope.first = Math.max(0, $scope.first - (step || $scope.max_per_page) * $scope.step);
					refreshControl();
				}
			};
		}]
	};
})
.directive('depthControlButton', function(){
	return {
		scope : {
			begin : '=',
			end : '=',
		},
		restrict : 'E',
		templateUrl : 'partials/depth_control_button.html',
		controller : ['$scope', function($scope){
			$scope.setImageDepth = function(){
				var data = {
						begin : $scope.begin,
						end : $scope.end
				};
				$scope.$emit('ClickDepthButton', data);
			};
		}]
	};
})
.directive('errSrc', ['$modal', function($modal){
	return {
		link : function(scope, element, attrs){
			element.bind('error', function(){
				displayPrompt(scope, $modal, 'image_size_too_big');
			});
		}
	};
}])
.filter('cm2m', function() {
    return function(str) {
        return str / 100;
    };
});