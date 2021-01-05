import json
import types

try:
    import urllib2
    urlopen = urllib2.urlopen
except:
    import urllib.request
    urlopen = urllib.request.urlopen

class Api:
    """
    A minimal BIMserver.org API client. Interfaces are obtained from the server
    and can be retrieved as attributes from an API instance. The interfaces 
    expose their methods as functions with keyword arguments.
    
    Example:
    import bimserver
    client = bimserver.Api(server_address, username, password)
    client.Bimsie1ServiceInterface.addProject(projectName="My new project")
    """
    
    class Interface:
        def __init__(self, api, name):
            self.api, self.name = api, name
            meta = self if self.name == "MetaInterface" else self.api.MetaInterface
            methods = meta.make_request("getServiceMethods", serviceInterfaceName="org.bimserver."+self.name)
            for method in methods:
                self.add_method(method)

        def add_method(self, methodMeta):
            def method(self, **kwargs):
                return self.make_request(methodMeta["name"], **kwargs)
            method.__name__ = str(methodMeta["name"])
            method.__doc__ = methodMeta["doc"]
            setattr(self, methodMeta["name"], types.MethodType(method, self))

        def make_request(self, method, **kwargs):
            request = urlopen(self.api.url, data=json.dumps(dict({
                "request": {
                    "interface": self.name,
                    "method": method,
                    "parameters": kwargs
                }
            }, **({"token":self.api.token} if self.api.token else {}))).encode("utf-8"))
            response = json.loads(request.read().decode("utf-8"))
            exception = response.get("response", {}).get("exception", None)
            if exception:
                raise Exception(exception['message'])
            else: return response["response"]["result"]
            
        def __getattr__(self, method):
            print("this should not be called anymore")
            return lambda **kwargs: self.make_request(method, **kwargs)

        def __repr__(self):
            return self.name

        def __dir__(self):
            return sorted(set(Api.Interface.__dict__.keys() + self.__dict__.keys()))

            
            
    token = None
    interfaces = None
    
    def __init__(self, hostname, username=None, password=None):
        self.url = "%s/json" % hostname.strip('/')
        if not hostname.startswith('http://') and not hostname.startswith('https://'):
            self.url = "http://%s" % self.url

        self.interfaces = set(si["simpleName"] for si in self.MetaInterface.getServiceInterfaces())

        self.version = "1.4" if "Bimsie1AuthInterface" in self.interfaces else "1.5"

        if username is not None and password is not None:
            auth_interface = getattr(self, "Bimsie1AuthInterface", getattr(self, "AuthInterface"))
            self.token = auth_interface.login(
                username=username,
                password=password
            )            
            
    def __getattr__(self, interface):
        if self.interfaces is None or interface in self.interfaces:
            return Api.Interface(self, interface)

        # Some form of compatibility:
        if self.version == "1.4" and not interface.startswith("Bimsie1"):
            return self.__getattr__("Bimsie1" + interface)
        elif self.version == "1.5" and interface.startswith("Bimsie1"):
            return self.__getattr__(interface[len("Bimsie1"):])
                
        raise AttributeError("'%s' is does not name a valid interface on this server" % interface)

    def __dir__(self):
        return sorted(set(Api.__dict__.keys()).union(self.__dict__.keys()).union(self.interfaces))
