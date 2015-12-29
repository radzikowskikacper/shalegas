/**
 * @file test08_meanings_srv.js
 * @brief Unit tests for meanings and sections services 
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

test('MeaningsService', function(){
	expect(0);
	
	Meanings = appinj.get('Meanings');
	
	var url = urlprefix + 'meanings/';
	
	httpbackend.expectGET(url).respond(200);
	Meanings.get();
	
	httpbackend.expectGET(url + test_id + '/').respond(200);
	Meanings.get(test_id);
	
	httpbackend.expectPOST(url).respond(200);
	Meanings.add({'name' : 'test_name', 'section' : 'test_section', 'unit' : 'test_unit'});
	
	httpbackend.expectPUT(url + test_id + '/').respond(200);
	Meanings.modify({'name' : 'test_name', 'section' : 'test_section', 'unit' : 'test_unit', 'id' : test_id});
	
	httpbackend.expectDELETE(url + test_id + '/').respond(200);
	Meanings.remove(test_id);
	
	httpbackend.flush();
});

test('SectionsService', function(){
	expect(0);
	
	Sections = appinj.get('Sections');
	
	var url = urlprefix + 'meanings/sections/';
	httpbackend.expectGET(url).respond(200);
	Sections.get();
	
	httpbackend.expectGET(url + test_id + '/').respond(200);
	Sections.get(test_id);
	
	httpbackend.expectPOST(url).respond(200);
	Sections.add({'name' : 'test_name', 'section' : 'test_section', 'unit' : 'test_unit'});
	
	httpbackend.expectPUT(url + test_id + '/').respond(200);
	Sections.modify(test_id, {'name' : 'test_name', 'section' : 'test_section', 'unit' : 'test_unit'});
	
	httpbackend.expectDELETE(url + test_id + '/').respond(200);
	Sections.remove(test_id);
	
	httpbackend.flush();
});