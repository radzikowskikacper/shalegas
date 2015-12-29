/**
 * @file info-ctrl.js
 * @brief AngularJS controllers for support, the prompt formats, languages, system info
 */ 

angular.module('infoControllers', [])
.controller('promptController', ['$scope', '$modalInstance', 'content', 'type',
    function($scope, $modalInstance, content, type){
      	$scope.content = content;
        $scope.type = type;
        $scope.ok = function(){ $modalInstance.close('ok'); };
        $scope.cancel = function() { $modalInstance.dismiss('cancel'); };
    }]
)
.controller('logController', ['$scope', 'Sysinfo',
    function($scope, Sysinfo){
		$scope.line_num = 100;
		$scope.line_num_opts = [10, 20, 30, 40, 50, 100, 200, 500];
		
		$scope.$watch('line_num', function(newval){
			Sysinfo.getLogs(newval).success(function(data){
				$scope.logs = data;
			});
		});
	}]
)
.controller('resetController', ['$scope', 'Reset', '$modal',
    function($scope, Reset, $modal){
		var refreshDumps = function(){
			Reset.showFiles().success(function(data){
				$scope.dump_files = data;
			});			
		};
		
		refreshDumps();
		
		$scope.doDump = function(){
			Reset.dump().success(function(){
				displayPrompt($scope, $modal, 'DUMP_SUCCESS', 'OK_PROMPT');
				refreshDumps();
			}).error(function(e){
				displayPrompt($scope, $modal, e);
			});
		};
		
		$scope.doReset = function(fname){
            displayPrompt($scope, $modal, 'DUMP_WARNING', 'PROMPT');
				
            $scope.errwin.result.then(function(){
    			Reset.restore(fname).success(function(){
    				displayPrompt($scope, $modal, 'RESTORE_SUCCESS', 'OK_PROMPT');
    			}).error(function(e){
    				displayPrompt($scope, $modal, e);
    			});
            });
		};
		
		$scope.doDelete = function(fname){
			Reset.delete(fname).success(function(){
				refreshDumps();
			}).error(function(e){
				displayPrompt($scope, $modal, e);
			});
		};
	}]
)
.controller('navbarController', ['$scope', '$rootScope', '$translate', '$modal', 'User', '$location',
    function($scope, $rS, $translate, $modal, User, $location){
        $scope.langs = ['en', 'pl'];
                         
        $scope.switchLanguage = function(lang){
        	$translate.use(lang);
        };
                         
        $scope.switchLanguage('pl');

        $scope.loginWindow = function(){
            $scope.loginwind = $modal.open({
            	templateUrl: 'partials/auth.html',
                controller: 'loginController',
            });

            $scope.loginwind.result.then(function(data){
                	$rS.logged = true;
                	$rS.user_data = {'username' : data.username, 'uid' : data.uid};
                	$rS.$broadcast('LOGGED_IN');
            	}, function() {});
        };

        $scope.logout = function(){
        	User.logout().success(function(){
        		$rS.logged = false;
                $rS.user_data = {};
                $rS.$broadcast('LOGGED_OUT');
                $location.path('/');
            }).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };
    }]
)
.controller('sysinfoController', ['$scope', '$rootScope', '$timeout', '$rootScope', '$log', 'Boreholes', 'Sysinfo', '$translate',
                                  '$translatePartialLoader', 
    function($scope, $rootScope, $timeout, $rootScope, $log, Boreholes, Sysinfo, $translate, $translatePartialLoader){
        $scope.status_icon = 'rdot';
        // $scope versions holds function returning data version that is currently used
        $scope.versions = {
        	'boreholes' : function(){ return Boreholes.version; },
			'params' : function(){ return 0; }
        };
        var initVersions = {
          	'boreholes' : function(){ return Boreholes.version; },
    		'params' : function(){ return 0; }
        }; 
        $scope.client_ver = client_ver_major.toString() + '.' + client_ver_minor.toString() + '.' + client_ver_compilation.toString();
        $scope.client_settings = {refresh_interval : 5000, equal_depths: false};
        
        $scope.filters = {son : false, mon : true, meanings : [], stratigraphy : []};
        $scope.sections = [];
        $scope.imgHeight = 0;
        $scope.query = {start_depth : 0};
        $scope.depth_range = { rounds : [1, 5, 10, 100, 1000]};
                         
		$translatePartialLoader.addPart('meanings');
		$translate.refresh();

		$scope.$on('CLIENT_SETTINGS_CHANGED', function(event, args){
           	$scope.client_settings = angular.copy(args);
        });
                         
        $scope.$on('LOGGED_OUT', function(){ $scope.versions = initVersions;});
                         
        $scope.getCurrent = function(){
        	var REFRESH_SUCCESS_INTERVAL = $scope.client_settings.refresh_interval; //ms
            var REFRESH_ERROR_INTERVAL = 5000; //ms

            return Sysinfo.getCurrent().success(function(data){
            	if(data.username !== undefined && data.username != ''){
            		$rootScope.logged = true;
                    $rootScope.user_data = {'username' : data.username, 'uid' : data.uid};
                }

                var outdated = false;
                angular.forEach(data.versions, function(version, app){
                	$log.info('Checking ' + app + '...');
                    outdated = outdated || ($scope.versions[app] !== undefined && ($scope.versions[app])() != version);
                });

                if(outdated)
                	$rootScope.$broadcast('OUTDATED');//DATA_EVENTS.outdated);

                $scope.current = angular.copy(data);
                $scope.status_icon = 'gdot';
                $timeout($scope.getCurrent, REFRESH_SUCCESS_INTERVAL);
            }).error(function(e){
            	$scope.status_icon = 'rdot';
                $timeout($scope.getCurrent, REFRESH_ERROR_INTERVAL); //call again if error
            });
        };

        $scope.getVersion = function(){
        	return Sysinfo.getVersion().success(function(data){
        		$scope.version = angular.copy(data);
        		$rootScope.version = angular.copy(data);
        		$scope.versions.params = function() { return $scope.version.paramsVer; };
        	});
        };

        $timeout($scope.getCurrent, 0); //start calling the getCurrent()
        $timeout($scope.getVersion, 0); //start calling the getVersion()

        $scope.$watch('version', function(){
        	if(!$scope.version || !$scope.version.borehole_max_height)
                return;

	        $scope.depth_range['max'] = $scope.version.borehole_max_height; 
	        $scope.query['stop_depth'] = $scope.depth_range.max;
        });

   	    $scope.prepareQuery = function(type, data){
   	    	var temp = {'query' : $scope.prepareFilters(type)};
   	    	for(i in data)
   	    		temp[i] = data[i];
   	    	return temp;
   	    };

    	$scope.prepareFilters = function(type){
            if($scope.filters.mon)
              	if($scope.filters.meanings.length > 0){
               		$scope.query.filter = [];
               		for(var m in $scope.filters.meanings)
              			$scope.query.filter.push($scope.filters.meanings[m].id);            		
               	}
              	else
               		$scope.query.filter = [0];
            else
              	delete $scope.query.filter;
            
            if($scope.filters.son)
            	if($scope.filters.stratigraphy.length > 0){
            		$scope.query.strat = [];
            		for(var m in $scope.filters.stratigraphy)
            			$scope.query.strat.push($scope.filters.stratigraphy[m].id);
            	}
            	else
            		$scope.query.strat = [0];
            else
            	delete $scope.query.strat;

            var temp = angular.copy($scope.query);
            if(type)
               	temp['type'] = type;

            return temp;
      	};
	}]
);