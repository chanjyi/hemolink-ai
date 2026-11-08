"""Smoke and authorization tests; run: python -m pytest -q"""
import os
from pathlib import Path
import tempfile

DB = Path(tempfile.mkdtemp()) / "tests.db"
os.environ["HEMOLINK_DB_PATH"] = str(DB)

from fastapi.testclient import TestClient
from app import app


def client(role):
    c=TestClient(app)
    r=c.post('/api/login',json={'email':f'{role}@demo.com','password':'Demo123!'},headers={'X-HemoLink-Request':'app'})
    assert r.status_code==200,r.text
    return c


def hdr():
    return {'X-HemoLink-Request':'app'}


def test_login_and_me():
    c=client('donor')
    assert c.get('/api/me').json()['role']=='donor'
    assert c.post('/api/login',json={'email':'donor@demo.com','password':'wrong'},headers=hdr()).status_code==401


def test_roles_and_inventory():
    donor=client('donor');admin=client('admin')
    item=admin.get('/api/inventory').json()[0]
    assert donor.patch(f'/api/inventory/{item["id"]}',json={'units':1,'threshold':10},headers=hdr()).status_code==403
    update=admin.patch(f'/api/inventory/{item["id"]}',json={'units':2,'threshold':10},headers=hdr())
    assert update.status_code==200, update.text
    assert any(i['id']==item['id'] and i['stock_status']=='low' for i in admin.get('/api/inventory').json())


def test_book_then_cancel():
    donor=client('donor')
    campaigns=donor.get('/api/campaigns').json();slot=campaigns[0]['slots'][0]['id']
    booked=donor.post('/api/bookings',json={'slot_id':slot},headers=hdr())
    assert booked.status_code==200,booked.text
    assert donor.post('/api/bookings',json={'slot_id':slot},headers=hdr()).status_code==409
    assert donor.post(f'/api/bookings/{booked.json()["id"]}/cancel',json={},headers=hdr()).status_code==200
    assert donor.post('/api/bookings',json={'slot_id':slot},headers=hdr()).status_code==200


def test_organizer_create_and_permissions():
    org=client('organizer');donor=client('donor')
    from datetime import date,timedelta
    body={'title':'Test Blood Drive','venue':'Test Community Centre','city':'Putrajaya',
          'event_date':str(date.today()+timedelta(days=8)),'description':'Testing',
          'times':['09:00','11:00'],'capacity':2}
    assert donor.post('/api/campaigns',json=body,headers=hdr()).status_code==403
    r=org.post('/api/campaigns',json=body,headers=hdr())
    assert r.status_code==200,r.text
    assert any(c['id']==r.json()['id'] for c in org.get('/api/organizer/campaigns').json())


def test_forecast_and_overview():
    c=client('admin')
    result=c.get('/api/forecast?region=Selangor&blood_type=all')
    assert result.status_code==200,result.text
    data=result.json()
    import forecast as model
    assert len(data['future'])==7 and len(data['history'])==28
    assert data['official'] is (model.data_file() is not None)  # official MOH data when imported
    assert 'baseline_mae' in data['metrics'] and data['metrics']['selected'] in model.METHODS
    assert 'Selangor' in data['regions']
    assert c.get('/api/overview').status_code==200


def test_signup_and_csrf_header():
    c=TestClient(app)
    assert c.post('/api/signup',json={'name':'Test Student','email':'newstudent@example.com','password':'longsecurepassword'}).status_code==403
    r=c.post('/api/signup',json={'name':'Test Student','email':'newstudent@example.com','password':'longsecurepassword','agree_privacy':True},headers=hdr())
    assert r.status_code==200,r.text
    assert c.get('/api/me').json()['role']=='donor'


def test_external_data_import_format(monkeypatch,tmp_path):
    """Forecast can use official-style data and doesn't mislabel it synthetic."""
    import pandas as pd
    import numpy as np
    import forecast as model
    dates=pd.date_range('2025-01-01',periods=190,freq='D')
    df=pd.DataFrame({
        'date':dates.strftime('%Y-%m-%d'),
        'state':'Selangor','blood_type':'all',
        'donations':(120+dates.dayofweek*4+np.arange(len(dates))%13).tolist(),
    })
    source=tmp_path/'blood_donations_state.csv';df.to_csv(source,index=False)
    monkeypatch.setattr(model,'DATA_FILES',[source])
    model._forecast.cache_clear()
    result=model.get_forecast('Selangor','all')
    assert result['official'] is True
    assert 'KKMNOW' in result['source']
    assert len(result['future'])==7
    assert result['source_last_date']=='2025-07-09'
