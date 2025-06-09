from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0001_initial'),  # Replace with your last migration
    ]

    operations = [
        # Create Program table
        migrations.CreateModel(
            name='Program',
            fields=[
                ('prog_id', models.AutoField(primary_key=True, serialize=False)),
                ('prog_code', models.CharField(max_length=10, unique=True, verbose_name='Program Code')),
                ('prog_name', models.CharField(max_length=100, verbose_name='Program Name')),
                ('prog_description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('prog_duration', models.IntegerField(default=4, verbose_name='Duration (Years)')),
                ('prog_department', models.CharField(default='College of Computer Studies', max_length=100, verbose_name='Department')),
                ('prog_is_active', models.BooleanField(default=True, verbose_name='Is Active')),
            ],
            options={
                'verbose_name': 'Program',
                'verbose_name_plural': 'Programs',
                'db_table': 'program',
            },
        ),
        
        # Add prog_id field to Student table
        migrations.AddField(
            model_name='student',
            name='prog',
            field=models.ForeignKey(blank=True, db_column='prog_id', null=True, on_delete=django.db.models.deletion.PROTECT, to='main_app.program', verbose_name='Program'),
        ),
        
        # Add prog_id field to Course table
        migrations.AddField(
            model_name='course',
            name='prog',
            field=models.ForeignKey(blank=True, db_column='prog_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.program', verbose_name='Program'),
        ),
        
        # Add prog_id field to Sections table
        migrations.AddField(
            model_name='sections',
            name='prog',
            field=models.ForeignKey(blank=True, db_column='prog_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='main_app.program', verbose_name='Program'),
        ),
    ]