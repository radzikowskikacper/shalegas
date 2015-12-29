/**
 * @file measurements-ctrl.js
 * @brief AngularJS controllers for measurements, charts, import and export
 */ 

angular.module('measurementsControllers', [ 'ui.bootstrap', 'google-maps'])
.controller('dataController', ['$scope', 'Data',
   	function($scope, Data){
      	$scope.limit = 0;
       	$scope.isNaN = isNaN;

       	$scope.increaseLimit = function(){
         	$scope.limit += $scope.limit ? 5 : 30;
     	};
                           		
      	$scope.$watchCollection(function(){ return [$scope.filters.mon, $scope.filters.meanings.length,
      	                                            $scope.filters.son, $scope.filters.stratigraphy.length]; }, 
          	function(){
             	if(!$scope.query.stop_depth)
                   	return;

               	Data.get($scope.prepareFilters()).success(function(data){
                    $scope.measurements = data;
                });	    	
            }
      	);		
	}]
)
.controller('boreholeChartsController', ['$filter', '$scope', 'Charts', '$translate',
    function($filter, $scope, Charts, $translate){
		$scope.unit_pair = false;		
		$scope.limit = 0;
		
		$scope.increaseLimit = function(){
			$scope.limit += 5;
		};
		
	    var chartOptsTemplate = {
	    	axes : {
	    		xaxis : {
	    			show : true
	    		},
	    		yaxis : {
	    			show : true,
	    			labelRenderer: jQuery.jqplot.CanvasAxisLabelRenderer,
	    			tickRenderer: jQuery.jqplot.CanvasAxisTickRenderer
	    		}
	    	},
	    	legend : {
	    		show: true, 
	    		location: 's', 
	    		placement: 'outsideGrid',
	    		renderer : jQuery.jqplot.EnhancedLegendRenderer,
	    		rendererOptions : {numberRows : 4}
	    	}
	    };
	  
	    $scope.drawCharts = function(){
			if($scope.unit_pair === false){
		    	for(i in $scope.charts){
		    		var opts = angular.copy(chartOptsTemplate);		    			
		    		opts.axes.yaxis.label = $scope.charts[i].unit;
		    		opts.series = [{label : $scope.charts[i].name}];
		    		$scope.charts[i]['options'] = opts;
		    	}
			}
			else{
			    for(i in $scope.charts){
			    	var opts = angular.copy(chartOptsTemplate);
			    	opts.axes.yaxis.label = $scope.charts[i].unit;
			    	opts.series = $scope.charts[i].names;
		    	    $scope.charts[i].options = opts;
			    }
			}
	    };
	    
	    $scope.$watch(function() { return $filter('translate')('DEPTH_FROM'); },
	        function(newval) { chartOptsTemplate.axes.xaxis.label = newval; }
	    );
	    
	    $scope.printElem = function(elem)
	    {
	        html2canvas($('[chart-id="' + elem + '"]'), {
	        	allowTaint : 'true',
	        	loggind : 'on',
	        	background : '#fff',
	        	onrendered : function(canvas){
	        		window.location.href = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");	 
	        	}
	        });
	    };
	    
	    $scope.getCharts = function(){
            if(!$scope.query.stop_depth || !$translate.use())
            	return;

            var filters = $scope.prepareFilters();
            if($scope.unit_pair)
            	filters['unit_pair'] = true;
            filters['lang'] = $translate.use();
            
    		Charts.get($scope.borehole_id, filters).success(function(data){
    			$scope.charts = data;
	       		$scope.limit = 5;
	       		$scope.drawCharts();
	       		delete $scope.error;
    		}).error(function(e){
    			$scope.error = e;
    		});    	
	    };
	    
	    $scope.$watchCollection(function() { return [$scope.query.start_depth, $scope.query.stop_depth, $translate.use(),
	                                                 $scope.filters.mon, $scope.filters.meanings.length, $scope.filters.son, 
	                                                 $scope.filters.stratigraphy.length]; }, 
	    	$scope.getCharts);
	}]
)
.controller('boreholeTablesController', ['$scope', 'Tables',
    function($scope, Tables){
		$scope.limit = 0;
		$scope.isNaN = isNaN;

		$scope.increaseLimit = function(){
			$scope.limit += $scope.limit ? 5 : 30;
		};

		$scope.getTables = function(){
            if(!$scope.query.stop_depth)
            	return;

            Tables.get($scope.borehole_id, $scope.prepareFilters()).success(function(data){
            	$scope.measurements = data;
            	delete $scope.error;
			}).error(function(e){
				$scope.error = e;
			});
		};
		
	    $scope.$watchCollection(function() { return [$scope.query.start_depth, $scope.query.stop_depth,
	                                                 $scope.filters.mon, $scope.filters.meanings.length,
	                                                 $scope.filters.son, $scope.filters.stratigraphy.length]; }, 
	    	$scope.getTables);		
	}]
)
.controller('boreholeStratigraphyController', ['$scope', 'Stratigraphy', '$modal', 'Meanings',
    function($scope, Stratigraphy, $modal, Meanings){
		$scope.newDictionary = {};
		$scope.stratigraphy = {header : []};
		$scope.dicts = [];
		
		$scope.getStratigraphy = function(){
            if($scope.query.stop_depth)
            	Stratigraphy.get($scope.borehole_id, $scope.prepareFilters()).success(function(data){
            		$scope.stratigraphy = data;
            	});
		};
		
	    Meanings.getByType('STRAT').success(function(data){
	    	for(d in data)
	    		Meanings.get(data[d].id).success((function(local_i){
					return function(data2){
						$scope.dicts.push(data2);
					};
	    		})(d));
	    });
		
	    $scope.addStratigraphy = function(data){
	    	Stratigraphy.add($scope.borehole_id, $scope.prepareQuery('STRAT', data)).success(function(dat){
	    		$scope.stratigraphy = dat;
	    		$scope.newDictionary = {};
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
		
	    $scope.$watchCollection(function() { return [$scope.query.start_depth, $scope.query.stop_depth]; },
	    	$scope.getStratigraphy);		
	}]
)
.controller('boreholeImportExportController', ['$scope', 'Measurements', 'Meanings', '$modal',
    function($scope, Measurements, Meanings, $modal){
	    $scope.showCsvModal = function(borehole_id) {
	    	var modalInstance = $modal.open({
				templateUrl: 'partials/csv_modal.html',
			    controller: 'csvUploadController',
			    keyboard : false,
			    backdrop : 'static',
			    scope : $scope
			});	
	    }
	    
	    $scope.showExportModal = function() {
	    	var modalInstance = $modal.open({
	    		templateUrl: 'partials/export_modal.html',
	    		controller: 'exportController',
	    		keyboard : false,
	    		backdrop : 'static',
	    		scope : $scope
	    	});
	    }		
	}]
)
.controller('boreholeMeasurementsController', ['$scope', '$log', '$modal', 'Measurements', 'Meanings', 'Images', '$http', 'formDataObject', '$filter',
	function($scope, $log, $modal, Measurements, Meanings, Images, $http, formDataObject, $filter) {
		$scope.predicate = 'drilling_depth';
		$scope.reverse = false;
	    $scope.newValue = {};
	    $scope.newGraphics = { borehole_id : $scope.borehole_id };
		$scope.newDictionary = {};
		$scope.dictionary_measurements = [];
		$scope.real_measurements = [];
		$scope.pict_measurements = [];
		$scope.limit = 0;
		$scope.shown = [];
		$scope.real_meanings = [];
		$scope.dictionary_meanings = [];
	    $scope.pict_meanings = [];
	    
	    Meanings.getByType('PICT').success(function(data){
	    	for(d in data)
	    		$scope.pict_meanings = $scope.pict_meanings.concat(data[d].meanings);
	    });
	    
	    Meanings.getByType('NDICT').success(function(data){
	    	for(d in data)
	    		$scope.real_meanings = $scope.real_meanings.concat(data[d].meanings);
	    });
	    
	    Meanings.getByType('DICT').success(function(data){
	    	for(d in data)
	    		$scope.dictionary_meanings = $scope.dictionary_meanings.concat(data[d].meanings);
	    });

		$scope.increaseLimit = function(){
			$scope.limit += 20;
		};
		
	    $scope.deleteDictionary = function(did){
	    	Measurements.remove(did, $scope.prepareQuery('DICT', {'borehole_id' : $scope.borehole_id})).success(function(data){
	    		$scope.dictionary_measurements = data;
	            $scope.getMeasurementsImage();
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
	    
	    $scope.addDictionary = function(data){
	    	Measurements.add($scope.borehole_id, JSON.stringify($scope.prepareQuery('DICT', data))).success(function(data){
	    		$scope.dictionary_measurements = data;
	    		$scope.newDictionary = {};
	            $scope.getMeasurementsImage();
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
	    	    
	    $scope.addGraphics = function(data){
	    		var filters = $scope.prepareFilters('PICT');
	    		for(i in data)
	    			filters[i] = data[i];

                Measurements.add($scope.borehole_id, filters, formDataObject).success(function(d){
	            	$scope.pict_measurements = d;
	        	    $scope.newGraphics = {
	        	            borehole_id : $scope.borehole_id,};
	            	$scope.getMeasurementsImage();
                }).error(function(rdata, st) {
	                if(st == 530) { // size error
	                    size = rdata.toString().split(' ');
	                    displayPrompt($scope, $modal, $filter('translate')('Wrong size, should be {width}x{height}').replace('{width}', size[0]).replace('{height}', size[1]));
	                } else {
	                    displayPrompt($scope, $modal, $filter('translate')(rdata));
	                }
	                $log.error(st + ': Cannot add new entry');
	            });
	    };
	    
	    $scope.deleteGraphics = function(id){
	    	Measurements.remove(id, $scope.prepareQuery('PICT', {'borehole_id' : $scope.borehole_id})).success(function(data){
	    		$scope.pict_measurements = data;
	            $scope.getMeasurementsImage();
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
	   
	    $scope.deleteValue = function(vid){
	    	Measurements.remove(vid, $scope.prepareQuery('NDICT', {'borehole_id' : $scope.borehole_id})).success(function(data){
	    		$scope.real_measurements = data;
	            $scope.getMeasurementsImage();
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
	   
	    $scope.addValue = function(data){
	    	Measurements.add($scope.borehole_id, JSON.stringify($scope.prepareQuery('NDICT', data))).success(function(data){
	    		$scope.real_measurements = data;
	            $scope.newValue = {};
	            $scope.getMeasurementsImage();
	    	}).error(function(e){
	    		displayPrompt($scope, $modal, e);
	    	});
	    };
	    
	    $scope.getMeasurementsImage = function(){
            $scope.path = $scope.makePath('measurements/intervals', $scope.borehole_id, $scope.query.start_depth, 
            		$scope.query.stop_depth, $scope.imgHeight, 100);
            
            if($scope.path && (filter = $scope.prepareFilters().filter))
            	for(f in filter)
            		$scope.path += '&filter=' + filter[f];
	    };
	    
	    $scope.$watchCollection(function() { return [$scope.query.start_depth, $scope.query.stop_depth,
	                                                 $scope.filters.mon, $scope.filters.meanings.length,
	                                                 $scope.filters.son, $scope.filters.stratigraphy.length,
	                                                 $scope.imgHeight]; },
	        function(){
	          	if(!$scope.query.stop_depth || !$scope.imgHeight)
	          		return;

	            $scope.getMeasurementsImage();
	            
	            Measurements.get($scope.borehole_id, $scope.prepareFilters('NDICT')).success(function(data){
	            	$scope.real_measurements = data;
	              	$scope.limit = 20;
	              	delete $scope.rerror;
	            }).error(function(e){
	            	$scope.rerror = e;
	            });
	                                            		
	           	Measurements.get($scope.borehole_id, $scope.prepareFilters('DICT')).success(function(data){
	              	$scope.dictionary_measurements = data;
	              	delete $scope.derror;
	           	}).error(function(e){
	           		$scope.derror = e;
	           	});

	          	Measurements.get($scope.borehole_id, $scope.prepareFilters('PICT')).success(function(data){
	              	$scope.pict_measurements = data;
	              	delete $scope.gerror;
	           	}).error(function(e){
	           		$scope.gerror = e;
	           	});
	        }
	    );
	    
	    $scope.$watch('newDictionary.meaning', function(){
	    	if(!$scope.newDictionary.meaning)
	    		return;
	    	
	    	Meanings.get($scope.newDictionary.meaning).success(function(data){
	    		$scope.dictvals = data;
	    	});
	    });

	    $scope.$watch('newValue.meaning', function(){
	    	if(!$scope.newValue.meaning)
	    		return;
	    	
	    	Meanings.get($scope.newValue.meaning).success(function(data){
	    		$scope.valueUnit = data.unit;
	    	});
	    });

	    $scope.$watch('newGraphics.meaning', function(){
	    	if(!$scope.newGraphics.meaning)
	    		return;

	    	Meanings.get($scope.newGraphics.meaning).success(function(data){
	    		$scope.graphicsUnit = data.unit;
	    	});
	    });
	    
	    $scope.shownId = function(id){
	    	return $scope.shown.indexOf(id) != -1;
	    };
	    
	    $scope.toggleShow = function(id){
	    	index = $scope.shown.indexOf(id);
	    	if(index > -1)
	    		$scope.shown.splice(index, 1);
	    	else
	    		$scope.shown.push(id);
	    };
	    
	    $scope.isInvalid = function(form) {
	        return form.$invalid;
	    };
	}]
)
.controller('csvUploadController', ['$translate', '$scope', '$filter', '$modalInstance', 'createXhr', '$modal', 'Meanings', 
    function($translate, $scope, $filter, $modalInstance, createXhr, $modal, Meanings){
		$scope.modalData = {'column' : 1};
		$scope.sections = [];
		
	    Meanings.get().success(function(data){
	    	for(d in data)
	    		$scope.sections = $scope.sections.concat(data[d].meanings);
	    });
	    
		$scope.ok = function(){
			var url = client_server_prefix + '/ajax/measurements/archive/' + $scope.borehole_id + '/' + $scope.modalData.column
			 + '/' + $scope.modalData.meaning.id + '/' + $translate.use();
			
			return createXhr(url, {archive: $scope.archive.path, lang : $translate.use()}, undefined)
			.success(function(data, status) {
				$modalInstance.close();
				if (status == 200) {
					var response = JSON.parse(data);
					
					displayPrompt($scope, $modal, $filter('translate')("values_add").concat(response.rows), 'OK_PROMPT');				
				} else {
					displayPrompt($scope, $modal, $filter('translate')(data));	
				}
			})
		};
		
		$scope.cancel = function(){
			$modalInstance.close();
		}
	}]
)
.controller('exportController', ['$scope', '$filter', '$modalInstance', '$modal', 'Meanings', '$translate', 'Measurements', 
    function($scope, $filter, $modalInstance, $modal, Meanings, $translate, Measurements) {
		$scope.chooseLabel = $filter('translate')('CHOOSE_LABEL');
		$scope.exportData = {};

		Meanings.get().success(function(data){
	    	$scope.meanings = [];
	    	
	    	data.forEach(function(section){
	    		var beginSectionEntry = {};
	    		beginSectionEntry.name = $filter('translate')(section.name);
	    		beginSectionEntry.groupMarker = true;
	    		$scope.meanings = $scope.meanings.concat(beginSectionEntry);
	    		
	    		section.meanings.forEach(function(m){
	    			m.name = $filter('translate')(m.name);
	    			$scope.meanings = $scope.meanings.concat(m);
	    		});
	    		
	    		var endSectionEntry = {}
	    		endSectionEntry.groupMarker = false
	    		$scope.meanings = $scope.meanings.concat(endSectionEntry);
	    	});
	    });
		
		var downloadURL = function downloadURL(url){
			var hiddenIFrameID = 'hiddenDownloader',
			iframe = document.getElementById(hiddenIFrameID);
			if (iframe === null){
				iframe = document.createElement('iframe');
				iframe.id = hiddenIFrameID;
				iframe.style.display = 'none';
				document.body.appendChild(iframe);
			}
			iframe.src = url;
		};
		
		$scope.cancel = function(){
			$modalInstance.close();
		};
		
		$scope.ok = function(){
			
			if ($scope.exportData.begin == undefined || $scope.exportData.end == undefined)
				return;
			
			var ticked = [];
			angular.forEach($scope.meanings, function(value, key){
			    if (value.ticked === true)
			        ticked = ticked.concat(value.id)
			})
			
			Measurements.export($scope.borehole_id ,$scope.exportData.begin, $scope.exportData.end, $translate.use(), ticked)
			.success(function(data){
				$modalInstance.close();
				downloadURL(client_server_prefix + "/ajax/measurements/download/" + data.filename);
			})
			.error(function(e){
				$modalInstance.close();
				displayPrompt($scope, $modal, $filter('translate')(e));
			});
		};
	}]
)
.controller('boreholePhotosController', ['$modal', '$filter', '$scope', '$log', '$http', 'formDataObject', 'createXhr', 'Images', 'Sysinfo',
    function($modal, $filter, $scope, $log, $http, formDataObject, createXhr, Images, sysinfo){
		$scope.new_entry = {
            borehole_id : $scope.borehole_id,
            image_path : ''
        };
		$scope.params = {};
		$scope.limit = 0;
		
	    $scope.getBoreholeImage = function(){
	    	if($scope.imgHeight)
	    		$scope.path = $scope.makePath('borehole_image', $scope.borehole_id, $scope.query.start_depth, $scope.query.stop_depth, $scope.imgHeight, 100);
	    };
	    
        $scope.addEntry = function(data){
        	displayPrompt($scope, $modal, 'HELPER_UPDATE_WARNING', 'WARNING');
        	
        	$scope.errwin.result.then(function(){
                $log.log('Adding entry...');

                Images.add(data, function(){
    	            $scope.getPictures();
    	            $scope.getBoreholeImage();
                }, function(rdata){
	                if(rdata.status == 415) {
	    	            $scope.getPictures();
	    	            $scope.getBoreholeImage();
	                    displayPrompt($scope, $modal, 'UNOPTIMAL_PHOTO_SIZE', 'WARNING');
	                } else {
	                    displayPrompt($scope, $modal, rdata);
		                $log.error(rdata.status + ': Cannot add new entry');
	                }
                });
        	});
        };

        $scope.removeEntry = function(entry_id){
        	displayPrompt($scope, $modal, 'HELPER_UPDATE_WARNING', 'WARNING');
        	
        	$scope.errwin.result.then(function(){
        		Images.delete({measurementId : entry_id}, function(){
	            	$log.info('Removed...');
	            	$scope.getPictures();
	            	$scope.getBoreholeImage();
        		});
        	});
        };
   
	    $scope.$watchCollection(function(){ return [$scope.query.start_depth, $scope.query.stop_depth, $scope.imgHeight]; }, 
		    function(){
	            if($scope.query.start_depth + 1 != $scope.query.stop_depth){
		            $scope.getBoreholeImage();
		            $scope.getPictures();	 
	            }
	            else
	                $scope.getFullImage(false);
	        });
		
		$scope.increaseLimit = function(){
			$scope.limit += 10;
		};
				
        $scope.sendArchive = function(borehole_id, path){
            $log.info('Sending archive ' + path + '...');
            $scope.progress = 0;
            return createXhr(client_server_prefix + '/ajax/image/archive/' + borehole_id, {archive: path}, undefined)
            	.success(function(){
            		delete $scope.progress;
		        	var modalInstance = $modal.open({
						templateUrl: 'partials/modal.html',
					    controller: 'modalController',
					    keyboard : false,
					    backdrop : 'static'
					});
        	
		        	modalInstance.result.then(function(data) {
		        		if (data == "ok"){
		        			$scope.getPictures();
		        			$scope.getBoreholeImage();
		        		}
		        		else
		        			displayPrompt($scope, $modal, $filter('translate')(data));
		        	});
            	})
	            .error(function(){
	            	(displayPrompt($scope, $modal, $filter('translate')('Archive upload error')));
	            })
	            .progress(function(e, p) {
	                $log.info('Progress: ' + p + '%');
	                if ('progress' in $scope)
	                	$scope.progress = p;
	            });
	    };

	    $scope.getPictures = function(){
	    	if(!$scope.query.stop_depth)
	    		return;
	    	
	    	$scope.limit = 10;
	        $scope.measurements = Images.query({borehole_id: $scope.borehole_id, start_depth : $scope.query.start_depth, 
	        	stop_depth : $scope.query.stop_depth});
	    };
	    
	    $scope.regenerateHelperPhotos = function(){
	    	Images.regenerate({borehole_id : $scope.borehole_id}, function(){
	    	 	$scope.modalInstance = $modal.open({
					templateUrl: 'partials/modal.html',
				    controller: 'modalController',
				    keyboard : false,
				    backdrop : 'static'
				});
    	
	        	$scope.modalInstance.result.then(function(data) {
        		if (data == "ok"){
        			$scope.getPictures();
        			$scope.getBoreholeImage();
        		}
        		else
        			displayPrompt($scope, $modal, data);
	        	});
        	}, function(error){
        		displayPrompt($scope, $modal, error);
        	});
	    };
	    
	    $scope.getFullImage = function(toggleZoom){
	    	if(!$scope.fullimg)
	    		$scope.fullimg = {zoom : false, height : $scope.imgHeight, start : 0,
	    			width : parseInt($scope.version.image_width_px * $scope.imgHeight / $scope.version.image_height_px)};

	    	if(toggleZoom)
	    		$scope.fullimg.zoom = !$scope.fullimg.zoom;
	    	
	    	$scope.fullimg.start = $scope.query.start_depth;
	    	
	    	height = $scope.fullimg.height;
	    	width = $scope.fullimg.width;
	    	
	    	if($scope.fullimg.zoom){
		    	height = 0;
		    	width = 0;
	    	}

	    	$scope.full_img_path = $scope.makePath('borehole_image', $scope.borehole_id, $scope.fullimg.start, $scope.fullimg.start + 1, 
	    			height, width); 
	    };
	}]
)
.controller('modalController', ['$scope', '$modalInstance', 'Images', '$interval',
    function($scope, $modalInstance, Images, $interval){
		$scope.progress = {max : 100, state : 0};
		var stop;
	
		$scope.intervalFc = function(){
			Images.getProgress(function(data){
	    		var status = data.status;
	    		var splitStatus = data.status.split(' ');
	    		
	    		if(status == "Ok"){	$scope.progress.state = data.progress; } 
	    		else if(status == "Finished"){
	    			$interval.cancel(stop);
	    			$modalInstance.close('ok');
	    		}
	    		else if(splitStatus[0] == "Size"){
	    			$interval.cancel(stop);
	    			var ret = 'Wrong size, should be {w}x{h}'.replace('{w}', splitStatus[1]).replace('{h}', splitStatus[2]);
	    			$modalInstance.close(ret);
	    		}
	    		else if(status == 'no_archive'){
	    			$interval.cancel(stop);
	    			$modalInstance.close(data.status);
	    		}
	    		else
	    			$modalInstance.close(data.status); 			
    		}
		);}
		
		stop = $interval($scope.intervalFc, 500);
		
		$scope.cancel = function(){
			Images.cancelUpload(function(){
				$interval.cancel(stop);
				$modalInstance.close('ok');			
			});
		};
	}]
);