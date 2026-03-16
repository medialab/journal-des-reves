from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0023_temps_reve_to_booleans'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_ami_parent_heberge',
            field=models.BooleanField(default=False, verbose_name='Avec ami/parent hébergé'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_autres',
            field=models.BooleanField(default=False, verbose_name='Autres'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_colocataire',
            field=models.BooleanField(default=False, verbose_name='Colocataire'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_conjoint',
            field=models.BooleanField(default=False, verbose_name='Avec mon ou ma conjointe'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_enfants',
            field=models.BooleanField(default=False, verbose_name='Avec un enfant ou des enfants'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_parent_grand_parent',
            field=models.BooleanField(default=False, verbose_name='Parent ou grand-parent'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='composition_logement_seul',
            field=models.BooleanField(default=False, verbose_name='Seul.e'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='nb_enfants_cohabitants',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(19)], verbose_name='Combien d’enfants vivent avec vous (même en garde alternée) ?'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='nb_enfants_moins14',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(19)], verbose_name='Combien ont moins de 14 ans ?'),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='statut_couple',
            field=models.IntegerField(blank=True, choices=[(1, 'Oui'), (2, 'Non'), (3, 'Indéterminé'), (4, 'Ne souhaite pas répondre')], null=True, verbose_name='Êtes-vous en couple ?'),
        ),
    ]
