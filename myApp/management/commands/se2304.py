from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError
import json, sqlite3
from contextlib import contextmanager
from django.db import connections
from django.db.utils import OperationalError
from myApp.models import *
# from models import Names
from django.core.exceptions import ValidationError
import csv
import requests 
import os
from django.contrib.auth import authenticate
import jwt
from datetime import datetime, timedelta
from django.conf import settings

def create_jwt_token(data):
    """Create a JWT token with provided data."""
    payload = data.copy()
    # Set the expiration time for the token (e.g., 24 hours from now)
    payload['exp'] = datetime.utcnow() + timedelta(days=1)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

DATABASE_PATH = 'db.sqlite3'

class Command(BaseCommand):
    help = 'Custom Command for our WebApp (Gamo Tin Patra)'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='subcommand')

        # Subparser for the adduser command
        adduser_parser = subparsers.add_parser('adduser')
        adduser_parser.add_argument('--username', required=True)
        adduser_parser.add_argument('--password', required=True)

        # See users in database
        seeusers_parser = subparsers.add_parser('seeusers')

        # Health Check 
        healthcheck_parser = subparsers.add_parser('healthcheck')

        # Subparser for the login command
        login_parser = subparsers.add_parser('login')
        login_parser.add_argument('--username', required=True)
        login_parser.add_argument('--password', required=True)

        # Subparser for the addmovie command
        addmovie_parser = subparsers.add_parser('addmovie')
        addmovie_parser.add_argument('--tconst', required=True)
        addmovie_parser.add_argument('--titleType', required=True)
        addmovie_parser.add_argument('--primaryTitle', required=True)
        addmovie_parser.add_argument('--originalTitle', required=True)
        addmovie_parser.add_argument('--isAdult', required=True, type=int)
        addmovie_parser.add_argument('--startYear', required=True)
        addmovie_parser.add_argument('--endYear')
        addmovie_parser.add_argument('--runtimeMinutes', type=int)
        addmovie_parser.add_argument('--genres')
        addmovie_parser.add_argument('--img_url_asset')

        #See movies in database
        seeusers_parser = subparsers.add_parser('seemovies')

        # New subparser for the newcrew command
        newcrew_parser = subparsers.add_parser('newcrew')
        newcrew_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')

        # Subparser for the addepisode command
        addepisode_parser = subparsers.add_parser('addepisode')
        addepisode_parser.add_argument('--tconst', required=True)
        addepisode_parser.add_argument('--parentTconst')
        addepisode_parser.add_argument('--seasonNumber', type=int)
        addepisode_parser.add_argument('--episodeNumber', type=int)

        # Subparser for the addrating command
        addrating_parser = subparsers.add_parser('addrating')
        addrating_parser.add_argument('--tconst', required=True)
        addrating_parser.add_argument('--averageRating', required=True, type=float)
        addrating_parser.add_argument('--numVotes', required=True, type=int)

        # Adding searchtitle subparser
        searchtitle_parser = subparsers.add_parser('searchtitle')
        searchtitle_parser.add_argument('--titlepart', required=True)

        # Adding bygenre subparser
        bygenre_parser = subparsers.add_parser('bygenre')
        bygenre_parser.add_argument('--genre', type=str, help='Genre of the movies to filter by.')
        bygenre_parser.add_argument('--min', type=float, help='Minimum average rating of the movies.')
        bygenre_parser.add_argument('--from', dest='from_year', type=str, help='Start year for filtering movies.', default=None)
        bygenre_parser.add_argument('--to', dest='to_year', type=str, help='End year for filtering movies.', default=None)

        # Subparser for the addname command
        addname_parser = subparsers.add_parser('addname')
        addname_parser.add_argument('--nameID', required=True)
        addname_parser.add_argument('--name', required=True)
        addname_parser.add_argument('--namePoster')
        addname_parser.add_argument('--birthYear', type=int)
        addname_parser.add_argument('--deathYear', type=int)
        addname_parser.add_argument('--profession')
        addname_parser.add_argument('--titleID')  # Assuming a single title; you could modify this to accept multiple IDs
        addname_parser.add_argument('--category')

        # Subparser for the name command
        name_parser = subparsers.add_parser('name')
        name_parser.add_argument('--nameid', required=True)

        # Subparser for the searchname command
        searchname_parser = subparsers.add_parser('searchname')
        searchname_parser.add_argument('--name', required=True)

        # Subparser for the name command
        title_parser = subparsers.add_parser('title')
        title_parser.add_argument('--titleID', required=True)

        # Inside the add_arguments method, add the following code:
        newepisode_parser = subparsers.add_parser('newepisode')
        newepisode_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')

        # Inside the add_arguments method, add the following code:
        newratings_parser = subparsers.add_parser('newratings')
        newratings_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')

        newprincipals_parser = subparsers.add_parser('newprincipals')
        newprincipals_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')

        newnames_parser = subparsers.add_parser('newnames')
        newnames_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')

        newakas_parser = subparsers.add_parser('newakas')
        newakas_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')
        
        newtitles_parser = subparsers.add_parser('newtitles')
        newtitles_parser.add_argument('--filename', type=str, required=True, help='Path to the TSV file')

        # Add subparser for resetall command
        resetall_parser = subparsers.add_parser('resetall')

    def handle(self, *args, **options):
        subcommand = options['subcommand'] 
