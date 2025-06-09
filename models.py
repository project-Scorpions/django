from django.db import models
import random
import string

# Create your models here.

class Program(models.Model):
    prog_id = models.AutoField(primary_key=True)
    prog_code = models.CharField("Program Code", max_length=10, unique=True)
    prog_name = models.CharField("Program Name", max_length=100)
    prog_description = models.TextField("Description", blank=True, null=True)
    prog_duration = models.IntegerField("Duration (Years)", default=4)
    prog_department = models.CharField("Department", max_length=100, default="College of Computer Studies")
    prog_is_active = models.BooleanField("Is Active", default=True)

    def __str__(self):
        return f"{self.prog_code} - {self.prog_name}"
    
    class Meta:
        db_table = 'program'
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'


class Professor(models.Model):
    prof_id = models.AutoField(primary_key=True)
    prof_fname = models.CharField("First Name", max_length=50)
    prof_lname = models.CharField("Last Name", max_length=50)
    prof_room = models.CharField("Room", max_length=50)

    def __str__(self):
        return f"{self.prof_fname} {self.prof_lname}"
    
    class Meta:
        db_table = 'professor'


class Course(models.Model):
    YEAR_LVL_CHOICES = [
        ("First Year", "First Year"),
        ("Second Year", "Second Year"),
        ("Third Year", "Third Year"),
        ("Fourth Year", "Fourth Year"),
    ]

    SEMESTER_CHOICES = [
        ("First Semester", "First Semester"),
        ("Second Semester", "Second Semester"),
    ]

    crs_code = models.CharField("Course Code", max_length=50, primary_key=True)
    prof = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        db_column='prof_id'  
    )
    prog = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        db_column='prog_id',
        verbose_name="Program",
        null=True,
        blank=True
    )
    crs_year_lvl = models.CharField("Year Level", max_length=50, choices=YEAR_LVL_CHOICES)
    crs_sem = models.CharField("Semester", max_length=50, choices=SEMESTER_CHOICES)
    crs_name = models.CharField("Course Name", max_length=200)
    crs_unit = models.PositiveSmallIntegerField("Units")
    crs_lec_hours = models.PositiveSmallIntegerField("Lec")
    crs_lab_hours = models.PositiveSmallIntegerField("Lab")
    crs_prerequisite = models.ManyToManyField('self', symmetrical=False, blank=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.crs_name
    
    class Meta:
        db_table = 'course'


class Sections(models.Model):
    sec_id = models.AutoField(primary_key=True)
    section_name = models.CharField("Section Name", max_length=100)
    sec_capacity = models.IntegerField("Section Capacity")
    prog = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        db_column='prog_id',
        verbose_name="Program",
        null=True,
        blank=True
    )
    year_level = models.CharField("For Year Level", max_length=50,
        choices=[
            ("First Year", "First Year"),
            ("Second Year", "Second Year"),
            ("Third Year", "Third Year"),
            ("Fourth Year", "Fourth Year"),
        ],
        default="First Year"  
    )

    def __str__(self):
        prog_code = self.prog.prog_code if self.prog else "N/A"
        return f"{prog_code} {self.section_name} (Capacity: {self.sec_capacity})"
    
    @property
    def first_sem_enrolled_count(self):
        """Count of distinct students enrolled in this section for first semester"""
        return Student.objects.filter(
            enrollment__enroll_status='Approved',
            enrollment__enroll_sem='First Semester',
            enrollment__enrolldetail__sched__sec=self
        ).distinct().count()
    
    @property
    def second_sem_enrolled_count(self):
        """Count of distinct students enrolled in this section for second semester"""
        return Student.objects.filter(
            enrollment__enroll_status='Approved',
            enrollment__enroll_sem='Second Semester',
            enrollment__enrolldetail__sched__sec=self
        ).distinct().count()
    
    @property
    def first_sem_available_slots(self):
        """Calculate available slots for first semester, never negative"""
        return max(0, self.sec_capacity - self.first_sem_enrolled_count)
    
    @property
    def second_sem_available_slots(self):
        """Calculate available slots for second semester, never negative"""
        return max(0, self.sec_capacity - self.second_sem_enrolled_count)
    
    # Admin-friendly versions
    def get_first_sem_enrolled(self):
        return self.first_sem_enrolled_count
    get_first_sem_enrolled.short_description = '1st Sem Enrolled'
    
    def get_second_sem_enrolled(self):
        return self.second_sem_enrolled_count
    get_second_sem_enrolled.short_description = '2nd Sem Enrolled'
    
    def get_first_sem_available(self):
        return self.first_sem_available_slots
    get_first_sem_available.short_description = '1st Sem Available'
    
    def get_second_sem_available(self):
        return self.second_sem_available_slots
    get_second_sem_available.short_description = '2nd Sem Available'
    
    class Meta:
        db_table = 'sections'


class User(models.Model):
    USER_ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]
    
    user_id = models.AutoField(primary_key=True)
    user_role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default='student')

    def __str__(self):
        return f"User {self.user_id} ({self.user_role})"

    class Meta:
        db_table = 'user'
        

class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id')
    admin_fname = models.CharField(max_length=50)
    admin_lname = models.CharField(max_length=50)
    admin_dob = models.DateField()
    admin_email = models.EmailField()

    def __str__(self):
        return f"{self.admin_fname} {self.admin_lname}"

    def save(self, *args, **kwargs):
        # Set the starting ID for the first admin
        if not self.admin_id:
            last_admin = Admin.objects.order_by('-admin_id').first()
            if last_admin:
                self.admin_id = last_admin.admin_id + 1
            else:
                self.admin_id = 20001
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'admin'


