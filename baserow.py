import requests

import config

headers = {
    "Authorization": f"Token {config.baserow_apikey}"
}

def list_rows(id):
    data = []
    results = {
        "next": f"{config.baserow_url}/database/rows/table/{id}/?user_field_names=true&size=200"
    }
    while results["next"]:
        results = requests.get(results["next"], headers=headers).json()
        data.extend(results["results"])
    return {x['id']: x for x in data}

def get_row(table_id, id):
    return requests.get(f"{config.baserow_url}/database/rows/table/{table_id}/{id}/?user_field_names=true", headers=headers).json()

def list_fields(id):
    req = requests.get(f"{config.baserow_url}/database/fields/table/{id}/", headers=headers)
    return {x['name']: x for x in req.json()}

def get_requests():
    fields = list_fields(config.baserow_requests_table)
    requested = list_rows(config.baserow_requests_table)
    departments = list_rows(fields['Department']['link_row_table_id'])
    for request in requested.values():
        assert len(request.get("Department")) == 1
        department = request['Department'][0]['id']
        assert department in departments
        request['dept'] = departments[department]
        request['checked_out'] = (request['Status'] or {'value': None})['value'] == "Picked Up"
    return requested

def get_request(id):
    fields = list_fields(config.baserow_requests_table)
    request = get_row(config.baserow_requests_table, id)
    print(request)
    assert len(request.get("Department")) == 1
    department = get_row(fields['Department']['link_row_table_id'], request['Department'][0]['id'])
    request['dept'] = department
    request['checked_out'] = (request['Status'] or {'value': None})['value'] == "Picked Up"
    return request

def get_sections(request):
    field_sections = {
        "Power": [
            "25' Ext Cords",
            "50' Ext Cords",
            "Powerstrips",
            "Single-phase Power Whips",
            "dept:Power",
        ],
        "PPE": [
            "68oz Hand Sanitizer",
            "8oz Hand Sanitizer",
            "Boxes Face Masks",
            "Boxes Medium Nitrile Gloves",
            "Boxes XL Nitrile Gloves",
            "Cleaning Wipes",
            "Rolls Paper Towels",
            "Sanitizing Spray Bottle"
        ],
        "Office Supplies": [
            "Ballpoint Pens",
            "Black Gaff",
            "Clipboards",
            "Dry Erase Markers",
            "Easel Tripods",
            "Large Whiteboards",
            "Medium Whiteboards",
            "Small Whiteboards",
            "Mechanical Pencils",
            "Reams Paper",
            "Rolls Painters Tape",
            "Scissors",
            "Scotch Tape Dispensers",
            "Sharpies",
            "Staplers",
            "Thin Spike Tape",
            "Sticky Notes",
            "Whiteboard Erasers",
            "Wide Spike Tape",
            "Other Office Supplies",
        ],
        "Technology": [
            "dept:Barcode Readers",
            "dept:Cameras",
            "Cable Ramps",
            "DI Boxes",
            "Keyboards",
            "Mice",
            "Monitors",
            "dept:Phones",
            "Pipe and Drape (feet)",
            "dept:Printers",
            "Projector Screens",
            "dept:Projectors",
            "Radio Gang Chargers",
            "Radios",
            "Sandbags",
            "Speakers",
            "dept:Square Readers",
            "dept:TVs",
            "dept:iPads",
            "dept:Laptops",
            "dept:AV Gear",
            "Notes",
        ],
        "LensRentals": [
            "dept:LensRentals Items"
        ]
    }

    request_fields = list_fields(config.baserow_requests_table)
    department_fields = list_fields(request_fields['Department']['link_row_table_id'])
    sections = []
    for section_name, field_section in field_sections.items():
        counted_items = []
        tracked_items = []
        textual_items = []
        for item in field_section:
            if item.startswith("dept:"):
                field_name = item.split("dept:", 1)[1]
                field = department_fields[field_name]
                raw_value = request['dept'][field_name]
            else:
                field_name = item
                field = request_fields[field_name]
                raw_value = request[field_name]
            if field['type'] == "number":
                if raw_value and int(raw_value):
                    counted_items.append({
                        "name": field_name,
                        "value": raw_value
                    })
            elif field['type'] == "link_row":
                if raw_value:
                    linked_table = list_rows(field['link_row_table_id'])
                    for val in raw_value:
                        tracked_items.append({
                            "id": val['id'],
                            "table_id": field['link_row_table_id'],
                            "name": val['value'],
                            "checked_out": (linked_table[val['id']]['Status'] or {'value': None})['value'] == "Picked Up"
                        })
            elif field['type'] in ["text", "long_text"]:
                if raw_value and raw_value.strip():
                    textual_items.extend([x.strip() for x in raw_value.split("\n") if x.strip()])
            else:
                print(f"Unhandled field type {field['type']}")
        if counted_items or tracked_items or textual_items:
            sections.append({
                "name": section_name,
                "checked_out": all([x['checked_out'] for x in tracked_items]) and request['checked_out'],
                "counted_items": counted_items,
                "tracked_items": tracked_items,
                "textual_items": textual_items
            })
    return sections

def update_status(table_id, row_id, status):
    req = requests.patch(f"{config.baserow_url}/database/rows/table/{table_id}/{row_id}/?user_field_names=true", headers=headers, json={
        "Status": status
    })
    assert req.status_code == 200

def update_status_batch(table_id, row_ids, status):
    req = requests.patch(f"{config.baserow_url}/database/rows/table/{table_id}/batch/?user_field_names=true", headers=headers, json={
        "items": [
            {
                "id": row_id,
                "Status": status
            } for row_id in row_ids
    ]})
    print(req.status_code, req.text)
    assert req.status_code == 200

def update_request_status(request, status):
    sections = get_sections(request)
    updates = {}
    for section in sections:
        for tracked_item in section['tracked_items']:
            table_id = tracked_item['table_id']
            if not table_id in updates:
                updates[table_id] = []
            updates[table_id].append(tracked_item['id'])
    for table_id, row_ids in updates.items():
        update_status_batch(table_id, row_ids, status)
    update_status(config.baserow_requests_table, request['id'], status)

