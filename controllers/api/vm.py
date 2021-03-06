import cherrypy
import xmlrpclib
import xml.etree.ElementTree as ET

from socket import gethostbyaddr

from helpers.vnctokens import *
from helpers.auth import *
from helpers.oneerror import *

class VM(object):

    exposed = True

    '''
        Create a new VM

        template_id : the id of template to use with VM
        name        : name for the new VM
    '''
    @cherrypy.tools.isAuthorised()
    @cherrypy.tools.json_in()
    def PUT(self):

        json = cherrypy.request.json
        if not json.get("template_id") or not json.get("name"):
            raise cherrypy.HTTPError(400, "Bad parameters")

        HEADNODE = cherrypy.request.config.get("headnode")
        FEDID = cherrypy.request.cookie.get('fedid').value
        SESSION = cherrypy.request.cookie.get('session').value

        server = xmlrpclib.ServerProxy(HEADNODE)

        request = [
            "%s:%s"%(FEDID,SESSION),      # auth token
            int(json.get("template_id")), # template id
            json.get("name"),             # name of the new vm
            False,                        # start normally
            ""                            # extra context variables
        ]
        response = server.one.template.instantiate(*request)
        validateresponse(response)


    '''
        Delete a VM

        id : the id of the VM to be deleted
    '''
    @cherrypy.tools.isAuthorised()
    def DELETE(self, id=None):

        if id == None:
            raise cherrypy.HTTPError(400, "Bad parameters")

        HEADNODE = cherrypy.request.config.get("headnode")
        FEDID = cherrypy.request.cookie.get('fedid').value
        SESSION = cherrypy.request.cookie.get('session').value

        server = xmlrpclib.ServerProxy(HEADNODE)

        request = [
            "%s:%s"%(FEDID,SESSION), # auth token
            int(id)                  # vmid
        ]
        response = server.one.vm.info(*request)
        vm_info = ET.fromstring(response[1])
        state = vm_info.find('STATE').text

        if state == 14:
            action = "delete"
        else:
            action = "shutdown-hard"

        request = [
            "%s:%s"%(FEDID,SESSION), # auth token
            action,                  # required for quarantining vms
            int(id),                 # id of vm to delete
        ]
        response = server.one.vm.action(*request)
        validateresponse(response)

        deleteToken(FEDID, id)


    '''
        Return JSON list of VM information for the user

        history : 0 = show current running VMs for user,
                  1 = show all VMs, old and current
        offset  : index to start listing vms, used for pagination
        size    : number of results to return, used for pagination
    '''
    @cherrypy.tools.isAuthorised()
    @cherrypy.tools.json_out()
    def GET(self, history=0, offset=0, size=1):

        HEADNODE = cherrypy.request.config.get("headnode")
        FEDID = cherrypy.request.cookie.get('fedid').value
        SESSION = cherrypy.request.cookie.get('session').value

        server = xmlrpclib.ServerProxy(HEADNODE)

        request = [
            "%s:%s"%(FEDID,SESSION),   # auth token
            -3,                        # show only user's VMs
            int(offset),               # offest for pagination
            -1 * int(size),            # number of entries to return
            -1 if history == 0 else -2 # show either active or all VMs
        ]
        response = server.one.vmpool.info(*request)
        validateresponse(response)
        vm_pool = ET.fromstring(response[1])

        request = [
            "%s:%s"%(FEDID,SESSION),   # auth token
            -2,                        # show all visible templates
            -1,                        # list entries from the start
            -1,                        # return all entries
        ]
        response = server.one.templatepool.info(*request)
        validateresponse(response)
        template_pool = ET.fromstring(response[1])

        json = []

        for vm in vm_pool.findall('VM'):
            # find template name from id
            template_type = "unknown"
            template_id = vm.find('TEMPLATE').find('TEMPLATE_ID').text
            for template in template_pool.findall('VMTEMPLATE'):
                if template.find('ID').text == template_id:
                    template_type = template.find('NAME').text

            # vms may not have an ip set
            try:
                ip = vm.find('TEMPLATE').find('NIC').find('IP').text
                hostname = gethostbyaddr(ip)[0]
            except:
                hostname = "-"

            # get/generate vnc token
            token = getToken(FEDID, vm.find('ID').text)
            if token == None:
                token = createToken(FEDID, SESSION, vm.find('ID').text)

            if vm.find('LCM_STATE').text == "11":
                state = "9"
            else:
                state = vm.find('STATE').text

            json.append({
                'id'       : vm.find('ID').text,
                'name'     : vm.find('NAME').text,
                'hostname' : hostname,
                'state'    : state,
                'stime'    : vm.find('STIME').text,
                'etime'    : vm.find('ETIME').text,
                'cpu'      : vm.find('TEMPLATE').find('CPU').text,
                'memory'   : vm.find('TEMPLATE').find('MEMORY').text,
                'type'     : template_type,
                'token'    : token
            })

        return json


    '''
        Upate VM info/state

        id     : the id of VM to update
        action : the action to be performed
    '''
    @cherrypy.tools.isAuthorised()
    def POST(self, **params):

        if not params.get("id") or not params.get("action"):
            raise cherrypy.HTTPError(400, "Bad parameters")

        HEADNODE = cherrypy.request.config.get("headnode")
        FEDID = cherrypy.request.cookie.get('fedid').value
        SESSION = cherrypy.request.cookie.get('session').value

        server = xmlrpclib.ServerProxy(HEADNODE)

        if params.get("action") == 'boot':
            request = [
                "%s:%s"%(FEDID,SESSION), # auth token
                "resume",                # the action to be performed
                int(params.get("id"))    # the VM id
            ]
            response = server.one.vm.action(*request)
            validateresponse(response)
