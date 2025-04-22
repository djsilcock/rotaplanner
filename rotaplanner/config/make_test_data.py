import uuid
import json
import datetime

with open("test_data.py", "w") as f:
    f.write("# This file is auto-generated. Do not edit.\n")
    staff_list = [(str(uuid.uuid4()), f"staff-{i}") for i in range(10)]
    location_list = [(str(uuid.uuid4()), f"location {i}") for i in range(10)]
    activity_tags = [(str(uuid.uuid4()), f"tag-{i}") for i in range(10)]
    activities = [
        (
            str(uuid.uuid4()),
            f"activity-{i}",
            (datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i)).isoformat(),
            (
                datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i, hours=1)
            ).isoformat(),
        )
        for i in range(10)
    ]
    f.write(f"staff_list = {json.dumps(staff_list, indent=4)}\n")
    f.write(f"location_list = {json.dumps(location_list, indent=4)}\n")
    f.write(f"activity_tags = {json.dumps(activity_tags, indent=4)}\n")
    f.write(f"activities = {json.dumps(activities, indent=4)}\n")
