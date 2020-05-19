# python-bimserver-client
A minimal client for the BIMserver.org REST API

Example:

    # Commit an IFC file into a newly created project
    
    import base64
    import bimserver
        
    client = bimserver.api(server_address, username, password)

    deserializer_id = client.ServiceInterface.getDeserializerByName(deserializerName='Ifc2x3tc1 (Streaming)').get('oid')
    project_id = client.ServiceInterface.addProject(projectName="My new project", schema="ifc2x3tc1").get('oid')

    with open(fn, "rb") as f:
        ifc_data = f.read()
        
    client.ServiceInterface.checkin(
        poid=               project_id,
        comment=            "my first commit",
        deserializerOid=    deserializer_id,
        fileSize=           len(ifc_data),
        fileName=           "IfcOpenHouse.ifc",
        data=               base64.b64encode(ifc_data).decode('utf-8'),
        sync=               "false",
        merge=              "false"
    )
    
    
    # Download latest revision from a specified project

    import json
    from urllib import request
    
    project_name = "MyProject"
    client = bimserver.api(server_address, username, password)
    projects = client.ServiceInterface.getProjectsByName(name=project_name)
    project = projects[0]
    
    serializer = client.ServiceInterface.getSerializerByName(serializerName='Ifc4 (Streaming)')
    serializer_id = serializer.get('oid')
    roid = projects[0].get('lastRevisionId')
    
    topicId = client.ServiceInterface.download(
        roids=[roid],
        serializerOid=serializer_id,
        query=json.dumps({}),
        sync='false',
    )
    
    download_url = f"{server_address}/download?token={client.token}&zip=on&topicId={topicId}"
    res = request.urlopen(download_url)
    with open('res.zip', 'wb') as d:
        d.write(res.read())
    
Or for BIMserver version 1.4:

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
