# python-bimserver-client
A minimal client for the BIMserver.org REST API

Example:

    # Commit an IFC file into a newly created project
    
    import base64
    import bimserver
    
    client = bimserver.api(server_address, username, password)
    
    deserializer_id = client.Bimsie1ServiceInterface.getSuggestedDeserializerForExtension(extension="ifc").get('oid')
    project_id = client.Bimsie1ServiceInterface.addProject(projectName="My new project").get('oid')
    
    with open("IfcOpenHouse.ifc", "rb") as f:
        ifc_data = f.read()
        
    client.Bimsie1ServiceInterface.checkin(
        poid=               project_id,
        comment=            "my first commit",
        deserializerOid=    deserializer_id,
        fileSize=           len(ifc_data),
        fileName=           "IfcOpenHouse.ifc",
        data=               base64.b64encode(ifc_data).decode('utf-8'),
        sync=               "false"
    )
