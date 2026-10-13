from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Turma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.PositiveSmallIntegerField()),
                ('disciplina', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('ano', 'disciplina')},
        ),
        migrations.CreateModel(
            name='Aluno',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150)),
                ('ra', models.CharField(max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('turma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alunos', to='core.turma')),
            ],
            options={'ordering': ('nome',)},
        ),
        migrations.AddConstraint(
            model_name='turma',
            constraint=models.UniqueConstraint(fields=('ano', 'disciplina'), name='unique_turma_ano_disciplina'),
        ),
        migrations.AddConstraint(
            model_name='aluno',
            constraint=models.UniqueConstraint(fields=('turma', 'ra'), name='unique_aluno_ra_turma'),
        ),
    ]
