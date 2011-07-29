'''
Created on Jul 26, 2011

@author: sdaubin
'''
import json,httplib,os,socket,string
from newrelic.core.exceptions import raise_newrelic_exception
from newrelic.core.config import create_configuration

class NewRelicService(object):
    def __init__(self, remote,app_names=["FIXME Python test"]):
        self._remote = remote
        self._agent_run_id = None
        self._app_names = app_names
        self._configuration = None

    def get_configuration(self):
        return self._configuration

    def get_agent_run_id(self):
        return self._agent_run_id

        
    def agent_version(self):
        #FIXME move this
        return "0.9.0"
        
    def shutdown(self):
        if self.agent_run_id is not None:
            try:
                conn = self._remote.create_connection()
                try:
                    self._remote.invoke_remote(conn, "shutdown", True, self._agent_run_id)
                finally:
                    conn.close()

            except Exception as ex:
                #FIXME log
                print ex
                pass
            self._agent_run_id = None
        
    def connected(self):
        return self._agent_run_id is not None    
        
    def connect(self):
        conn = self._remote.create_connection()
        try:
            redirect_host = self._remote.invoke_remote(conn, "get_redirect_host", True, None)
            
            if redirect_host is not None:
                self._remote.host = redirect_host
                print "Collector redirection to %s" % redirect_host
    
            self.parse_connect_response(self._remote.invoke_remote(conn, "connect", True, None, self.get_start_options()))
        finally:
            conn.close()
            
    def get_app_names(self):
        return self._app_names
        
    def get_identifier(self):
        return string.join(self.get_app_names(),',')
        
    def get_start_options(self):
        options = {"pid":os.getpid(),"language":"python","host":socket.gethostname(),"app_name":self.get_app_names(),"identifier":self.get_identifier(),"agent_version":self.agent_version()}
        '''
        # FIXME 
            if (agent.Config.BootstrapConfig.ServiceConfig.SendEnvironmentInfo) {
                map.Add("environment", agent.Environment);
                map.Add("settings", agent.Config);
            }
        '''

        return options
    
    def parse_connect_response(self, response):
        if "agent_run_id" in response:
            self._agent_run_id = response["agent_run_id"]
        else:
            raise Exception("The connect response did not include an agent run id: %s", str(response))
        
        # Remove this.  we always report once a minute
        if "data_report_period" in response:
            self._data_report_period = response["data_report_period"]
        else:
            raise Exception("The connect response did not contain a data report period")
        
        self._configuration = create_configuration(response)
    
    agent_run_id = property(get_agent_run_id, None, None, "The agent run id")
    configuration = property(get_configuration, None, None, None)
    
    

class JsonRemote(object):
    '''
    classdocs
    '''

    PROTOCOL_VERSION = 9

    def __init__(self, license_key, host, port):
        '''
        Constructor
        '''
        self._host = host
        self._port = port
        self._protocol = "http://"
        self._license_key = license_key

    def get_host(self):
        return self._host


    def set_host(self, value):
        self._host = value

        
    def create_connection(self):
        # FIXME add ssl support
        conn = httplib.HTTPConnection(self._host, self._port)        
        conn.connect()
        return conn
    
    def raise_exception(self, ex):
        # REVIEW 
        if "error_type" in ex and "message" in ex:
            raise_newrelic_exception(ex["error_type"], ex["message"])            
            
        raise Exception("Unknown exception: %s" % str(ex))
    
    def parse_response(self, str):
        try:
            res = json.loads(str)
        except Exception as ex:
            # FIXME log json
            raise Exception("Json load failed error:", ex.message, ex)
        
        if "exception" in res:
            self.raise_exception(res["exception"])            
        if "return_value" in res:
            return res["return_value"]
        
        raise Exception("Unexpected response format: %s" % str)
        
        
    def invoke_remote(self, connection, method, compress = True, agent_run_id = None, *args):
        json_data = json.dumps(args)
        url = self.remote_method_uri(method, agent_run_id)
        
        headers = {"Content-Encoding" : "identity" } # FIXME deflate
        connection.request("POST", url, json_data, headers)
        response = connection.getresponse()
        
        encoding = response.getheader("Content-Encoding")
        
        if response.status is httplib.OK:
            reply = response.read()
            try:
                return self.parse_response(reply)
            except Exception as ex:
                print json_data
                raise ex
        else:
            raise Exception("%s failed: status code %i" % (method, response.status))
        
    
    def remote_method_uri(self, method, agent_run_id = None):
        uri = "/agent_listener/%i/%s/%s?marshal_format=json" % (self.PROTOCOL_VERSION,self._license_key,method)
        if agent_run_id is not None:
            uri += "&run_id=%i" % agent_run_id
        return uri
    
    host = property(get_host, set_host, None, "The New Relic service host")
        
    