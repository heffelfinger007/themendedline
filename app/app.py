from flask import Flask, request, jsonify, Response
import requests

app = Flask(__name__)

USGS_BASE = 'https://nwis.waterservices.usgs.gov/nwis'

@app.route('/api/river-data')
def river_data():
    site = request.args.get('site', '')
    if not site:
        return jsonify({'error': 'Missing site parameter'}), 400

    # Fetch discharge (00060) and gauge height (00065)
    iv_url = f'{USGS_BASE}/iv'
    params = {
        'format': 'json',
        'timestamp': 'true',
        'sites': site,
        'parameterCd': '00065,00060',
    }
    try:
        res = requests.get(iv_url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    discharge = None
    gauge_height = None

    for vts in data.get('valueTimeSeries', []):
        for v in vts.get('value', []):
            pc = vts.get('variable', {}).get('variableName', '')
            val = v.get('value')
            if val is None:
                continue
            if 'Discharge' in pc:
                discharge = val
            elif 'Gauge height' in pc:
                gauge_height = val

    # Fetch daily precip (00010) from yesterday
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    dv_url = f'{USGS_BASE}/dv'
    params = {
        'format': 'json',
        'timestamp': 'true',
        'startDT': yesterday.isoformat(),
        'endDT': today.isoformat(),
        'sites': site,
        'parameterCd': '00010',
    }
    try:
        res = requests.get(dv_url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception:
        return jsonify({
            'discharge': discharge,
            'gaugeHeight': gauge_height,
            'precip': None,
        })

    precip = None
    for vts in data.get('valueTimeSeries', []):
        for v in vts.get('value', []):
            if v.get('value') is not None:
                precip = v['value']
                break
        if precip is not None:
            break

    return jsonify({
        'discharge': discharge,
        'gaugeHeight': gauge_height,
        'precip': precip,
    })
