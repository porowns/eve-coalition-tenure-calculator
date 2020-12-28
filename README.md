# coalition-activity-crunch
Python utilty to crunch membership statistics for EVE Online coalitions.

Commisioned by Padrick Millar. 

# Requirements
* Python 3.6

# Instructions
1. Create a virtual environment `python3 -m venv env; source ./venv/bin/activate`
2. Install requirements `pip install requirements.txt`
3. Run script `python3 statistics.py`

# Customization
All customization is handled through `coalitions.json`. Add or modify coalitions in JSON format. 

* `alliances.json` and `characters.json` are basically flat file storage, because calling ESI 100k times per run is expensive
