from django.shortcuts import render, redirect
from .models import Student, User, Course, Admin, Enrollment, EnrollDetail, AcademicYear, Course, Schedule, Sections, AcademicHistory
from django.contrib import messages
from django.views.generic import View
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Count, Subquery, OuterRef
from datetime import datetime


def student_register(request):
    if request.method == 'POST':
        user = User.objects.create(user_role='student')  
        student = Student.objects.create(
            user=user,
            stud_fname=request.POST['fname'],
            stud_lname=request.POST['lname'],
            stud_mname=request.POST['mname'],
            stud_gender=request.POST['gender'],
            stud_contact_num=request.POST['contact'],
            stud_dob=request.POST['dob'],
            stud_address=request.POST['address'],
            stud_city_add=request.POST['city'],
            stud_email=request.POST['email'],
            stud_program=request.POST['program']
        )
        messages.success(request, f"Registered successfully! Your Student ID is {student.stud_id}")
        return redirect('student_login')
    return render(request, 'main_app/student_register.html')


def student_login(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        dob = request.POST['dob']
        
        try:
            # First try to find a student
            student = Student.objects.get(stud_id=user_id, stud_dob=dob)
            request.session['user_id'] = student.user.user_id
            request.session['student_id'] = student.stud_id
            request.session['student_fname'] = student.stud_fname  
            request.session['student_lname'] = student.stud_lname
            request.session['user_role'] = student.user.user_role
            return redirect('dashboard')
            
        except Student.DoesNotExist:
            try:
                # If not a student, try to find an admin
                admin = Admin.objects.get(admin_id=user_id, admin_dob=dob)
                request.session['user_id'] = admin.user.user_id
                request.session['admin_id'] = admin.admin_id
                request.session['admin_fname'] = admin.admin_fname  
                request.session['admin_lname'] = admin.admin_lname
                request.session['user_role'] = admin.user.user_role
                return redirect('dashboard')
                
            except Admin.DoesNotExist:
                messages.error(request, "Invalid ID or Date of Birth")
    
    return render(request, 'main_app/student_login.html')


# Start Student Portal Views

def student_home(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    return render(request, 'main_app/student_home.html')


def student_courses(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    selected_year_level = request.GET.get('year_level', 'First Year')
    selected_semester = request.GET.get('semester', 'First Semester')
    
    courses = Course.objects.filter(
        crs_year_lvl=selected_year_level,
        crs_sem=selected_semester
    ).prefetch_related('crs_prerequisite')
    
   
    for course in courses:
        course.total_hours = course.crs_lec_hours + course.crs_lab_hours
    
    context = {
        'courses': courses,
        'selected_year_level': selected_year_level,
        'selected_semester': selected_semester,
    }
    return render(request, 'main_app/student_courses.html', context)


def student_enrollment(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    student_id = request.session['student_id']
    student = Student.objects.get(stud_id=student_id)
    current_year = AcademicYear.objects.latest('acad_year_id')
    
    # Check if this is a redirect after submission
    is_submission_redirect = request.GET.get('submitted') == 'true'
    new_enrollment = request.GET.get('new_enrollment') == 'true' or is_submission_redirect
    
    # Check if student is a first-time enrollee
    is_first_time = not Enrollment.objects.filter(stud=student).exists()
    
    # Get enrollments in current academic year ordered by semester
    current_year_enrollments = Enrollment.objects.filter(
        stud=student,
        acad_year=current_year,
        enroll_status='Approved'
    ).order_by('enroll_sem')
    
    # Determine default year level and semester
    default_year_level = 'First Year'
    default_semester = 'First Semester'
    
    if current_year_enrollments.exists():
        if current_year_enrollments.count() == 2:
            # Completed both semesters in current year, move to next year
            last_enroll = current_year_enrollments.last()
            if last_enroll.enroll_year_lvl == 'First Year':
                default_year_level = 'Second Year'
            elif last_enroll.enroll_year_lvl == 'Second Year':
                default_year_level = 'Third Year'
            elif last_enroll.enroll_year_lvl == 'Third Year':
                default_year_level = 'Fourth Year'
            default_semester = 'First Semester'
        else:
            # Only completed one semester in current year
            last_enroll = current_year_enrollments.last()
            default_year_level = last_enroll.enroll_year_lvl
            default_semester = 'Second Semester' if last_enroll.enroll_sem == 'First Semester' else 'First Semester'
    
    # Check for approved enrollment in current semester/year
    approved_enrollment = Enrollment.objects.filter(
        stud=student,
        acad_year=current_year,
        enroll_status='Approved',
        enroll_sem=default_semester,
        enroll_year_lvl=default_year_level
    ).first()
    
    # Check for pending enrollment in current semester/year
    pending_enrollment = None
    if not approved_enrollment:
        pending_enrollment = Enrollment.objects.filter(
            stud=student,
            acad_year=current_year,
            enroll_status='Pending',
            enroll_sem=default_semester,
            enroll_year_lvl=default_year_level
        ).order_by('-enroll_id').first()
    
    # If this is a new enrollment request and there's no pending enrollment, clear any approved enrollment display
    if new_enrollment and not pending_enrollment:
        approved_enrollment = None
    
    # Validation for manual year level selection
    validation_error = None
    selected_year_level = request.GET.get('year_level')
    if selected_year_level and selected_year_level != default_year_level:
        # Validate if student can enroll in this year level
        if selected_year_level == 'Second Year':
            # Check if student completed First Year
            first_year_completed = Enrollment.objects.filter(
                stud=student,
                enroll_year_lvl='First Year',
                enroll_sem='Second Semester',
                enroll_status='Approved',
                acad_year=current_year
            ).exists()
            if not first_year_completed:
                validation_error = "You can't enroll in Second Year because you haven't completed First Year in the current academic year"
        
        elif selected_year_level == 'Third Year':
            # Check if student completed Second Year
            second_year_completed = Enrollment.objects.filter(
                stud=student,
                enroll_year_lvl='Second Year',
                enroll_sem='Second Semester',
                enroll_status='Approved',
                acad_year=current_year
            ).exists()
            if not second_year_completed:
                validation_error = "You can't enroll in Third Year because you haven't completed Second Year in the current academic year"
        
        elif selected_year_level == 'Fourth Year':
            # Check if student completed Third Year
            third_year_completed = Enrollment.objects.filter(
                stud=student,
                enroll_year_lvl='Third Year',
                enroll_sem='Second Semester',
                enroll_status='Approved',
                acad_year=current_year
            ).exists()
            if not third_year_completed:
                validation_error = "You can't enroll in Fourth Year because you haven't completed Third Year in the current academic year"

    # Determine if student is regular or irregular
    student_is_regular = True
    failed_courses_list = []
    
    # Check if this is a forced irregular enrollment (from URL parameter)
    force_irregular = request.GET.get('force_irregular') == 'true'
    
    if not is_first_time:
        # Get the latest enrollment in current academic year
        latest_enrollment = current_year_enrollments.last()
        
        if latest_enrollment:
            failed_courses = AcademicHistory.objects.filter(
                stud=student,
                enroll=latest_enrollment,
                acad_remarks='Failed'
            ).select_related('crs')
            
            if failed_courses.exists():
                student_is_regular = False
                failed_courses_list = [fc.crs for fc in failed_courses]
    
    # Get available courses for irregular enrollment
    available_courses = []
    if not student_is_regular or (is_first_time and force_irregular):
        available_courses = get_available_courses(
            student,
            default_year_level,
            default_semester
        )
    
    # Get all sections for regular enrollment dropdown
    sections = Sections.objects.all()
    
    context = {
        'student': student,
        'current_year': current_year,
        'pending_enrollment': pending_enrollment,
        'approved_enrollment': approved_enrollment,
        'sections': sections,
        'year_level_choices': Enrollment.YEAR_LVL_CHOICES,
        'semester_choices': Enrollment.SEMESTER_CHOICES,
        'default_year_level': default_year_level,
        'default_semester': default_semester,
        'validation_error': validation_error,
        'student_is_regular': student_is_regular,
        'available_courses': available_courses,
        'failed_courses': failed_courses_list,
        'is_first_time': is_first_time,
    }
    
    return render(request, 'main_app/student_enrollment.html', context)


class GetSchedulesView(View):
    def get(self, request, *args, **kwargs):
        course_code = request.GET.get('course_code')
        schedules = Schedule.objects.filter(crs__crs_code=course_code).select_related('sec', 'crs').order_by('sec__section_name', 'sched_day')
        
        # Group schedules by section
        section_groups = {}
        for schedule in schedules:
            section_name = schedule.sec.section_name
            if section_name not in section_groups:
                section_groups[section_name] = {
                    'mis_codes': [],  # Changed from sched_ids to mis_codes
                    'days': [],
                    'times': [],
                    'raw_days': [],
                    'raw_times': [],
                    'room': schedule.crs.prof.prof_room,
                    'section': section_name,
                    'course_code': schedule.crs.crs_code,
                    'course_name': schedule.crs.crs_name
                }
            
            section_groups[section_name]['mis_codes'].append(schedule.mis_code)  # Changed from sched_id to mis_code
            section_groups[section_name]['days'].append(schedule.get_sched_day_display())
            section_groups[section_name]['raw_days'].append(schedule.sched_day)
            time_str = f"{schedule.sched_time_start.strftime('%H:%M')}-{schedule.sched_time_end.strftime('%H:%M')}"
            section_groups[section_name]['times'].append(time_str)
            section_groups[section_name]['raw_times'].append({
                'start': schedule.sched_time_start.strftime('%H:%M'),
                'end': schedule.sched_time_end.strftime('%H:%M')
            })
        
        # Prepare the response data
        data = []
        for section_name, group in section_groups.items():
            # Combine all days and times
            combined_schedule = " | ".join(
                f"{day} {time}" for day, time in zip(group['days'], group['times'])
            )
            
            data.append({
                'mis_code': ",".join(group['mis_codes']),  # Changed from sched_id to mis_code
                'display': f"BSIT {section_name} | {combined_schedule} | {group['room']}",
                'section': section_name,
                'day': ", ".join(group['days']),
                'time': ", ".join(group['times']),
                'raw_days': group['raw_days'],
                'raw_times': group['raw_times'],
                'room': group['room'],
                'course_code': group['course_code'],
                'course_name': group['course_name']
            })
        
        return JsonResponse(data, safe=False)


def get_available_courses(student, year_level, semester):
    """
    Get available courses for a student considering prerequisites and failed courses
    """
    # Get all courses for the requested year level and semester
    all_courses = Course.objects.filter(
        crs_year_lvl=year_level,
        crs_sem=semester
    )
    
    # For first-time enrollees in first year first semester, return only courses with no prerequisites
    if not Enrollment.objects.filter(stud=student).exists():
        if year_level == 'First Year' and semester == 'First Semester':
            return all_courses.filter(crs_prerequisite=None)
        return all_courses
    
    # Rest of your existing logic for non-first-time enrollees...
    academic_history = AcademicHistory.objects.filter(stud=student)
    failed_courses = academic_history.filter(acad_remarks='Failed').values_list('crs', flat=True)
    
    # Find courses with no prerequisites
    no_prereq_courses = all_courses.filter(crs_prerequisite=None)
    
    # Find courses where student has passed all prerequisites
    courses_with_passed_prereqs = []
    for course in all_courses.exclude(crs_prerequisite=None):
        prerequisites = course.crs_prerequisite.all()
        passed_all = True
        
        for prereq in prerequisites:
            # Check if student passed this prerequisite
            prereq_status = academic_history.filter(
                crs=prereq,
                acad_remarks='Passed'
            ).exists()
            
            if not prereq_status:
                passed_all = False
                break
                
        if passed_all:
            courses_with_passed_prereqs.append(course)
    
    # Combine both lists
    available_courses = no_prereq_courses | Course.objects.filter(pk__in=[c.pk for c in courses_with_passed_prereqs])
    
    # Filter out courses the student has already passed
    passed_courses = academic_history.filter(
        acad_remarks='Passed'
    ).values_list('crs__pk', flat=True)
    
    available_courses = available_courses.exclude(pk__in=passed_courses)
    
    # Include courses the student failed in previous semesters (for retaking)
    # Only include if it's the same semester in the next year level
    if semester == 'First Semester':
        # Can retake failed first semester courses from previous year
        available_courses = available_courses | Course.objects.filter(
            pk__in=failed_courses,
            crs_sem='First Semester',
            crs_year_lvl=year_level
        )
    else:  # Second Semester
        # Can retake failed second semester courses from same year level
        available_courses = available_courses | Course.objects.filter(
            pk__in=failed_courses,
            crs_sem='Second Semester',
            crs_year_lvl=year_level
        )
    
    return available_courses.distinct()


@transaction.atomic
def submit_enrollment(request):
    if 'student_id' not in request.session:
        return JsonResponse({'error': 'Not logged in', 'redirect': '/student_login/'}, status=403)
    
    if request.method == 'POST':
        try:
            student_id = request.session['student_id']
            student = Student.objects.get(stud_id=student_id)
            current_year = AcademicYear.objects.latest('acad_year_id')
            
            is_regular = request.POST.get('enrollment_type') == 'regular'
            year_level = request.POST.get('year_level')
            semester = request.POST.get('semester')
            
            if not year_level or not semester:
                return JsonResponse({'error': 'Please select both year level and semester'}, status=400)
            
            # Check for failed courses from previous enrollment
            latest_enrollment = Enrollment.objects.filter(
                stud=student,
                enroll_status='Approved'
            ).order_by('-acad_year__acad_year_date', 'enroll_sem').first()
            
            has_failed_courses = False
            if latest_enrollment:
                has_failed_courses = AcademicHistory.objects.filter(
                    stud=student,
                    enroll=latest_enrollment,
                    acad_remarks='Failed'
                ).exists()
            
            # Force irregular status if student has failed courses
            if has_failed_courses:
                is_regular = False
                
            
            if latest_enrollment:
                current_yl = latest_enrollment.enroll_year_lvl
                current_sem = latest_enrollment.enroll_sem
                
                
                # Check if trying to go back to previous year level
                if (year_level == 'First Year' and current_yl in ['Second Year', 'Third Year', 'Fourth Year']) or \
                   (year_level == 'Second Year' and current_yl in ['Third Year', 'Fourth Year']) or \
                   (year_level == 'Third Year' and current_yl == 'Fourth Year'):
                    return JsonResponse({'error': "You cannot enroll in a previous year level"}, status=400)
            
            
            # Create enrollment record
            enrollment = Enrollment.objects.create(
                stud=student,
                acad_year=current_year,
                enroll_year_lvl=year_level,
                enroll_sem=semester,
                stud_is_regular=is_regular
            )
            
            if is_regular:
                # Find a section with available slots for this year level
                section = Sections.objects.filter(
                    year_level=year_level
                ).annotate(
                    current_enrollment=Count('schedule__enrolldetail__enroll', 
                                            filter=Q(schedule__enrolldetail__enroll__acad_year=current_year) &
                                            Q(schedule__enrolldetail__enroll__enroll_sem=semester) &
                                            Q(schedule__enrolldetail__enroll__enroll_status='Approved'))
                ).filter(
                    current_enrollment__lt=F('sec_capacity')
                ).first()
                
                if not section:
                    return JsonResponse({'error': 'No available sections with capacity for this year level'}, status=400)
                
                # Set the section on the enrollment BEFORE saving
                enrollment.sec = section
                enrollment.save()  # Save again with the section set
                
                # Get all schedules for this section in the current semester
                section_schedules = Schedule.objects.filter(
                    sec=section,
                    crs__crs_sem=semester
                ).select_related('crs')
                
                if not section_schedules.exists():
                    return JsonResponse({'error': 'No schedules available for this section'}, status=400)
                
                # Enroll student in all courses for this section
                for schedule in section_schedules:
                    EnrollDetail.objects.create(
                        enroll=enrollment,
                        sched=schedule
                    )
                
            else:
                # Handle irregular enrollment 
                course_schedules = request.POST.getlist('course_schedule')
                if not course_schedules:
                    return JsonResponse({'error': 'Please select at least one course schedule'}, status=400)
                    
                for mis_codes in course_schedules:
                    # Handle comma-separated MIS codes
                    for mis_code in mis_codes.split(','):
                        try:
                            schedule = Schedule.objects.get(mis_code=mis_code.strip())
                            EnrollDetail.objects.create(
                                enroll=enrollment,
                                sched=schedule
                            )
                        except Schedule.DoesNotExist:
                            continue
            
            return JsonResponse({
                'message': 'Enrollment submitted successfully! Please wait for admin approval.',
                'redirect': '/enrollment/?new_enrollment=true'  # Add this parameter to force refresh
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error submitting enrollment: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def student_schedule(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    student_id = request.session['student_id']
    
    # Get filter parameters
    year_level = request.GET.get('year_level')
    semester = request.GET.get('semester')
    
    # Base queryset
    enrollments = Enrollment.objects.filter(
        stud_id=student_id,
        enroll_status='Approved'
    ).prefetch_related(
        'enrolldetail_set__sched__crs',
        'enrolldetail_set__sched__sec'
    ).order_by('-acad_year__acad_year_date', 'enroll_sem')
    
    # Apply filters if they exist
    if year_level:
        enrollments = enrollments.filter(enroll_year_lvl=year_level)
    if semester:
        enrollments = enrollments.filter(enroll_sem=semester)
    
    return render(request, 'main_app/student_schedule.html', {
        'enrollments': enrollments
    })


def academic_history(request):
    if 'student_id' not in request.session:
        return redirect('student_login')
    
    student_id = request.session['student_id']
    student = Student.objects.get(stud_id=student_id)
    
    # Get all academic history records for the student, ordered by academic year and semester
    academic_history = AcademicHistory.objects.filter(
        stud=student
    ).select_related('crs', 'enroll__acad_year').order_by(
        'enroll__acad_year__acad_year_date',
        'enroll__enroll_sem'
    )
    
    # Group by academic year and semester
    grouped_history = {}
    for record in academic_history:
        key = f"{record.enroll.acad_year.acad_year_date} - {record.enroll.enroll_sem}"
        if key not in grouped_history:
            grouped_history[key] = {
                'year': record.enroll.acad_year.acad_year_date,
                'semester': record.enroll.enroll_sem,
                'year_level': record.enroll.enroll_year_lvl,
                'records': []
            }
        grouped_history[key]['records'].append(record)
    
    context = {
        'student': student,
        'grouped_history': grouped_history.values(),
    }
    
    return render(request, 'main_app/student_academic_history.html', context)


def get_courses(request):
    year_level = request.GET.get('year_level')
    semester = request.GET.get('semester')
    
    courses = Course.objects.filter(
        crs_year_lvl=year_level,
        crs_sem=semester
    ).values('crs_code', 'crs_name', 'crs_unit')
    
    return JsonResponse(list(courses), safe=False)

# End Student Portal Views



def logout_view(request):
    request.session.flush()  
    return redirect('student_login')  



# Start Admin Portal Views

def admin_dashboard(request):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')  
    return render(request, 'main_app/admin_home.html')


def student_records(request):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    # Get gender filter from request
    selected_gender = request.GET.get('gender', '')
    
    # Filter students based on gender if selected
    if selected_gender:
        students = Student.objects.filter(stud_gender=selected_gender).order_by('stud_id')
    else:
        students = Student.objects.all().order_by('stud_id')
    
    context = {
        'students': students,
        'gender_choices': Student.GENDER_CHOICES,
        'selected_gender': selected_gender
    }
    
    return render(request, 'main_app/admin_student_records.html', context)


def pending_enrollment(request):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    pending_enrollments = Enrollment.objects.filter(enroll_status='Pending').select_related('stud', 'acad_year')
    
    context = {
        'pending_enrollments': pending_enrollments
    }
    
    return render(request, 'main_app/admin_enrollment.html', context)


def approve_enrollment(request, enroll_id):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    enrollment = Enrollment.objects.get(enroll_id=enroll_id)
    enrollment.enroll_status = 'Approved'
    enrollment.save()
    
    messages.success(request, f"Enrollment #{enroll_id} approved successfully!")
    return redirect('pending_enrollment')


def reject_enrollment(request, enroll_id):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    enrollment = Enrollment.objects.get(enroll_id=enroll_id)
    enrollment.enroll_status = 'Rejected'
    enrollment.save()
    
    messages.success(request, f"Enrollment #{enroll_id} rejected.")
    return redirect('pending_enrollment')


def enrollment_details(request, enroll_id):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    enrollment = get_object_or_404(Enrollment.objects.select_related(
        'stud', 'acad_year'
    ).prefetch_related(
        'enrolldetail_set__sched__crs',
        'enrolldetail_set__sched__sec'
    ), enroll_id=enroll_id)
    
    return render(request, 'main_app/enrollment_details.html', {
        'enrollment': enrollment,
        'enroll_details': enrollment.enrolldetail_set.all()
    })


def add_academic_remarks(request, enroll_id):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    enrollment = get_object_or_404(Enrollment, enroll_id=enroll_id)
    
    if request.method == 'POST':
        # Process form data
        for detail in enrollment.enrolldetail_set.all():
            remark = request.POST.get(f'remark_{detail.sched.crs.crs_code}')
            if remark:
                AcademicHistory.objects.update_or_create(
                    enroll=enrollment,
                    crs=detail.sched.crs,
                    stud=enrollment.stud,
                    defaults={'acad_remarks': remark}
                )
        messages.success(request, "Academic remarks updated successfully!")
        return redirect('student_records')
    
    # Group enroll details by course
    course_details = {}
    for detail in enrollment.enrolldetail_set.select_related('sched__crs').all():
        course_code = detail.sched.crs.crs_code
        if course_code not in course_details:
            course_details[course_code] = {
                'crs': detail.sched.crs,
                'details': [detail],
                'existing_remark': AcademicHistory.objects.filter(
                    enroll=enrollment,
                    crs=detail.sched.crs
                ).first()
            }
        else:
            course_details[course_code]['details'].append(detail)
    
    context = {
        'enrollment': enrollment,
        'course_details': course_details,
    }
    return render(request, 'main_app/admin_acad_remarks.html', context)


def view_academic_history(request, stud_id):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    student = get_object_or_404(Student, stud_id=stud_id)
    academic_history = AcademicHistory.objects.filter(
        stud=student
    ).select_related('crs', 'enroll').order_by('enroll__acad_year', 'enroll__enroll_sem')
    
    context = {
        'student': student,
        'academic_history': academic_history,
    }
    return render(request, 'main_app/admin_acad_history.html', context)


def select_enrollment_for_remarks(request, stud_id):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    student = get_object_or_404(Student, stud_id=stud_id)
    enrollments = Enrollment.objects.filter(stud=student).order_by('-acad_year', '-enroll_sem')
    
    return render(request, 'main_app/select_enrollment.html', {
        'student': student,
        'enrollments': enrollments
    })


def admin_courses(request):
    if 'admin_id' not in request.session:
        return redirect('student_login')
    
    selected_year_level = request.GET.get('year_level', 'First Year')
    selected_semester = request.GET.get('semester', 'First Semester')
    
    courses = Course.objects.filter(
        crs_year_lvl=selected_year_level,
        crs_sem=selected_semester
    ).prefetch_related('crs_prerequisite')
    
    for course in courses:
        course.total_hours = course.crs_lec_hours + course.crs_lab_hours
    
    context = {
        'courses': courses,
        'selected_year_level': selected_year_level,
        'selected_semester': selected_semester,
    }
    return render(request, 'main_app/admin_courses.html', context)


def admin_schedules(request):
    if request.session.get('user_role') != 'admin':
        return redirect('student_login')
    
    # Get filter parameters from request
    selected_year_level = request.GET.get('year_level', '')
    selected_semester = request.GET.get('semester', '')
    
    # Filter schedules based on parameters
    schedules = Schedule.objects.select_related('crs', 'sec', 'crs__prof').order_by('crs__crs_year_lvl', 'crs__crs_sem', 'sec__section_name', 'sched_day')
    
    if selected_year_level:
        schedules = schedules.filter(crs__crs_year_lvl=selected_year_level)
    
    if selected_semester:
        schedules = schedules.filter(crs__crs_sem=selected_semester)
    
    # Group schedules by course and section for display
    grouped_schedules = {}
    for schedule in schedules:
        key = f"{schedule.crs.crs_code}-{schedule.sec.section_name}"
        if key not in grouped_schedules:
            grouped_schedules[key] = {
                'mis_code': schedule.mis_code,  # Changed from sched_id to mis_code
                'course_code': schedule.crs.crs_code,
                'course_name': schedule.crs.crs_name,
                'section': schedule.sec.section_name,
                'professor': f"{schedule.crs.prof.prof_fname} {schedule.crs.prof.prof_lname}",
                'room': schedule.crs.prof.prof_room,
                'days_times': []
            }
        day_time = f"{schedule.get_sched_day_display()} {schedule.sched_time_start.strftime('%H:%M')}-{schedule.sched_time_end.strftime('%H:%M')}"
        grouped_schedules[key]['days_times'].append(day_time)
    
    context = {
        'grouped_schedules': grouped_schedules.values(),
        'year_level_choices': Course.YEAR_LVL_CHOICES,
        'semester_choices': Course.SEMESTER_CHOICES,
        'selected_year_level': selected_year_level,
        'selected_semester': selected_semester,
    }
    return render(request, 'main_app/admin_schedules.html', context)


# End Admin Portal Views


def dashboard(request):
    user_role = request.session.get('user_role')
    if user_role == 'admin':
        return redirect('admin_dashboard')
    elif user_role == 'student':
        return redirect('student_home')
    else:
        return redirect('student_login')