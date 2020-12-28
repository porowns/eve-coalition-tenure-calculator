import requests, json, datetime, esipy, arrow, csv
from esipy import App, EsiApp, EsiClient


esi_app = EsiApp()
app = esi_app.get_latest_swagger
app = App.create(url="https://esi.evetech.net/latest/swagger.json?datasource=tranquility")
client = EsiClient(
    retry_requests=True,  # set to retry on http 5xx error (default False)
    headers={'User-Agent': 'https://github.com/porowns/coalition-activity-crunch'},
    raw_body_only=False,  # default False, set to True to never parse response and only return raw JSON string content.
)

with open('./characters.json') as f:
        static_character_data = json.load(f)

with open('./alliances.json') as f:
        static_alliance_data = json.load(f)


def write_static_character_data(character_id, data):
    """
    This query takes forever, to be nicer to ESI we will store static data instead of re-running
    """
    static_character_data[character_id] = data 
    with open('./characters.json', 'w') as f:
        json.dump(static_character_data, f, indent=4)

def write_static_alliance_data(alliance_id, data):
    """
    This query takes forever, to be nicer to ESI we will store static data instead of re-running
    """
    static_alliance_data[alliance_id] = data 
    with open('./alliances.json', 'w') as f:
        json.dump(static_alliance_data, f, indent=4)

def parse_alliance_names_from_json(data):
    l = []
    for key in data.keys():
        l = l + data[key]
    return l 

def resolve_alliance_names_to_ids(alliance_names):
    op = app.op['post_universe_ids'](names=alliance_names)
    return client.request(op).data 

def get_character_history(character_id):
    """
    Returns the days that character has been in corporation
    """
    if str(character_id) in static_character_data:
        return static_character_data[str(character_id)]

    op = app.op['get_characters_character_id_corporationhistory'](character_id=character_id)
    response = client.request(op).data
    if len(response) < 1:
        return 1 
    else:
        delta = datetime.datetime.utcnow() - arrow.get(response[0]['start_date'].to_json()).datetime.replace(tzinfo=None)
        write_static_character_data(character_id, delta.days)
        return delta.days


def get_alliance_members(alliance_id):
    """
    Pulls roster from alliance using EveWho
    """
    if str(alliance_id) in static_alliance_data:
        return static_alliance_data[str(alliance_id)]

    print("Calling EveWho to pull alliance listing for %s" % alliance_id)
    url = f"https://evewho.com/api/allilist/{alliance_id}"
    response = requests.get(url)
    write_static_alliance_data(alliance_id, response.json()['characters'])
    return response.json()['characters']

def calculate_coalition_activity(coalition_name, data, alliance_ids):
    print("Calculating coalition activity... %s" % coalition_name)
    alliance_data = {}
    for alliance in data[coalition_name]:
        print("Processing alliance: %s" % alliance)
        alliance_id = alliance_ids[alliance]
        member_retention_average = 0 
        alliance_members = get_alliance_members(alliance_id)
        progression_counter = 0
        progression_threshold = int(len(alliance_members)/10)
        for member in alliance_members:
            progression_counter += 1
            if (progression_counter % progression_threshold) == 0:
                print(".", end="")
            history_delta = get_character_history(member['character_id'])
            member_retention_average += history_delta

        alliance_average = member_retention_average / len(alliance_members)
        alliance_data[alliance] = alliance_average 
        print("")
        
    return alliance_data




if __name__ == "__main__": 
    with open('./coalitions.json') as f:
        data = json.load(f)
    
    coalition_names = data.keys()
    print("Parsing alliance names")
    alliance_names = parse_alliance_names_from_json(data)
    print("Resolving alliance IDs")
    alliance_ids = { i['name']: i['id'] for i in resolve_alliance_names_to_ids(alliance_names)['alliances']}
    
    coalition_data = {}
    for coalition in coalition_names:
        coalition_data[coalition] = calculate_coalition_activity(coalition, data, alliance_ids)


    with open('output.csv', 'w') as f:  # Just use 'w' mode in 3.x
        print("Writing to output.csv")
        for coalition in coalition_data.keys():
            w = csv.DictWriter(f, coalition_data[coalition].keys())
            w.writeheader()
            w.writerow(coalition_data[coalition])