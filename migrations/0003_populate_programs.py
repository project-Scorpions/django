from django.db import migrations


def populate_programs(apps, schema_editor):
    Program = apps.get_model('main_app', 'Program')
    
    programs = [
        {
            'prog_code': 'BSIT',
            'prog_name': 'Bachelor of Science in Information Technology',
            'prog_description': 'A four-year degree program that focuses on the application of technology in business and organizations',
            'prog_duration': 4,
            'prog_department': 'College of Computer Studies',
            'prog_is_active': True
        },
        {
            'prog_code': 'BSIS',
            'prog_name': 'Bachelor of Science in Information Systems',
            'prog_description': 'A degree program that combines business and technology to design and implement information systems',
            'prog_duration': 4,
            'prog_department': 'College of Computer Studies',
            'prog_is_active': True
        },
        {
            'prog_code': 'BIT',
            'prog_name': 'Bachelor of Information Technology',
            'prog_description': 'A degree program focused on the technical aspects of information technology',
            'prog_duration': 4,
            'prog_department': 'College of Computer Studies',
            'prog_is_active': True
        },
        {
            'prog_code': 'BSCS',
            'prog_name': 'Bachelor of Science in Computer Science',
            'prog_description': 'A degree program that covers the theoretical and practical aspects of computer science',
            'prog_duration': 4,
            'prog_department': 'College of Computer Studies',
            'prog_is_active': True
        },
        {
            'prog_code': 'BSSE',
            'prog_name': 'Bachelor of Science in Software Engineering',
            'prog_description': 'A degree program focused on software development and engineering principles',
            'prog_duration': 4,
            'prog_department': 'College of Computer Studies',
            'prog_is_active': True
        }
    ]
    
    for prog_data in programs:
        Program.objects.create(**prog_data)


def link_existing_students(apps, schema_editor):
    Student = apps.get_model('main_app', 'Student')
    Program = apps.get_model('main_app', 'Program')
    
    # Map existing students to programs based on stud_program field
    program_mapping = {
        'BSIT': 'BSIT',
        'BSIS': 'BSIS',
        'BIT': 'BIT',
        'BSCS': 'BSCS',
        'BSSE': 'BSSE'
    }
    
    for student in Student.objects.all():
        if student.stud_program in program_mapping:
            try:
                program = Program.objects.get(prog_code=program_mapping[student.stud_program])
                student.prog = program
                student.save()
            except Program.DoesNotExist:
                pass  # Skip if program doesn't exist


def reverse_populate_programs(apps, schema_editor):
    Program = apps.get_model('main_app', 'Program')
    Program.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0002_add_program_table'),
    ]

    operations = [
        migrations.RunPython(populate_programs, reverse_populate_programs),
        migrations.RunPython(link_existing_students, migrations.RunPython.noop),
    ]