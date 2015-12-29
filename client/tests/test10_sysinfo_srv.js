/**
 * @file test10_sysinfo_srv.js
 * @brief Unit tests for sysinfo services 
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

test('SysinfoSpecs', function()     {
    Sysinfo = appinj.get('Sysinfo');
    equal(Sysinfo.url, urlprefix);
    
    httpbackend.expectGET(urlprefix + 'current/get/').respond(200);
    Sysinfo.getCurrent();

    httpbackend.expectGET(urlprefix + 'version/get/').respond(200);
    Sysinfo.getVersion();

    httpbackend.expectGET(urlprefix + 'log/10').respond(200);
    Sysinfo.getLogs(10);

    httpbackend.flush();
});

test('UserService', function()  {
    expect(0);

    User = appinj.get('User');
    var url = urlprefix + 'users/';

    httpbackend.expectGET(url).respond(200);
    User.get()
    
    httpbackend.expectGET(url + test_id + '/').respond(200);
    User.get(test_id)
    
    httpbackend.expectPOST(url + 'login/').respond(200);
    User.login();

    httpbackend.expectPOST(url + 'logout/').respond(200);
    User.logout();

    httpbackend.expectDELETE(url + test_id + '/').respond(200);
    User.delete(test_id);

    httpbackend.expectPUT(url + test_id + '/').respond(200);
    User.modify({'id' : test_id, 'username' : 'modified'});

    httpbackend.expectPOST(url).respond(200);
    User.add();
    
    httpbackend.flush();
});

test('ResetService', function(){
	expect(0);
	
	Reset = appinj.get('Reset');
	var url = urlprefix + 'reset/';
	
	httpbackend.expectGET(url).respond(200);
	Reset.showFiles();
	
	httpbackend.expectPOST(url).respond(200);
	Reset.dump();
	
	httpbackend.expectPUT(url).respond(200);
	Reset.restore();
	
	httpbackend.expectDELETE(url).respond(200);
	Reset.delete();
	
	httpbackend.flush();
});