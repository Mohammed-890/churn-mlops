"""Turn an ECS describe response into a register input, preserving infrastructure settings."""
import json
import sys
allowed={'family','taskRoleArn','executionRoleArn','networkMode','containerDefinitions',
         'volumes','placementConstraints','requiresCompatibilities','cpu','memory',
         'pidMode','ipcMode','proxyConfiguration','inferenceAccelerators','ephemeralStorage',
         'runtimePlatform','enableFaultInjection'}
data=json.load(open(sys.argv[1]))
result={k:v for k,v in data.items() if k in allowed}
containers=[c for c in result['containerDefinitions'] if c['name']=='api']
if len(containers)!=1:
    raise ValueError('Expected exactly one api container')
containers[0]['image']=sys.argv[2]
print(json.dumps(result))