#---------------------------------------------subcommands------------------------------------------------
        if subcommand == 'adduser':
            self.add_user(options['username'], options['password'])
        elif subcommand == 'addmovie':
            self.add_movie(options)
        elif subcommand == 'addcrew':
            self.add_crew(options)
        elif subcommand == 'addepisode':
            self.add_episode(options)
        elif subcommand == 'addrating':
            self.add_rating(options)
        elif subcommand == 'seeusers':
            self.see_users()
        elif subcommand =='seemovies':
            self.see_movies()
        elif subcommand == 'searchtitle':
            self.search_title(options['titlepart'])
        elif subcommand == 'bygenre':
            self.search_by_genre(options['genre'], options['min'], options.get('from_year'), options.get('to_year'))
        elif subcommand == 'addname':
            self.add_name(options)
        elif subcommand == 'name':
            self.show_name(options['nameid'])
        elif subcommand == 'title':
            self.show_title(options['titleID'])
        elif subcommand == 'searchname':
            self.search_name(options['name'])
        elif subcommand == 'searchtitle':
            self.search_title(options['titlepart'])
        elif subcommand == 'newcrew':
            self.import_crew_from_tsv(options)
        elif subcommand == 'newepisode':
            self.import_episode(options)
        elif subcommand == 'newratings':
            self.import_rating(options)
        elif subcommand == 'newprincipals':
            self.import_principals(options)
        elif subcommand == 'newnames':
            self.import_names(options)
        elif subcommand == 'newakas':
            self.import_akas(options)
        elif subcommand == 'newtitles':
            self.import_titles(options)
        elif subcommand == 'resetall':
            self.resetall()
        elif subcommand == 'login':
            self.login_user(options)
        elif subcommand == 'healthcheck':
            self.health_check()

    def add_user(self, username, password):
        try:
            # Check if the user already exists
            user, created = User.objects.get_or_create(username=username)
            
            # If the user was created, set the password
            if created:
                user.set_password(password)
                user.save()
                message = f"User {username} added successfully."
            else:
                # If the user exists, update the password
                user.set_password(password)
                user.save()
                message = f"User {username}'s password updated successfully."
            
            # Output message
            self.stdout.write(message)

        except Exception as e:
            self.stdout.write(f"An error occurred: {e}")

    def see_users(self):
        users = User.objects.all()
        if users:
            self.stdout.write(f"Total Users: {users.count()}\n")
            for user in users:
                self.stdout.write(f"User ID: {user.id}, Username: {user.username}, Password: {user.password}")
        else:
            self.stdout.write("No users found.")
    
    def add_movie(self, options):

        try:
            # Create a new movie instance and save it to the database
            movie = Movies.objects.create(
                tconst=options['tconst'],
                titleType=options['titleType'],
                primaryTitle=options['primaryTitle'],
                originalTitle=options['originalTitle'],
                isAdult=options['isAdult'],
                startYear=options['startYear'],
                endYear=options.get('endYear'),
                runtimeMinutes=options.get('runtimeMinutes'),
                genres=options.get('genres'),
                img_url_asset=options.get('img_url_asset')
            )

            # Output message
            self.stdout.write(f"Movie {movie.primaryTitle} added successfully.")

        except IntegrityError:
            self.stdout.write(f"A movie with tconst {options['tconst']} already exists.")
        except Exception as e:
            self.stdout.write(f"An error occurred: {e}")

    def see_movies(self):
        movies = Movies.objects.all()
        if movies:
            self.stdout.write(f"Total Movies: {movies.count()}\n")
            for movie in movies:
                self.stdout.write(f"ID: {movie.id}, "
                                  f"Tconst: {movie.tconst}, "
                                  f"Type: {movie.titleType}, "
                                  f"Primary Title: {movie.primaryTitle}, "
                                  f"Original Title: {movie.originalTitle}, "
                                  f"Adult: {'Yes' if movie.isAdult else 'No'}, "
                                  f"Start Year: {movie.startYear}, "
                                  f"End Year: {movie.endYear if movie.endYear else 'N/A'}, "
                                  f"Runtime Minutes: {movie.runtimeMinutes if movie.runtimeMinutes else 'N/A'}, "
                                  f"Genres: {movie.genres if movie.genres else 'N/A'}, "
                                  f"Image URL: {movie.img_url_asset if movie.img_url_asset else 'N/A'}")
        else:
            self.stdout.write("No movies found.")

    def add_crew(self, options):
        # Define the path to your JSON file
        json_file_path = 'crews.json'

        # Open the JSON file and read the data
        try:
            with open(json_file_path, 'r') as file:
                crews = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is empty/invalid, start with an empty list
            crews = []

        # Append the new crew data
        new_crew = {
            'tconst': options['tconst'],
            'directors': options['directors'],
            'writers': options['writers']
        }
        crews.append(new_crew)

        # Write the updated data back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(crews, file, indent=4)

        # Output message
        self.stdout.write(f"Crew for movie {options['tconst']} added.")
