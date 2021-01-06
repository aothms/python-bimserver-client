import json
import types
import inspect

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

    token = None
    interfaces = None

    def __init__(self, hostname, username=None, password=None):
        self.url = "%s/json" % hostname.strip('/')
        if not hostname.startswith('http://') and not hostname.startswith('https://'):
            self.url = "http://%s" % self.url

        interfaceMetaList = self.make_request( "MetaInterface", "getServiceInterfaces")
        # index by short interface name only might fail with multiple name spaces, but currently there is only one
        self.interfaceNames = [interfaceMeta['simpleName'] for interfaceMeta in interfaceMetaList]
        for interfaceMeta in interfaceMetaList:
            setattr(self, interfaceMeta['simpleName'], Interface(self, interfaceMeta['simpleName'], interfaceMeta['name']))

        self.version = "1.4" if "Bimsie1AuthInterface" in self.interfaceNames else "1.5"

        if username is not None and password is not None:
            self.token = self.AuthInterface.login(
                username=username,
                password=password
            )            
            
    def __getattr__(self, interface):
        # Some form of compatibility:
        if self.version == "1.4" and not interface.startswith("Bimsie1"):
            return getattr(self, "Bimsie1" + interface)
        elif self.version == "1.5" and interface.startswith("Bimsie1"):
            return getattr(self, interface[len("Bimsie1"):])
        raise AttributeError("'%s' is does not name a valid interface on this server" % interface)

    def __dir__(self):
        return sorted(set(Api.__dict__.keys()).union(self.__dict__.keys()).union(self.interfaceNames))

    def make_request(self, interface, method, **kwargs):
        request = urlopen(self.url, data=json.dumps(dict({
            "request": {
                "interface": interface,
                "method": method,
                "parameters": kwargs
            }
        }, **({"token": self.token} if self.token else {}))).encode("utf-8"))
        response = json.loads(request.read().decode("utf-8"))
        exception = response.get("response", {}).get("exception", None)
        if exception:
            raise Exception(exception['message'])
        else:
            return response["response"]["result"]

class Interface:
    def __init__(self, api, name, longName):
        self.api, self.name, self.longName = api, name, longName
        methods = self.api.make_request("MetaInterface", "getServiceMethods", serviceInterfaceName=longName)
        for method in methods:
            self.add_method(method)

    def add_method(self, methodMeta):
        def method(self, **kwargs):
            return self.api.make_request(self.name, methodMeta["name"], **kwargs)

        method.__name__ = str(methodMeta["name"])
        method.__doc__ = methodMeta["doc"]

        # add parameter info to doc, will only work after fix of BIMserver issue #1179, TODO: check BIMserver version
        params = self.api.make_request("MetaInterface", "getServiceMethodParameters", serviceInterfaceName=self.longName, serviceMethodName=methodMeta['name'])
        try:
            inspect.signature(method) # TODO for Python >= 3.3, modify signature
        except AttributeError:
            pass
        for p in params:
            method.__doc__ += "%s : %s\n    %s\n" % (p['name'], p['type']['name'], p['doc'])

        setattr(self, methodMeta["name"], types.MethodType(method, self))

    def __repr__(self):
        return self.name

    def __dir__(self):
        return sorted(set(Interface.__dict__.keys()).union(self.__dict__.keys()))
