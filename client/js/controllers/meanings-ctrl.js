/**
 * @file meanings-ctrl.js
 * @brief AngularJS controllers for meanings and sections
 */ 

angular.module('meaningsControllers', [])
.controller('meaningsController', ['$scope', 'Meanings', '$translatePartialLoader', '$translate', '$modal', '$location', 
    function($scope, Meanings, $translatePartialLoader, $translate, $modal, $location){
    	$translatePartialLoader.addPart('meanings');
        $translate.refresh();
                               		
        var fetchMeanings = function(){
        	Meanings.get().success(function(data){
        		$scope.meanings = data;	    		
        	});
        };
        fetchMeanings();
                               	    
        $scope.toggleAddition = function(){
            $scope.additionForm = !$scope.additionForm;
            $scope.newMeaning = {unit : '', dictvals : []};
        }
                               	    
        $scope.showMeaning = function(id){
            $location.path('management/meanings/' + id);
        }
                               	    
        $scope.addMeaning = function(mn){
            for(var i in mn.dictvals)
                mn.dictvals[i] = mn.dictvals[i].value || mn.dictvals[i];

            Meanings.add(mn).success(function(data){
                $scope.meanings = data;
                $scope.additionForm = false; 
            }).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };
                                       
        $scope.deleteMeaning = function(id){
            Meanings.remove(id).success(function(data){
                $scope.meanings = data;
            }).error(function(e){
                displayPrompt($scope, $modal, e);
            });
        };
                               	    
        $scope.$on('LOGGED_IN', fetchMeanings);
    }]
)
.controller('meaningDetailsController', ['$scope', 'Meanings', '$stateParams','$translatePartialLoader', '$translate', '$modal', '$location',
    function($scope, Meanings, $stateParams, $translatePartialLoader, $translate, $modal, $location){
		$translatePartialLoader.addPart('meanings');
		$translate.refresh();
	
		Meanings.get($stateParams.meaningId).success(function(data){ 
			$scope.meaning = data; 
			console.log(data);
		});
			
		$scope.toggleMeaningEdit = function(){
	        $scope.editMode = !$scope.editMode;
	    };
		
	    $scope.modifyMeaning = function(data){    	
	    	for(var i in data.dictvals)
				data.dictvals[i] = data.dictvals[i].value || data.dictvals[i];
	    	
	    	data.unit = data.unit || '';
	    	Meanings.modify(data).success(function(){
	    		$location.path('management/meanings');
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
		};
	}]
)
.controller('sectionsController', ['$scope', 'Sections', '$translatePartialLoader', '$translate', '$modal', '$location',
    function($scope, Sections, $translatePartialLoader, $translate, $modal, $location){
        $translatePartialLoader.addPart('meanings');
        $translate.refresh();
                               		
    	$scope.newSection = {};
                               		
       	var fetchSections = function(){
       		Sections.get().success(function(data){
       			$scope.sections = data;
       		});
       	};
       	fetchSections();
                               		
       	$scope.toggleAddition = function(){
          	$scope.additionForm = !$scope.additionForm;
       	};
                               	    
        $scope.showSection = function(id){
         	$location.path('management/sections/' + id);
        };
                               	    
       	$scope.deleteSection = function(id){
           	Sections.remove(id).success(function(data){
               	$scope.sections = data;
           	}).error(function(e){
               	displayPrompt($scope, $modal, e);
           	});
       	};
                               		
      	$scope.addSection = function(sect){
         	Sections.add(sect).success(function(data){
              	$scope.sections = data;
                $scope.additionForm = false; 
            }).error(function(e){
              	displayPrompt($scope, $modal, e);
          	});
      	};
                               	    
      	$scope.$on('LOGGED_IN', fetchSections);
    }]
)
.controller('sectionDetailsController', ['$scope', 'Sections', '$stateParams','$translatePartialLoader', '$translate', '$modal', '$location',
  	function($scope, Sections, $stateParams,$translatePartialLoader, $translate, $modal, $location){
      	$translatePartialLoader.addPart('meanings');
       	$translate.refresh();
                               	
      	$scope.name = {name : $scope.old = $stateParams.sectionId};
                               	
     	$scope.editMode = false;
                               		
       	$scope.toggleSectionEdit = function(){
            if(!$scope.editMode){
                displayPrompt($scope, $modal, 'TRANSLATION_WARNING', 'PROMPT');
                               				
                $scope.errwin.result.then(function(){
                    $scope.editMode = !$scope.editMode;			
                });
            }
            else
                $scope.editMode = false;			
        };
                               		
       	$scope.modifySection = function(data){
         	Sections.modify($stateParams.sectionId, data).success(function(){
               	$location.path('management/sections');
         	}).error(function(e){
             	displayPrompt($scope, $modal, e);
           	});
      	};
  	}]
)
.directive('ssSectionForm', function(){
	return {
		scope : {
			old : '=',
			sec : '=',
            readOnlyMode: '=?'
		},
		templateUrl : 'partials/forms/section-mod.html'
	}
})
.directive('ssMeaningForm', function() {
    return {
        scope: {
            mn: '=',
            readOnlyMode: '=?',
            type : '=?'
        },
        templateUrl: 'partials/forms/meaning-mod.html',
        controller : ['$scope', 'Sections', 
            function($scope, Sections){
        		Sections.get().success(function(data){
        			$scope.sects = data;
        		})

        		$scope.addValue = function(val){
        			if($scope.mn.dictvals === undefined)
        				$scope.mn.dictvals = [];
        			
        			if($scope.mn.dictvals.indexOf(val) <= -1)
        				$scope.mn.dictvals.push({'value' : val});
        		};
        		
        		$scope.deleteValue = function(val){
        			if((i = $scope.mn.dictvals.indexOf(val)) > -1)
        				$scope.mn.dictvals.splice(i, 1);
        		};
        		
        		$scope.updateMeaning = function(){
        	    	if($scope.type == 'dict'){
        	    		if(!$scope.mn.dictvals)
        	    			$scope.mn.dictvals = [];
        	    	}
        	    	else if($scope.type == 'normal'){
        	    		if(!$scope.mn.unit)
        	    			$scope.mn.unit = '';
        	    	}
        	    	else if($scope.type == 'pict'){
        	    		delete $scope.mn.unit;
        	    	}
        	    	
        	    	$scope.mn.type = $scope.type;
        		};
        	}]
    };
});