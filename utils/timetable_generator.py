from datetime import datetime, time, timedelta
import random
from models import Timetable, TimeSlot, Subject, TimetableEntry, Classroom, User

class TimetableGenerator:
    def __init__(self, branch, semester, classroom, start_date):
        self.branch = branch
        self.semester = semester
        self.classroom = classroom
        self.start_date = start_date
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.time_slots = []
        self.subjects = []
        self.labs = []
        self.classrooms = []
        self.lab_rooms = []
        self.theory_hours = 14
        self.practical_hours = 12
        self.total_hours = 26

    def initialize_data(self, db):
        """Initialize data from database"""
        # Get time slots
        self.time_slots = TimeSlot.query.all()
        
        # Get subjects for the branch and semester
        self.subjects = Subject.query.filter_by(
            department=self.branch,
            semester=self.semester,
            batch='Theory'
        ).all()
        
        # Get lab subjects
        self.labs = Subject.query.filter_by(
            department=self.branch,
            semester=self.semester,
            batch='Lab'
        ).all()
        
        # Get classrooms for theory
        self.classrooms = Classroom.query.filter_by(
            department=self.branch,
            room_type='lecture'
        ).all()
        
        # Get lab rooms
        self.lab_rooms = Classroom.query.filter_by(
            department=self.branch,
            room_type='lab'
        ).all()

    def generate_timetable(self, db, user_id):
        """Generate an AI-powered timetable following specific rules"""
        self.initialize_data(db)
        
        # Map branch codes to full names
        branch_names = {
            'CE': 'Civil Engineering',
            'ME': 'Mechanical Engineering',
            'EE': 'Electrical Engineering',
            'EC': 'Electronics & Communication',
            'IT': 'Information Technology',
            'CH': 'Chemical Engineering',
            'IC': 'Instrumentation & Control'
        }
        
        # Get full branch name or use original if not found
        full_branch_name = branch_names.get(self.branch, self.branch)
        
        # Create new timetable with department details
        timetable = Timetable(
            title=f"Government Polytechnic Palanpur - {full_branch_name} Department",
            semester=str(self.semester),
            department=full_branch_name,
            created_by=user_id,
            start_date=self.start_date
        )
        db.session.add(timetable)
        db.session.flush()
        
        # Initialize tracking dictionaries
        subject_counts = {subject.id: 0 for subject in self.subjects}
        lab_counts = {lab.id: 0 for lab in self.labs}
        day_subjects = {day: [] for day in self.days}
        
        # First, distribute lab sessions (2 per subject, consecutive slots)
        for lab in self.labs:
            sessions_needed = 2
            while sessions_needed > 0:
                # Find days with enough consecutive slots
                available_days = [day for day in self.days 
                                if len(day_subjects[day]) <= 4 and  # Leave room for 2 consecutive slots
                                lab.id not in day_subjects[day]]
                if available_days:
                    day = random.choice(available_days)
                    # Add two consecutive slots for lab
                    day_subjects[day].extend([lab.id, lab.id])
                    sessions_needed -= 1
        
        # Then, distribute theory lectures (4 per subject)
        for subject in self.subjects:
            lectures_needed = 4
            while lectures_needed > 0:
                # Find day with fewest lectures and no same subject
                available_days = [day for day in self.days 
                                if len(day_subjects[day]) < 6 and  # Max 6 slots per day
                                subject.id not in day_subjects[day] and  # No same subject in a day
                                (not day_subjects[day] or  # First slot of the day
                                 day_subjects[day][-1] != subject.id)]  # Not after same subject
                if available_days:
                    day = min(available_days, key=lambda d: len(day_subjects[d]))
                    day_subjects[day].append(subject.id)
                    lectures_needed -= 1
        
        # Now create actual timetable entries
        for day in self.days:
            available_slots = sorted(self.time_slots.copy(), key=lambda x: x.start_time)
            current_subjects = day_subjects[day].copy()
            
            for slot in available_slots:
                # Skip break time (12:30 - 13:00)
                if slot.start_time <= time(12, 30) and slot.end_time >= time(13, 0):
                    continue
                
                if current_subjects:
                    subject_id = current_subjects.pop(0)
                    subject = next((s for s in self.subjects + self.labs if s.id == subject_id), None)
                    
                    if subject:
                        classroom_id = self.classroom.id if subject in self.subjects else random.choice(self.lab_rooms).id
                        entry = TimetableEntry(
                            timetable_id=timetable.id,
                            day=day,
                            time_slot_id=slot.id,
                            subject_id=subject.id,
                            classroom_id=classroom_id
                        )
                        db.session.add(entry)
            
            # Schedule theory subjects
            for slot in available_slots:
                # Skip break time (12:30 - 13:00)
                if slot.start_time <= time(12, 30) and slot.end_time >= time(13, 0):
                    continue
                
                if current_subjects:
                    subject_id = current_subjects.pop(0)
                    subject = next((s for s in self.subjects + self.labs if s.id == subject_id), None)
                    
                    if subject:
                        classroom_id = self.classroom.id if subject in self.subjects else random.choice(self.lab_rooms).id
                        entry = TimetableEntry(
                            timetable_id=timetable.id,
                            day=day,
                            time_slot_id=slot.id,
                            subject_id=subject.id,
                            classroom_id=classroom_id
                        )
                        db.session.add(entry)
        
        db.session.commit()
        return timetable

    def find_consecutive_slots(self, available_slots, count):
        """Find consecutive time slots"""
        available_slots = sorted(available_slots, key=lambda x: x.start_time)
        for i in range(len(available_slots) - count + 1):
            slots = available_slots[i:i+count]
            is_consecutive = True
            for j in range(len(slots)-1):
                if slots[j].end_time != slots[j+1].start_time:
                    is_consecutive = False
                    break
            if is_consecutive:
                return slots
        return None

    def find_suitable_subject(self, subject_counts, last_subject, subjects):
        """Find a suitable subject based on constraints"""
        available_subjects = [
            subject for subject in subjects
            if subject_counts[subject.id] < 4  # Each subject 4 times a week
            and subject != last_subject  # No consecutive same subject
        ]
        
        if available_subjects:
            # Prioritize subjects with fewer appearances
            min_count = min(subject_counts[s.id] for s in available_subjects)
            candidates = [s for s in available_subjects if subject_counts[s.id] == min_count]
            return random.choice(candidates)
        
        return None