# ok
    def import_crew_from_tsv(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                directors = row['directors'] if row['directors'] != '\\N' else None
                writers = row['writers'] if row['writers'] != '\\N' else None

                try:
                    crew, created = Crews.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'directors': directors,
                            'writers': writers,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created crew entry {crew}'))
                    else:
                        self.stdout.write(f'Updated crew entry {crew}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating crew entry {tconst}: {e}'))

    def add_episode(self, options):
        # Define the path to your JSON file
        json_file_path = 'episodes.json'

        # Open the JSON file and read the data
        try:
            with open(json_file_path, 'r') as file:
                episodes = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is empty/invalid, start with an empty list
            episodes = []

        # Append the new episode data
        new_episode = {
            'tconst': options['tconst'],
            'parentTconst': options.get('parentTconst', '\\N'),
            'seasonNumber': options.get('seasonNumber', '\\N'),
            'episodeNumber': options.get('episodeNumber', '\\N')
        }
        episodes.append(new_episode)

        # Write the updated data back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(episodes, file, indent=4)

        # Output message
        self.stdout.write(f"Episode for TV show {options['tconst']} added.")
    
    def add_rating(self, options):
        # Define the path to your JSON file
        json_file_path = 'ratings.json'

        # Open the JSON file and read the data
        try:
            with open(json_file_path, 'r') as file:
                ratings = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is empty/invalid, start with an empty list
            ratings = []

        # Append the new rating data
        new_rating = {
            'tconst': options['tconst'],
            'averageRating': options['averageRating'],
            'numVotes': options['numVotes']
        }
        ratings.append(new_rating)

        # Write the updated data back to the JSON file
        with open(json_file_path, 'w') as file:
            json.dump(ratings, file, indent=4)

        # Output message
        self.stdout.write(f"Rating for movie {options['tconst']} added.")
    
    def search_title(self, titlePart):
        # Perform a case-insensitive search for movies with a title containing titlePart
        matching_movies = Movies.objects.filter(originalTitle__icontains=titlePart)
        if matching_movies.exists():
            self.stdout.write(f"Found {matching_movies.count()} movie(s) matching '{titlePart}':")
            for movie in matching_movies:
                self.stdout.write(f"ID: {movie.id}, Title: {movie.originalTitle}")
        else:
            self.stdout.write(f"No movies found matching '{titlePart}'.")

    def search_by_genre(self, genre, min_rating, from_year=None, to_year=None):
        # Filter movies by genre
        movies = Movies.objects.filter(genres__icontains=genre)
        if from_year and to_year:
            movies = movies.filter(startYear__gte=from_year, startYear__lte=to_year)
        
        # Get tconsts of filtered movies
        movie_tconsts = movies.values_list('tconst', flat=True)

        # Filter ratings based on min_rating and the tconsts of the filtered movies
        ratings = Ratings.objects.filter(tconst__in=movie_tconsts, averageRating__gte=min_rating)

        # Now, get the tconsts from the filtered ratings to ensure we only consider movies with the required rating
        rated_movie_tconsts = ratings.values_list('tconst', flat=True)

        # Finally, filter the movies again to get only those with the required ratings
        final_movies = movies.filter(tconst__in=rated_movie_tconsts)

        if final_movies.exists():
            self.stdout.write(f"Found {final_movies.count()} movie(s) for genre '{genre}' with a minimum rating of {min_rating}")
            if from_year and to_year:
                self.stdout.write(f" within the year range {from_year}-{to_year}:")
            for movie in final_movies:
                # Since we already filtered ratings, we can safely assume each movie has at least one rating that matches.
                # However, since Django doesn't directly support joins on non-foreign keys, we access the rating differently:
                rating = Ratings.objects.get(tconst=movie.tconst).averageRating
                self.stdout.write(f"ID: {movie.tconst}, Title: {movie.primaryTitle}, Year: {movie.startYear}, Rating: {rating}")
        else:
            message = f"No movies found for genre '{genre}' with a minimum rating of {min_rating}"
            if from_year and to_year:
                message += f" within the year range {from_year}-{to_year}."
            self.stdout.write(message)

    def show_name(self, nameid):
        try:
            # Retrieve the specified name entry
            name = Names.objects.get(nconst=nameid)

            # Prepare and output the name attributes
            birthYear = 'N/A' if name.birthYear in [None, '\\N'] else name.birthYear
            deathYear = 'N/A' if name.deathYear in [None, '\\N'] else name.deathYear
            profession = 'N/A' if name.primaryProfession in [None, '\\N'] else name.primaryProfession
            knownForTitles = 'N/A' if name.knownForTitles in [None, '\\N'] else name.knownForTitles
            img_url_asset = 'N/A' if name.img_url_asset in [None, '\\N'] else name.img_url_asset

            self.stdout.write("Name ID: " + name.nconst)
            self.stdout.write("Name: " + name.primaryName)
            self.stdout.write("Birth Year: " + birthYear)
            self.stdout.write("Death Year: " + deathYear)
            self.stdout.write("Profession: " + profession)
            self.stdout.write("Known For Titles: " + knownForTitles)
            self.stdout.write("Image URL: " + img_url_asset)

            # Retrieve participations of the name in Principals
            participations = Principals.objects.filter(nconst=nameid)

            if participations.exists():
                self.stdout.write("Participations:")
                for part in participations:
                    # Retrieve the corresponding movie from Movies model
                    movie = Movies.objects.get(tconst=part.tconst)  # Using get() here since tconst is expected to be unique
                    job_display = 'N/A' if part.job in [None, '\\N'] else part.job
                    characters_display = 'N/A' if part.characters in [None, '\\N'] else part.characters
                    self.stdout.write(
                        "Title ID: " + part.tconst + ", " +
                        #"Title: " + movie.primaryTitle + ", " +
                        "Category: " + part.category + ", " #+
                        #"Job: " + job_display + ", " +
                        #"Characters: " + characters_display
                    )
            else:
                self.stdout.write("No participations found for this individual.")

        except Names.DoesNotExist:
            self.stdout.write("No name found with Name ID: " + nameid)
        except Movies.DoesNotExist:
            self.stdout.write("Movie not found for a participation entry.")
        except Exception as e:
            self.stdout.write("An error occurred: " + str(e))

    def search_name(self, name):
        try:
            # Perform a case-insensitive search for names containing the search term
            matching_names = Names.objects.filter(primaryName__icontains=name)
            
            if matching_names.exists():
                self.stdout.write(f"Found {matching_names.count()} name(s) containing '{name}':")
                for name_entry in matching_names:
                    # Replace '\\N' with 'N/A' and ensure the values are strings
                    birthYear = 'N/A' if name_entry.birthYear in [None, '\\N'] else name_entry.birthYear
                    deathYear = 'N/A' if name_entry.deathYear in [None, '\\N'] else name_entry.deathYear
                    profession = 'N/A' if name_entry.primaryProfession in [None, '\\N'] else name_entry.primaryProfession
                    knownForTitles = 'N/A' if name_entry.knownForTitles in [None, '\\N'] else name_entry.knownForTitles

                    self.stdout.write(
                        f"Name ID: {name_entry.nconst}, "
                        f"Name: {name_entry.primaryName}, "
                        f"Birth Year: {birthYear}, "
                        f"Death Year: {deathYear}, "
                        f"Profession: {profession}, "
                        f"Known For Titles: {knownForTitles}"
                    )
            else:
                self.stdout.write(f"No names found containing '{name}'.")
        except Exception as e:
            self.stdout.write(f"An error occurred: {e}")
