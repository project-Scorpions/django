from django.contrib import admin
from .models import Professor, Course, Sections, Student, User, AcademicYear, Schedule, Admin, EnrollDetail, Enrollment
from django.db.models import Count, Q

class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('prof_id', 'prof_fname', 'prof_lname', 'prof_room')
    search_fields = ('prof_fname', 'prof_lname', 'prof_room')
    ordering = ('prof_id',)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('crs_code', 'crs_name', 'crs_year_lvl', 'crs_sem', 'crs_unit', 'crs_lec_hours', 'crs_lab_hours', 'display_prerequisites', 'prof', 'prof_room')
    list_filter = ('crs_year_lvl', 'crs_sem', 'prof')
    search_fields = ('crs_code', 'crs_name', 'prof__prof_fname', 'prof__prof_lname')

    def prof_room(self, obj):
        return obj.prof.prof_room
    prof_room.short_description = 'Room'

    def display_prerequisites(self, obj):
        prereqs = obj.crs_prerequisite.all()
        if prereqs:
            return ", ".join([prereq.crs_code for prereq in prereqs])
        return "None"
    display_prerequisites.short_description = 'Prerequisites'


class SectionAdmin(admin.ModelAdmin):
    list_display = ('sec_id', 'section_name', 'year_level', 'sec_capacity', 
                   'get_first_sem_enrolled', 'get_first_sem_available',
                   'get_second_sem_enrolled', 'get_second_sem_available')
    list_filter = ('year_level',)
    search_fields = ('section_name',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Annotate with counts for both semesters
        queryset = queryset.annotate(
            _first_sem_enrolled=Count(
                'schedule__enrolldetail__enroll__stud',
                distinct=True,
                filter=Q(schedule__enrolldetail__enroll__enroll_status='Approved') &
                       Q(schedule__enrolldetail__enroll__enroll_sem='First Semester')
            ),
            _second_sem_enrolled=Count(
                'schedule__enrolldetail__enroll__stud',
                distinct=True,
                filter=Q(schedule__enrolldetail__enroll__enroll_status='Approved') &
                       Q(schedule__enrolldetail__enroll__enroll_sem='Second Semester')
            )
        )
        return queryset
    
    # First Semester methods
    def get_first_sem_enrolled(self, obj):
        return obj._first_sem_enrolled
    get_first_sem_enrolled.admin_order_field = '_first_sem_enrolled'
    get_first_sem_enrolled.short_description = '1st Sem Enrolled'
    
    def get_first_sem_available(self, obj):
        return max(0, obj.sec_capacity - obj._first_sem_enrolled)
    get_first_sem_available.short_description = '1st Sem Available'
    
    # Second Semester methods
    def get_second_sem_enrolled(self, obj):
        return obj._second_sem_enrolled
    get_second_sem_enrolled.admin_order_field = '_second_sem_enrolled'
    get_second_sem_enrolled.short_description = '2nd Sem Enrolled'
    
    def get_second_sem_available(self, obj):
        return max(0, obj.sec_capacity - obj._second_sem_enrolled)
    get_second_sem_available.short_description = '2nd Sem Available'
    
    readonly_fields = ('get_first_sem_enrolled', 'get_first_sem_available',
                     'get_second_sem_enrolled', 'get_second_sem_available')


class StudentAdmin(admin.ModelAdmin):
    list_display = ('stud_id', 'full_name','stud_mname', 'stud_gender','stud_contact_num','stud_dob',
                    'stud_email','get_program_display','stud_address','stud_city_add','user_link')
    list_filter = ('stud_gender', 'stud_city_add')
    search_fields = ('stud_lname', 'stud_id')
    ordering = ('stud_id',)

    def full_name(self, obj):
        return f"{obj.stud_fname} {obj.stud_lname}"
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'stud_lname'

    def get_program_display(self, obj):
        return obj.get_stud_program_display()
    get_program_display.short_description = 'Program'

    def user_link(self, obj):
        return obj.user.user_id if obj.user else "None"
    user_link.short_description = 'User ID'


class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_role', 'id_number')
    list_filter = ('user_role',)
    search_fields = ('user_id', 'user_role')
    ordering = ('user_id',)
    
    def id_number(self, obj):
        if hasattr(obj, 'student'):
            return f"Student: {obj.student.stud_id}"
        elif hasattr(obj, 'admin'):
            return f"Admin: {obj.admin.admin_id}"
        return "N/A"
    id_number.short_description = 'ID Number'


class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('acad_year_id', 'acad_year_date')
    search_fields = ('acad_year_date',)
    ordering = ('acad_year_id',)


class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'mis_code',  # Changed from sched_id to mis_code
        'course_code',
        'course_name',  
        'section_name',
        'formatted_schedule',
        'professor_name',
        'duration'
    )
    list_filter = ('sched_day', 'sec', 'crs')
    search_fields = (
        'mis_code',  # Added mis_code to search fields
        'crs__crs_code',
        'crs__crs_name', 
        'sec__section_name'
    )
    ordering = ('mis_code',)  # Changed from sched_id to mis_code
    
    def course_code(self, obj):
        return obj.crs.crs_code
    course_code.short_description = 'Course Code'
    course_code.admin_order_field = 'crs__crs_code'
 
    def course_name(self, obj):
        return obj.crs.crs_name
    course_name.short_description = 'Course Name'
    course_name.admin_order_field = 'crs__crs_name'

    def section_name(self, obj):
        return obj.sec.section_name
    section_name.short_description = 'Section'
    section_name.admin_order_field = 'sec__section_name'

    def formatted_schedule(self, obj):
        return f"{obj.get_sched_day_display()} {obj.sched_time_start.strftime('%H:%M')}-{obj.sched_time_end.strftime('%H:%M')}"
    formatted_schedule.short_description = 'Schedule'

    def professor_name(self, obj):
        return str(obj.crs.prof)
    professor_name.short_description = 'Professor'
    professor_name.admin_order_field = 'crs__prof'

    def duration(self, obj):
        return f"{obj.sched_time_end.hour - obj.sched_time_start.hour} hrs"
    duration.short_description = 'Duration'


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('enroll_id', 'student_info', 'acad_year', 'enroll_year_lvl', 'enroll_sem', 'enroll_status', 'enroll_date')
    list_filter = ('enroll_status', 'enroll_year_lvl', 'enroll_sem')
    search_fields = ('stud__stud_fname', 'stud__stud_lname', 'stud__stud_id')
    
    def student_info(self, obj):
        return f"{obj.stud.stud_id} - {obj.stud.stud_fname} {obj.stud.stud_lname}"
    student_info.short_description = 'Student'


class EnrollDetailAdmin(admin.ModelAdmin):
    list_display = ('enroll_detail_id', 'enrollment_info', 'schedule_info')
    
    def enrollment_info(self, obj):
        return f"Enrollment #{obj.enroll.enroll_id}"
    enrollment_info.short_description = 'Enrollment'
    
    def schedule_info(self, obj):
        return f"{obj.sched.crs.crs_code} - {obj.sched.mis_code} - {obj.sched.get_sched_day_display()} {obj.sched.sched_time_start}-{obj.sched.sched_time_end}"
    schedule_info.short_description = 'Schedule'


# Register your models here
admin.site.register(Professor, ProfessorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Sections, SectionAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(AcademicYear, AcademicYearAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Admin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(EnrollDetail, EnrollDetailAdmin)