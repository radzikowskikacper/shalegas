/**
 * @file test07_boreholes_srv.js
 * @brief Unit tests for boreholes services management 
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

test('BoreholesSpecs', function()     {
    expect(0);
    Boreholes = appinj.get('Boreholes');
    
    var url = urlprefix + 'boreholes/';

    //testing GET all
    httpbackend.expectGET(url).respond(200);
    Boreholes.get();

    //testing GET one
    httpbackend.expectGET(url + test_id + '/').respond(200);
    Boreholes.get(test_id);

    //testing addition
    httpbackend.expectPOST(url).respond(200);
    Boreholes.add();
    
    //testing modify
    httpbackend.expectPUT(url + test_id + '/').respond(200);
    Boreholes.modify({id:test_id});

    //testing removal
    httpbackend.expectDELETE(url + test_id + '/').respond(200);
    Boreholes.remove(test_id);

    httpbackend.flush();
});

test('SimilarityService', function(){
	expect(0);
	Similarity = appinj.get('Similarity');
	
	httpbackend.expectGET('srvsweetspot/ajax/similarities/' + test_id + '/?a=5&b=6').respond(200);
	Similarity.get(test_id, {a : 5, b : 6});
	httpbackend.flush();
});