#
    def import_episode(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                parentTconst = row['parentTconst'] if row['parentTconst'] != '\\N' else None
                seasonNumber = int(row['seasonNumber']) if row['seasonNumber'] != '\\N' else None
                episodeNumber = int(row['episodeNumber']) if row['episodeNumber'] != '\\N' else None

                try:
                    episode, created = Episode.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'parentTconst': parentTconst,
                            'seasonNumber': seasonNumber,
                            'episodeNumber': episodeNumber,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created episode {episode}'))
                    else:
                        self.stdout.write(f'Updated episode {episode}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating episode {tconst}: {e}'))
# ok 
    def import_rating(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                averageRating = float(row['averageRating']) if row['averageRating'] != '\\N' else None
                numVotes = int(row['numVotes']) if row['numVotes'] != '\\N' else None

                try:
                    rating, created = Ratings.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'averageRating': averageRating,
                            'numVotes': numVotes,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created rating {rating}'))
                    else:
                        self.stdout.write(f'Updated rating {rating}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating rating {tconst}: {e}'))
# ok
    def import_principals(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                ordering = int(row['ordering'])
                nconst = row['nconst']
                category = row['category']
                job = None if row['job'] == '\\N' else row['job']
                characters = None if row['characters'] == '\\N' else row['characters']
                img_url_asset = None if 'img_url_asset' not in row or row['img_url_asset'] == '\\N' else row['img_url_asset']

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
                    action = "created" if created else "updated"
                    self.stdout.write(self.style.SUCCESS(f'Successfully {action} principals entry {principal}'))
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error {action} principals entry {tconst}: {e}'))

#
    def import_names(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                nconst = row['nconst']
                primaryName = row['primaryName']
                birthYear = None if row['birthYear'] == "\\N" else int(row['birthYear'])
                deathYear = None if row['deathYear'] == "\\N" else int(row['deathYear'])
                primaryProfession = None if row['primaryProfession'] == "\\N" else row['primaryProfession']
                knownForTitles = None if row['knownForTitles'] == "\\N" else row['knownForTitles']
                img_url_asset = None if 'img_url_asset' not in row or row['img_url_asset'] == "\\N" else row['img_url_asset']

                try:
                    person, created = Names.objects.update_or_create(
                        nconst=nconst,
                        defaults={
                            'primaryName': primaryName,
                            'birthYear': birthYear,
                            'deathYear': deathYear,
                            'primaryProfession': primaryProfession,
                            'knownForTitles': knownForTitles,
                            'img_url_asset': img_url_asset,
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully created person {person}'))
                    else:
                        self.stdout.write(f'Updated person {person}')
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating person {nconst}: {e}'))

# ok
    def import_akas(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r', encoding='utf-8') as file:  # Ensure correct encoding
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                titleId = row['titleId']
                ordering = int(row['ordering'])  # Ensure ordering is an integer
                title = row['title']
                region = None if row['region'] == '\\N' else row['region']
                language = None if row['language'] == '\\N' else row['language']
                types = None if row['types'] == '\\N' else row['types']
                attributes = None if row['attributes'] == '\\N' else row['attributes']
                isOriginalTitle = True if row.get('isOriginalTitle') == '1' else False  # Safely use .get for optional fields

                try:
                    akas_entry, created = Akas.objects.update_or_create(
                        titleId=titleId,
                        ordering=ordering,
                        defaults={
                            'title': title,
                            'region': region,
                            'language': language,
                            'types': types,
                            'attributes': attributes,
                            'isOriginalTitle': isOriginalTitle,
                        }
                    )
                    action = "created" if created else "updated"
                    self.stdout.write(self.style.SUCCESS(f'Successfully {action} Akas entry {akas_entry}'))
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error {action} Akas entry {titleId}: {e}'))
# ok 
    def import_titles(self, options):
        tsv_file = options['filename']
        with open(tsv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                tconst = row['tconst']
                titleType = row['titleType']
                primaryTitle = row['primaryTitle']
                originalTitle = row['originalTitle']
                isAdult = True if row['isAdult'] == '1' else False
                startYear = row['startYear'] if row['startYear'] != '\\N' else None
                endYear = row['endYear'] if row['endYear'] != '\\N' else None
                runtimeMinutes = int(row['runtimeMinutes']) if row['runtimeMinutes'] != '\\N' else None
                genres = row['genres'] if row['genres'] != '\\N' else None
                img_url_asset = row['img_url_asset'] if 'img_url_asset' in row and row['img_url_asset'] != '\\N' else None

                try:
                    movie, created = Movies.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'titleType': titleType,
                            'primaryTitle': primaryTitle,
                            'originalTitle': originalTitle,
                            'isAdult': isAdult,
                            'startYear': startYear,
                            'endYear': endYear,
                            'runtimeMinutes': runtimeMinutes,
                            'genres': genres,
                            'img_url_asset': img_url_asset,
                        }
                    )
                    action = "created" if created else "updated"
                    self.stdout.write(self.style.SUCCESS(f'Successfully {action} movie entry {movie}'))
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error {action} movie entry {tconst}: {e}'))

    def show_title(self, titleid):
        try:
            # Retrieve the specified title entry
            movie = Movies.objects.get(tconst=titleid)

            # Output the movie attributes
            self.stdout.write("Title ID: {}".format(movie.tconst))
            self.stdout.write("Title Type: {}".format(movie.titleType))
            self.stdout.write("Primary Title: {}".format(movie.primaryTitle))
            self.stdout.write("Original Title: {}".format(movie.originalTitle))
            self.stdout.write("Is Adult: {}".format('Yes' if movie.isAdult else 'No'))
            self.stdout.write("Start Year: {}".format(movie.startYear if movie.startYear != '\\N' else 'N/A'))
            self.stdout.write("End Year: {}".format(movie.endYear if movie.endYear != '\\N' else 'N/A'))
            self.stdout.write("Runtime Minutes: {}".format(movie.runtimeMinutes if movie.runtimeMinutes != '\\N' else 'N/A'))
            self.stdout.write("Genres: {}".format(movie.genres if movie.genres != '\\N' else 'N/A'))
            self.stdout.write("Image URL: {}".format(movie.img_url_asset if movie.img_url_asset != '\\N' else 'N/A'))

            # Retrieve the rating for the movie
            rating = Ratings.objects.filter(tconst=titleid).first()
            if rating:
                self.stdout.write("Average Rating: {}".format(rating.averageRating))
                self.stdout.write("Number of Votes: {}".format(rating.numVotes))

            # Retrieve the principals for the movie
            principals = Principals.objects.filter(tconst=titleid)
            if principals.exists():
                self.stdout.write("Principals:")
                for principal in principals:
                    name_entry = Names.objects.filter(nconst=principal.nconst).first()
                    name_display = name_entry.primaryName if name_entry else 'Unknown'
                    self.stdout.write(
                        "Name ID: {}, Name: {}, Category: {}".format(
                            principal.nconst, name_display, principal.category
                        )
                    )
            else:
                self.stdout.write("No principals found for this title.")

        except Movies.DoesNotExist:
            self.stdout.write("No title found with Title ID: {}".format(titleid))
        except Ratings.DoesNotExist:
            self.stdout.write("No ratings found for this title.")
        except Exception as e:
            self.stdout.write("An error occurred: {}".format(str(e)))

    def search_title(self, title_part):
        try:
            # Use the `icontains` filter to perform a case-insensitive search for titles with a matching `originalTitle`
            matching_titles = Movies.objects.filter(originalTitle__icontains=title_part)
            
            if matching_titles.exists():
                self.stdout.write(f"Found {matching_titles.count()} title(s) containing '{title_part}':")
                for movie in matching_titles:
                    # Output the details of each matching movie
                    start_year = 'N/A' if movie.startYear == '\\N' else movie.startYear
                    end_year = 'N/A' if movie.endYear == '\\N' else movie.endYear
                    runtime_minutes = 'N/A' if movie.runtimeMinutes == '\\N' else movie.runtimeMinutes
                    genres = 'N/A' if movie.genres == '\\N' else movie.genres
                    img_url_asset = 'N/A' if movie.img_url_asset == '\\N' else movie.img_url_asset

                    self.stdout.write(
                        f"Title ID: {movie.tconst}, "
                        f"Title Type: {movie.titleType}, "
                        f"Primary Title: {movie.primaryTitle}, "
                        f"Original Title: {movie.originalTitle}, "
                        f"Is Adult: {'Yes' if movie.isAdult else 'No'}, "
                        f"Start Year: {start_year}, "
                        f"End Year: {end_year}, "
                        f"Runtime Minutes: {runtime_minutes}, "
                        f"Genres: {genres}, "
                        f"Image URL: {img_url_asset}"
                    )
            else:
                self.stdout.write(f"No titles found containing '{title_part}'.")
        except Exception as e:
            self.stdout.write(f"An error occurred: {str(e)}")

    # Reset all data and run CLI commands
    def resetall(self):
        # Delete all data from all models
        self.stdout.write("Resetting all data in the database...")

        # Delete data from Movies model
        Movies.objects.all().delete()

        # Delete data from other models (Names, Crews, Episode, Ratings, Principals, Akas)
        # Replace ModelName with the actual model names
        Names.objects.all().delete()
        Crews.objects.all().delete()
        Episode.objects.all().delete()
        Ratings.objects.all().delete()
        Principals.objects.all().delete()
        Akas.objects.all().delete()

        # Run CLI commands
        self.stdout.write("Running CLI commands...")
        self.run_cli_commands()

        self.stdout.write(self.style.SUCCESS("Resetall completed successfully."))

    # Run any necessary CLI commands after resetting the database
    def run_cli_commands(self):
        os.system("python manage.py se2304 newnames --filename truncated_name.basics.tsv")
        os.system("python manage.py se2304 newakas --filename truncated_title.akas.tsv")
        os.system("python manage.py se2304 newtitles --filename truncated_title.basics.tsv")
        os.system("python manage.py se2304 newcrew --filename truncated_title.crew.tsv")
        os.system("python manage.py se2304 newepisode --filename truncated_title.episode.tsv")
        os.system("python manage.py se2304 newprincipals --filename truncated_title.principals.tsv")
        os.system("python manage.py se2304 newratings --filename truncated_title.ratings.tsv")
        
    def login_user(self, options):
        
        # Assuming you're receiving 'username' and 'password' as POST parameters
        username = options['username']
        password = options['password']
        
        # Authenticate the user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # User is authenticated
            token = create_jwt_token({"username" : username, "password" : password})
            mydata = {
                'token' : token
            }

            # Define the URL to which you want to make the POST request
            post_url = 'http://127.0.0.1:9876/ntuaflix_api/application/x-www-form-urlencoded'  # Change this to your actual endpoint URL
            
            # Make the POST request with JSON data
            headers = {'Content-Type': 'application/json'}  # Ensure the server expects JSON
            response = requests.post(post_url, json=mydata, headers=headers)
            
            # Check response status (optional)
            if response.status_code == 200:
                print("Data successfully posted")
                print(mydata)
            else:
                print("Failed to post data. Status code:", response.status_code)
        else:
            print("Authentication failed.")


    def health_check(self):
        # Example of checking database connectivity
        db_conn = connections['default']

        try:
            db_conn.cursor()
            db_status = "OK"
        except OperationalError:
            db_status = "failed"
        
        # Assuming 'connection_name' is a placeholder for your actual connection string's reference or identifier
        connection_name = "Server = http://127.0.0.1:9876/ntuaflix_api; Database=django.db.backends.sqlite3;"  # Be cautious with sensitive info
        if db_status == "OK":
            response = {"status": "OK", "dataconnection": connection_name}
        else:
            response = {"status": "failed", "dataconnection": connection_name}
        print(response)
        #return JsonResponse(response)