class Student(models.Model):
    # Remove PROGRAM_CHOICES since we'll use the Program model
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    stud_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id')
    prog = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        db_column='prog_id',
        verbose_name="Program",
        null=True,
        blank=True
    )
    stud_fname = models.CharField(max_length=50)
    stud_lname = models.CharField(max_length=50)
    stud_mname = models.CharField(max_length=50, blank=True, null=True)
    stud_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    stud_contact_num = models.CharField(max_length=15)
    stud_dob = models.DateField()
    stud_address = models.TextField()
    stud_city_add = models.TextField()
    stud_email = models.EmailField()
    # Keep the old field for backward compatibility
    stud_program = models.CharField(
        max_length=100,
        default='BSIT',
        help_text="Legacy field - use prog field instead"
    )

    def __str__(self):
        return f"{self.stud_fname} {self.stud_lname}"
    
    def get_program_display(self):
        """Get program display from the Program model or fallback to stud_program"""
        if self.prog:
            return f"{self.prog.prog_code} - {self.prog.prog_name}"
        return self.stud_program

    class Meta:
        db_table = 'student'


class AcademicYear(models.Model):
    acad_year_id = models.AutoField(primary_key=True)
    acad_year_date = models.CharField(
        max_length=9, 
        unique=True,
    )

    def __str__(self):
        return self.acad_year_date

    class Meta:
        db_table = 'academic_year'


class Schedule(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    # Replace the AutoField with CharField for mis_code as primary key
    mis_code = models.CharField(primary_key=True, max_length=10, verbose_name="MIS Code")
    sec = models.ForeignKey(
        'Sections',
        on_delete=models.CASCADE,
        db_column='sec_id',
        verbose_name="Section"
    )
    crs = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        db_column='crs_code',
        verbose_name="Course"
    )
    sched_day = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        verbose_name="Day"
    )
    sched_time_start = models.TimeField(verbose_name="Start Time", help_text="Format: HH:MM (24-hour clock)")
    sched_time_end = models.TimeField(verbose_name="End Time", help_text="Format: HH:MM (24-hour clock)")

    def __str__(self):
        return f"{self.mis_code} - {self.crs.crs_code} - {self.get_sched_day_display()} {self.sched_time_start}-{self.sched_time_end}"
    
    def save(self, *args, **kwargs):
        # Generate a unique MIS code if one isn't set
        if not self.mis_code:
            self.mis_code = self.generate_mis_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_mis_code():
        """Generate a unique MIS code in format 'XX123' (2 letters, 3 digits)"""
        while True:
            # Generate 2 random uppercase letters
            letters = ''.join(random.choices(string.ascii_uppercase, k=2))
            # Generate 3 random digits
            numbers = ''.join(random.choices(string.digits, k=3))
            # Combine to form MIS code
            mis_code = f"{letters}{numbers}"
            
            # Check if this code already exists
            if not Schedule.objects.filter(mis_code=mis_code).exists():
                return mis_code
    
    class Meta:
        db_table = 'schedule'


class Enrollment(models.Model):
    ENROLL_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    YEAR_LVL_CHOICES = [
        ("First Year", "First Year"),
        ("Second Year", "Second Year"),
        ("Third Year", "Third Year"),
        ("Fourth Year", "Fourth Year"),
    ]

    SEMESTER_CHOICES = [
        ("First Semester", "First Semester"),
        ("Second Semester", "Second Semester"),
    ]

    enroll_id = models.AutoField(primary_key=True)
    stud = models.ForeignKey(Student, on_delete=models.CASCADE, db_column='stud_id')
    sec = models.ForeignKey(Sections, on_delete=models.SET_NULL, null=True, blank=True, db_column='sec_id')
    acad_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, db_column='acad_year_id')
    enroll_year_lvl = models.CharField("Year Level", max_length=50, choices=YEAR_LVL_CHOICES)
    enroll_sem = models.CharField("Semester", max_length=50, choices=SEMESTER_CHOICES)
    enroll_status = models.CharField(max_length=20, choices=ENROLL_STATUS_CHOICES, default='Pending')
    enroll_date = models.DateTimeField(auto_now_add=True)
    stud_is_regular = models.BooleanField(default=True)

    def __str__(self):
        return f"Enrollment #{self.enroll_id} - {self.stud} ({self.get_enroll_status_display()})"
    
    class Meta:
        db_table = 'enrollment'


class EnrollDetail(models.Model):
    enroll_detail_id = models.AutoField(primary_key=True)
    enroll = models.ForeignKey(Enrollment, on_delete=models.CASCADE, db_column='enroll_id')
    # Update to reference Schedule's mis_code field
    sched = models.ForeignKey(Schedule, on_delete=models.CASCADE, db_column='mis_code')
    
    def __str__(self):
        return f"Enrollment Detail #{self.enroll_detail_id} for {self.enroll}"
    
    class Meta:
        db_table = 'enroll_detail'


class AcademicHistory(models.Model):
    REMARK_CHOICES = [
        ('Passed', 'Passed'),
        ('Failed', 'Failed'),
    ]

    acad_id = models.AutoField(primary_key=True)
    crs = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        db_column='crs_code',
        verbose_name="Course"
    )
    enroll = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        db_column='enroll_id',
        verbose_name="Enrollment"
    )
    stud = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        db_column='stud_id',
        verbose_name="Student"
    )
    acad_remarks = models.CharField(
        max_length=20,
        choices=REMARK_CHOICES,
        blank=True,
        null=True
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.stud} - {self.crs} ({self.acad_remarks})"

    class Meta:
        db_table = 'academic_history'
        verbose_name_plural = 'Academic Histories'