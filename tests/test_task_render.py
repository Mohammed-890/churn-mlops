import json
import subprocess
import sys
from src.train import ROOT

def test_render_preserves_settings_and_removes_response_fields(tmp_path):
    data={'family':'churnops','taskDefinitionArn':'old-arn','revision':7,
          'status':'ACTIVE','registeredAt':'date','cpu':'512','memory':'1024',
          'executionRoleArn':'execution-role','networkMode':'awsvpc',
          'requiresCompatibilities':['FARGATE'],
          'containerDefinitions':[{'name':'api','image':'old','user':'10001',
                                   'readonlyRootFilesystem':True}]}
    path=tmp_path/'task.json'; path.write_text(json.dumps(data))
    result=subprocess.run([sys.executable,str(ROOT/'scripts/render_task.py'),str(path),'new@sha256:abc'],
                          capture_output=True,text=True,check=True)
    updated=json.loads(result.stdout)
    assert updated['cpu']=='512'
    assert updated['executionRoleArn']=='execution-role'
    assert updated['containerDefinitions'][0]['image']=='new@sha256:abc'
    assert updated['containerDefinitions'][0]['readonlyRootFilesystem'] is True
    assert 'revision' not in updated and 'taskDefinitionArn' not in updated
