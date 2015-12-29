/**
 * @file test09_measurements_srv.js
 * @brief Unit tests for measurements services 
 */

module('servicesSpec',
       {
			setup : function(){
				urlprefix = 'srvsweetspot/ajax/';
			
			},
           teardown : function()
           {
               //actual teststing happens here
               httpbackend.verifyNoOutstandingExpectation();
               httpbackend.verifyNoOutstandingRequest();
           }
       });

test('ImagesFactory', function(){
	expect(0);
	
	Image = appinj.get('Images');
	
	httpbackend.expectPUT('srvsweetspot/ajax/image').respond(200);
	Image.regenerate({borehole_id : test_id});
	httpbackend.flush();
	
	httpbackend.expectGET('srvsweetspot/ajax/image/progress').respond(200);
	Image.getProgress();
	httpbackend.flush();
	
	httpbackend.expectPOST('srvsweetspot/ajax/image/cancel').respond(200);
	Image.cancelUpload();
	httpbackend.flush();
});

test('TablesServices', function(){
	expect(0);
	
	Tables = appinj.get('Tables');
	var url = urlprefix + 'tables/';
	
	httpbackend.expectGET(url + test_id + '/').respond(200);
	Tables.get(test_id, {});
	httpbackend.flush();
});

test('StratigraphyService', function(){
	expect(0);
	
	Stratigraphy = appinj.get('Stratigraphy');
	var url = urlprefix + 'stratigraphy/';
	
	httpbackend.expectGET(url + test_id + '/?type=STRAT').respond(200);
	Stratigraphy.get(test_id, {});
	httpbackend.flush();
});

test('DataService', function(){
	expect(0);
	
	Data = appinj.get('Data');
	var url = urlprefix + 'data';
	
	httpbackend.expectGET(url + '?type=ALL_BHS').respond(200);
	Data.get({});
	httpbackend.flush();
});

test('MeasurementsService', function(){
	expect(0);

	Measurements = appinj.get('Measurements');
	var url = urlprefix + 'measurements/';
	
	httpbackend.expectGET(url + test_id + '/').respond(200);
	Measurements.get(test_id);

	httpbackend.expectPOST(url + test_id + '/').respond(200);
	Measurements.add(test_id);
	
	httpbackend.expectDELETE(url + test_id + '/').respond(200);
	Measurements.remove(test_id);

	url = urlprefix + 'measurements/export/1/1000-2000/pl';

	httpbackend.expectPOST(url).respond(200);
	Measurements.export(1, 1000, 2000, 'pl');
	httpbackend.flush();
});