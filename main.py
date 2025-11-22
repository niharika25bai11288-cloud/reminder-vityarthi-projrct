import sqlite3
from datetime import datetime, timedelta
import os
import sys

class Priority:
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    
    @classmethod
    def get_name(cls, value):
        names = {
            1: "LOW",
            2: "MEDIUM", 
            3: "HIGH",
            4: "URGENT"
        }
        return names.get(value, "UNKNOWN")

class Status:
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"

class Deadline:
    def _init_(self, id, title, description, due_date, priority, status, category, created_at, completed_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.category = category
        self.created_at = created_at
        self.completed_at = completed_at

class DeadlineReminder:
    def _init_(self, db_name: str = "deadlines.db"):
        self.db_name = db_name
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with deadlines table"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deadlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            ''')
            conn.commit()
            conn.close()
            print(f"✅ Database initialized: {self.db_name}")
        except Exception as e:
            print(f"❌ Database error: {e}")

    def add_deadline(self, title: str, due_date: datetime, priority: int, category: str, description: str = "") -> int:
        """Add a new deadline to the database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO deadlines (title, description, due_date, priority, status, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, due_date.isoformat(), priority, Status.PENDING, category, current_time))
            
            deadline_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ Deadline '{title}' added successfully (ID: {deadline_id})")
            return deadline_id
        except Exception as e:
            print(f"❌ Error adding deadline: {e}")
            return -1

    def get_all_deadlines(self, include_completed: bool = False):
        """Get all deadlines"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            if include_completed:
                cursor.execute('SELECT * FROM deadlines ORDER BY due_date ASC')
            else:
                cursor.execute('SELECT * FROM deadlines WHERE status != ? ORDER BY due_date ASC', (Status.COMPLETED,))
            
            rows = cursor.fetchall()
            conn.close()
            
            deadlines = []
            for row in rows:
                try:
                    deadline = Deadline(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        due_date=datetime.fromisoformat(row[3]),
                        priority=row[4],
                        status=row[5],
                        category=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        completed_at=datetime.fromisoformat(row[8]) if row[8] else None
                    )
                    deadlines.append(deadline)
                except Exception as e:
                    print(f"❌ Error processing deadline row: {e}")
                    continue
            return deadlines
        except Exception as e:
            print(f"❌ Error fetching deadlines: {e}")
            return []

    def get_upcoming_deadlines(self, days: int = 7):
        """Get deadlines due within the next specified days"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            future_date = (datetime.now() + timedelta(days=days)).isoformat()
            current_date = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT * FROM deadlines 
                WHERE due_date BETWEEN ? AND ? 
                AND status != ?
                ORDER BY due_date ASC
            ''', (current_date, future_date, Status.COMPLETED))
            
            rows = cursor.fetchall()
            conn.close()
            
            deadlines = []
            for row in rows:
                try:
                    deadline = Deadline(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        due_date=datetime.fromisoformat(row[3]),
                        priority=row[4],
                        status=row[5],
                        category=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        completed_at=datetime.fromisoformat(row[8]) if row[8] else None
                    )
                    deadlines.append(deadline)
                except Exception as e:
                    print(f"❌ Error processing deadline: {e}")
                    continue
            return deadlines
        except Exception as e:
            print(f"❌ Error fetching upcoming deadlines: {e}")
            return []

    def get_overdue_deadlines(self):
        """Get all overdue deadlines"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            current_date = datetime.now().isoformat()
            
            cursor.execute('''
                SELECT * FROM deadlines 
                WHERE due_date < ? 
                AND status NOT IN (?, ?)
                ORDER BY due_date ASC
            ''', (current_date, Status.COMPLETED, Status.OVERDUE))
            
            rows = cursor.fetchall()
            conn.close()
            
            deadlines = []
            for row in rows:
                try:
                    deadline = Deadline(
                        id=row[0],
                        title=row[1],
                        description=row[2],
                        due_date=datetime.fromisoformat(row[3]),
                        priority=row[4],
                        status=row[5],
                        category=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        completed_at=datetime.fromisoformat(row[8]) if row[8] else None
                    )
                    # Mark as overdue
                    if deadline.status != Status.OVERDUE:
                        self.update_status(deadline.id, Status.OVERDUE)
                        deadline.status = Status.OVERDUE
                    deadlines.append(deadline)
                except Exception as e:
                    print(f"❌ Error processing overdue deadline: {e}")
                    continue
            return deadlines
        except Exception as e:
            print(f"❌ Error fetching overdue deadlines: {e}")
            return []

    def update_status(self, deadline_id: int, status: str) -> bool:
        """Update the status of a deadline"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            completed_at = datetime.now().isoformat() if status == Status.COMPLETED else None
            
            cursor.execute('''
                UPDATE deadlines 
                SET status = ?, completed_at = ?
                WHERE id = ?
            ''', (status, completed_at, deadline_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                print(f"✅ Status updated to '{status}' for deadline ID {deadline_id}")
            else:
                print(f"❌ Failed to update status for deadline ID {deadline_id}")
            
            return success
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return False

    def update_priority(self, deadline_id: int, priority: int) -> bool:
        """Update the priority of a deadline"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE deadlines SET priority = ? WHERE id = ?', (priority, deadline_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                print(f"✅ Priority updated to '{Priority.get_name(priority)}' for deadline ID {deadline_id}")
            else:
                print(f"❌ Failed to update priority for deadline ID {deadline_id}")
            
            return success
        except Exception as e:
            print(f"❌ Error updating priority: {e}")
            return False

    def delete_deadline(self, deadline_id: int) -> bool:
        """Delete a deadline"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM deadlines WHERE id = ?', (deadline_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                print(f"✅ Deadline ID {deadline_id} deleted successfully")
            else:
                print(f"❌ Failed to delete deadline ID {deadline_id}")
            
            return success
        except Exception as e:
            print(f"❌ Error deleting deadline: {e}")
            return False

    def get_deadline(self, deadline_id: int):
        """Get a specific deadline by ID"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM deadlines WHERE id = ?', (deadline_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Deadline(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    due_date=datetime.fromisoformat(row[3]),
                    priority=row[4],
                    status=row[5],
                    category=row[6],
                    created_at=datetime.fromisoformat(row[7]),
                    completed_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
            return None
        except Exception as e:
            print(f"❌ Error fetching deadline: {e}")
            return None

class NotificationManager:
    def _init_(self, reminder):
        self.reminder = reminder
    
    def check_upcoming_deadlines(self, days: int = 3):
        """Check and notify about upcoming deadlines"""
        try:
            upcoming = self.reminder.get_upcoming_deadlines(days)
            overdue = self.reminder.get_overdue_deadlines()
            
            print("\n" + "🔔" * 20)
            print("        DEADLINE NOTIFICATIONS")
            print("🔔" * 20)
            
            if overdue:
                print(f"\n❌ OVERDUE DEADLINES ({len(overdue)}):")
                for deadline in overdue:
                    days_overdue = (datetime.now() - deadline.due_date).days
                    print(f"   ⚠️  '{deadline.title}' - {days_overdue} days overdue!")
            
            if upcoming:
                print(f"\n📅 UPCOMING DEADLINES ({len(upcoming)} in next {days} days):")
                for deadline in upcoming:
                    days_until = (deadline.due_date - datetime.now()).days
                    priority_icon = "🔥" if deadline.priority in [Priority.HIGH, Priority.URGENT] else "⚠️"
                    print(f"   {priority_icon} '{deadline.title}' - Due in {days_until} days ({deadline.due_date.strftime('%m/%d/%Y')})")
            
            if not overdue and not upcoming:
                print("\n✅ No urgent notifications! You're all caught up!")
            
            print("🔔" * 20)
        except Exception as e:
            print(f"❌ Error checking notifications: {e}")

def add_sample_data(reminder):
    """Add sample data for demonstration"""
    sample_deadlines = [
        ("Complete Project Proposal", datetime.now() + timedelta(days=2), Priority.HIGH, "Work"),
        ("Study for Math Exam", datetime.now() + timedelta(days=5), Priority.URGENT, "Education"),
        ("Pay Electricity Bill", datetime.now() + timedelta(days=1), Priority.MEDIUM, "Personal"),
        ("Doctor Appointment", datetime.now() + timedelta(days=7), Priority.LOW, "Health"),
        ("Team Meeting", datetime.now() + timedelta(days=3), Priority.MEDIUM, "Work"),
        ("Birthday Party", datetime.now() + timedelta(days=10), Priority.LOW, "Personal"),
    ]
    
    print("Adding sample deadlines...")
    for title, due_date, priority, category in sample_deadlines:
        reminder.add_deadline(title, due_date, priority, category)
    print("✅ Sample data added successfully!")

def display_deadlines_table(deadlines, title):
    """Display deadlines in a nice table format"""
    if not deadlines:
        print(f"No {title} found!")
        return
    
    print(f"\n{title}")
    print("=" * 100)
    print(f"{'ID':<3} {'Priority':<8} {'Due Date':<12} {'Status':<12} {'Category':<10} {'Title':<30}")
    print("=" * 100)
    
    for deadline in deadlines:
        days_until = (deadline.due_date - datetime.now()).days
        status_icon = "✅" if deadline.status == Status.COMPLETED else "❌" if deadline.status == Status.OVERDUE else "⏳"
        priority_name = Priority.get_name(deadline.priority)
        
        # Color coding for priority
        if deadline.priority == Priority.URGENT:
            priority_display = f"🔴{priority_name}"
        elif deadline.priority == Priority.HIGH:
            priority_display = f"🟠{priority_name}"
        elif deadline.priority == Priority.MEDIUM:
            priority_display = f"🟡{priority_name}"
        else:
            priority_display = f"🟢{priority_name}"
        
        # Truncate long titles
        display_title = deadline.title[:27] + "..." if len(deadline.title) > 30 else deadline.title
        
        time_display = f"Overdue {abs(days_until)}d" if days_until < 0 else f"In {days_until}d"
        
        print(f"{deadline.id:<3} {priority_display:<8} {deadline.due_date.strftime('%m/%d/%Y'):<12} "
              f"{deadline.status:<12} {deadline.category:<10} {display_title:<30} {time_display}")

def main():
    """Main function to run the deadline reminder application"""
    print("📅 DEADLINE REMINDER & TRACKING SYSTEM")
    print("=" * 60)
    
    # Initialize reminder and notifier
    reminder = DeadlineReminder()
    notifier = NotificationManager(reminder)
    
    # Ask if user wants sample data
    try:
        add_samples = input("Do you want to load sample data for testing? (y/n): ").strip().lower()
        if add_samples == 'y':
            add_sample_data(reminder)
    except:
        pass
    
    while True:
        print("\n" + "=" * 60)
        print("📅 DEADLINE REMINDER MENU")
        print("=" * 60)
        print("1. Add New Deadline")
        print("2. View All Deadlines")
        print("3. View Upcoming Deadlines")
        print("4. View Overdue Deadlines")
        print("5. Update Deadline Status")
        print("6. Update Deadline Priority")
        print("7. Delete Deadline")
        print("8. Check Notifications")
        print("9. Exit")
        print("-" * 60)
        
        try:
            choice = input("Enter your choice (1-9): ").strip()
            
            if choice == '1':
                print("\n➕ ADD NEW DEADLINE")
                try:
                    title = input("Enter title: ").strip()
                    if not title:
                        print("❌ Title cannot be empty!")
                        continue
                    
                    due_date_str = input("Enter due date (YYYY-MM-DD): ").strip()
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                    
                    print("\nPriority Levels:")
                    print("  1. LOW 🟢")
                    print("  2. MEDIUM 🟡") 
                    print("  3. HIGH 🟠")
                    print("  4. URGENT 🔴")
                    
                    priority_choice = int(input("Enter priority (1-4): "))
                    if priority_choice not in [1, 2, 3, 4]:
                        print("❌ Invalid priority! Please enter 1-4.")
                        continue
                    
                    category = input("Enter category: ").strip()
                    description = input("Enter description (optional): ").strip()
                    
                    reminder.add_deadline(title, due_date, priority_choice, category, description)
                    
                except ValueError as e:
                    print(f"❌ Invalid input: {e}")
                except Exception as e:
                    print(f"❌ Error adding deadline: {e}")
            
            elif choice == '2':
                print("\n📋 ALL DEADLINES")
                include_completed = input("Include completed deadlines? (y/n): ").strip().lower() == 'y'
                deadlines = reminder.get_all_deadlines(include_completed)
                display_deadlines_table(deadlines, "ALL DEADLINES")
            
            elif choice == '3':
                print("\n📅 UPCOMING DEADLINES")
                try:
                    days = int(input("Enter number of days to look ahead (default 7): ") or "7")
                    deadlines = reminder.get_upcoming_deadlines(days)
                    display_deadlines_table(deadlines, f"UPCOMING DEADLINES (Next {days} days)")
                except ValueError:
                    print("❌ Invalid number of days!")
            
            elif choice == '4':
                print("\n❌ OVERDUE DEADLINES")
                deadlines = reminder.get_overdue_deadlines()
                display_deadlines_table(deadlines, "OVERDUE DEADLINES")
            
            elif choice == '5':
                print("\n🔄 UPDATE DEADLINE STATUS")
                try:
                    deadline_id = int(input("Enter deadline ID: "))
                    deadline = reminder.get_deadline(deadline_id)
                    
                    if not deadline:
                        print("❌ Deadline not found!")
                        continue
                    
                    print(f"\nCurrent status: {deadline.status}")
                    print("Available statuses:")
                    print(f"  1. {Status.PENDING}")
                    print(f"  2. {Status.IN_PROGRESS}")
                    print(f"  3. {Status.COMPLETED}")
                    
                    status_choice = input("Enter status (1-3 or type the status name): ").strip()
                    
                    if status_choice == "1":
                        new_status = Status.PENDING
                    elif status_choice == "2":
                        new_status = Status.IN_PROGRESS
                    elif status_choice == "3":
                        new_status = Status.COMPLETED
                    else:
                        new_status = status_choice
                    
                    # Validate status
                    valid_statuses = [Status.PENDING, Status.IN_PROGRESS, Status.COMPLETED, Status.OVERDUE]
                    if new_status not in valid_statuses:
                        print("❌ Invalid status!")
                        continue
                    
                    reminder.update_status(deadline_id, new_status)
                    
                except (ValueError, KeyError):
                    print("❌ Invalid deadline ID or status!")
            
            elif choice == '6':
                print("\n🎯 UPDATE DEADLINE PRIORITY")
                try:
                    deadline_id = int(input("Enter deadline ID: "))
                    deadline = reminder.get_deadline(deadline_id)
                    
                    if not deadline:
                        print("❌ Deadline not found!")
                        continue
                    
                    print(f"\nCurrent priority: {Priority.get_name(deadline.priority)}")
                    print("Available priorities:")
                    print("  1. LOW 🟢")
                    print("  2. MEDIUM 🟡")
                    print("  3. HIGH 🟠")
                    print("  4. URGENT 🔴")
                    
                    new_priority = int(input("Enter new priority (1-4): "))
                    if new_priority not in [1, 2, 3, 4]:
                        print("❌ Invalid priority! Please enter 1-4.")
                        continue
                    
                    reminder.update_priority(deadline_id, new_priority)
                    
                except (ValueError, KeyError):
                    print("❌ Invalid deadline ID or priority!")
            
            elif choice == '7':
                print("\n🗑️ DELETE DEADLINE")
                try:
                    deadline_id = int(input("Enter deadline ID to delete: "))
                    deadline = reminder.get_deadline(deadline_id)
                    
                    if not deadline:
                        print("❌ Deadline not found!")
                        continue
                    
                    confirm = input(f"Are you sure you want to delete '{deadline.title}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        reminder.delete_deadline(deadline_id)
                    else:
                        print("Deletion cancelled.")
                        
                except ValueError:
                    print("❌ Invalid deadline ID!")
            
            elif choice == '8':
                print("\n🔔 NOTIFICATIONS")
                try:
                    days = int(input("Enter days to check for upcoming deadlines (default 3): ") or "3")
                    notifier.check_upcoming_deadlines(days)
                except ValueError:
                    print("❌ Invalid number of days!")
            
            elif choice == '9':
                print("\n👋 Thank you for using Deadline Reminder! Stay productive! 🚀")
                break
            
            else:
                print("❌ Invalid choice! Please enter a number between 1-9.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Program interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if _name_ == "_main_":
    main()