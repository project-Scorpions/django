# Generated manually for schedule mis_code implementation

from django.db import migrations, models
import random
import string

def generate_mis_code():
    """Generate a unique MIS code in format XX123"""
    # Generate 2 random uppercase letters
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    # Generate 3 random digits
    numbers = ''.join(random.choices(string.digits, k=3))
    # Combine to form MIS code
    return f"{letters}{numbers}"

def convert_to_mis_code(apps, schema_editor):
    # Get models
    Schedule = apps.get_model('main_app', 'Schedule')
    EnrollDetail = apps.get_model('main_app', 'EnrollDetail')
    
    # Create mapping of old sched_id to new mis_code
    mapping = {}
    
    # First pass: generate and save mis_codes
    for schedule in Schedule.objects.all():
        mis_code = generate_mis_code()
        # Ensure uniqueness 
        while Schedule.objects.filter(mis_code=mis_code).exists():
            mis_code = generate_mis_code()
            
        schedule.mis_code = mis_code
        schedule.save()
        mapping[schedule.sched_id] = mis_code
    
    # Second pass: update EnrollDetail records
    for detail in EnrollDetail.objects.all():
        sched_id = detail.sched_id
        if sched_id in mapping:
            # Update directly in the database since the model now uses mis_code as FK
            # We need to manually update this since Django ORM is using the new model structure
            schema_editor.execute(
                f"UPDATE enroll_detail SET mis_code = '{mapping[sched_id]}' WHERE enroll_detail_id = {detail.enroll_detail_id};"
            )

class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0002_previous_migration'),  # replace with your actual previous migration
    ]

    operations = [
        # Step 1: Add mis_code field (nullable at first)
        migrations.AddField(
            model_name='schedule',
            name='mis_code',
            field=models.CharField(max_length=10, null=True, verbose_name='MIS Code'),
        ),
        
        # Step 2: Populate mis_code values
        migrations.RunPython(
            convert_to_mis_code,
            # No reverse function as this is a one-way migration
            reverse_code=migrations.RunPython.noop
        ),
        
        # Step 3: Make mis_code non-nullable
        migrations.AlterField(
            model_name='schedule',
            name='mis_code',
            field=models.CharField(max_length=10, null=False, verbose_name='MIS Code'),
        ),
        
        # Step 4: Add database index to mis_code
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['mis_code'], name='schedule_mis_idx'),
        ),
        
        # Step 5: Alter EnrollDetail table - rename sched_id to mis_code in db_column
        migrations.AlterField(
            model_name='enrolldetail',
            name='sched',
            field=models.ForeignKey('Schedule', on_delete=models.CASCADE, db_column='mis_code'),
        ),
        
        # Step 6: Make mis_code the primary key and drop sched_id
        migrations.AlterField(
            model_name='schedule',
            name='mis_code',
            field=models.CharField(max_length=10, primary_key=True, verbose_name='MIS Code'),
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='sched_id',
        ),
    ]
