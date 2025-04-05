from app import create_app
from models import db, User, Timetable, TimetableEntry, StudyMaterial, Assignment, LostItem, FoundItem

app = create_app()

with app.app_context():
    print("\nUsers:")
    users = User.query.all()
    for user in users:
        print(f"- {user.username} ({user.email})")

    print("\nTimetables:")
    timetables = Timetable.query.all()
    for timetable in timetables:
        print(f"- {timetable.title}")
        entries = TimetableEntry.query.all()
        for entry in entries:
            print(f"  * {entry.subject} on {entry.day_of_week} at {entry.start_time}-{entry.end_time}")

    print("\nStudy Materials:")
    materials = StudyMaterial.query.all()
    for material in materials:
        print(f"- {material.title} ({material.subject})")

    print("\nAssignments:")
    assignments = Assignment.query.all()
    for assignment in assignments:
        print(f"- {assignment.title} due {assignment.due_date}")

    print("\nLost & Found Items:")
    lost_items = LostItem.query.all()
    found_items = FoundItem.query.all()
    print(f"Lost Items: {len(lost_items)}")
    print(f"Found Items: {len(found_items)}") 