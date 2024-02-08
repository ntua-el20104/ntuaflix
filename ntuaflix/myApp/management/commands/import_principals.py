import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from myApp.models import Principals

class Command(BaseCommand):
    help = 'Import a TSV file into the Principals table'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str)

    def handle(self, *args, **options):
        with open(options['tsv_file'], 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                ordering = row['ordering']
                nconst = row['nconst']
                category = row['category']
                job = row['job'] if row['job'] != '\\N' else None
                characters = row['characters'] if row['characters'] != '\\N' else None
                img_url_asset = row['img_url_asset'] if 'img_url_asset' in row and row['img_url_asset'] != '\\N' else None

                try:
                    principal, created = Principals.objects.update_or_create(
                        tconst=tconst,
                        ordering=ordering,
                        defaults={
                            'nconst': nconst,
                            'category': category,
                            'job': job,
                            'characters': characters,
                            'img_url_asset': img_url_asset,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created principal entry {principal}'))
                    else:
                        self.stdout.write(f'Updated principal entry {principal}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating principal entry {tconst}: {e}'))
