from django.shortcuts import render
from django.http import JsonResponse
from django.template import loader 
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import csv
from .forms import UploadFileForm
from django.core.exceptions import ValidationError
from MySQLdb import IntegrityError
from .forms import *
from .models import *
from django.db import connections
from django.db.utils import OperationalError

from django.db import DatabaseError
from django.contrib.auth.models import User
# from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db import IntegrityError

def home(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render())

def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render())

def bygenre(request):
    # Get parameters from request
    qgenre = request.GET.get('qgenre')
    minrating = request.GET.get('minrating')
    yrFrom = request.GET.get('yrFrom')
    yrTo = request.GET.get('yrTo')

        # Start with all movies
    titles = Movies.objects.all().order_by('primaryTitle')
    
    results_title = "{} Titles".format(qgenre if qgenre else "All")

        # Filter by genre if qgenre is provided
    if qgenre:
        titles = titles.filter(genres__icontains=qgenre)
        results_title = "{} Titles".format(qgenre)
    
    # Filter by year range if yrFrom and/or yrTo are provided
    if yrFrom and yrTo:
        titles = titles.filter(startYear__gte=yrFrom, startYear__lte=yrTo)
        results_title += " From {} to {}".format(yrFrom, yrTo)
    elif yrFrom:
        titles = titles.filter(startYear__gte=yrFrom)
        results_title += " From {}".format(yrFrom)
    elif yrTo:
        titles = titles.filter(startYear__lte=yrTo)
        results_title += " Up to {}".format(yrTo)
    
    # Join with Ratings table and filter by minimum rating if provided
    if minrating:
        titles = titles.filter(tconst__in=Ratings.objects.filter(averageRating__gte=minrating).values_list('tconst', flat=True))
        results_title += " Rated at least {}".format(minrating)
    
    
    # Render the response with the filtered context
    return render(request, 'bygenre.html', {'titles': titles, 'results_title': results_title})

def names(request):
    names = Names.objects.all().order_by('primaryName').values() 
    template = loader.get_template('names.html')
    context = {
        'names': names
    }
    return HttpResponse(template.render(context, request))

def search_names(request):
    name_query = request.GET.get('query', '')
    if name_query:
        names = Names.objects.filter(primaryName__icontains=name_query)
    else:
        names = Names.objects.none()  # Return an empty queryset if no query
    return render(request, 'search_names.html', {'names': names})

def name_details(request, nconst):
  person = Names.objects.get(nconst=nconst)
  template2 = loader.get_template('my_custom_filters.py')

  try:
      personTitles = Principals.objects.filter(nconst=nconst)
      nameTitles = [(f"titleID: {x.tconst}", f"category: {x.category}") for x in personTitles]
  except personTitles.DoesNotExist:
      personTitles = None
      nameTitles = None


  if person.img_url_asset == None :
    full_url = None
  else:
    baseurl = person.img_url_asset
    width = "w220_and_h330_face"
    full_url = baseurl.replace("{width_variable}", width)

  template = loader.get_template('name_details.html')
  
  nameObject = {
    'person': person,
    'nameID':person.nconst,
    'name':person.primaryName,
    'namePoster': full_url,
    'birthYr':person.birthYear,
    'deathYr':person.deathYear,
    'profession':person.primaryProfession,
    'nameTitles':nameTitles
    }
  return HttpResponse(template.render(nameObject, request))

def titles(request):
    titles = Movies.objects.all().order_by('primaryTitle').values() 
    template = loader.get_template('titles.html')
    context = {
        'titles': titles
    }
    return HttpResponse(template.render(context, request))

def search_titles(request):
    title_query = request.GET.get('query', '')
    if title_query:
        movies = Movies.objects.filter(primaryTitle__icontains=title_query)
    else:
        movies = Movies.objects.none()  # Return an empty queryset if no query
    return render(request, 'search_titles.html', {'movies': movies})

def title_details(request, tconst):
  try:  
    title = Movies.objects.get(tconst=tconst)
    template = loader.get_template('title_details.html')
    
    try:
        rating = Ratings.objects.get(tconst=tconst)
        rating_object = (f"Average Rating: {rating.averageRating}",f"Number of Votes: {rating.numVotes}" )
    except Ratings.DoesNotExist:
        rating = None
        rating_object = None

    try:
        akas = Akas.objects.filter(titleId=tconst)
        akas_titles = [(f"title: {entry.title}", f"region: {entry.region}") for entry in akas]

    except Akas.DoesNotExist:
        akas = None
        akas_titles = None
    
    try:
        # Assuming you've already fetched 'principal' as you've shown:
        principal = Principals.objects.filter(tconst=tconst)

# For each principal, fetch the corresponding person from the Names table and create tuples
        principal_id_and_name = []
        for x in principal:
            try:
                name_entry = Names.objects.get(nconst=x.nconst)
                principal_id_and_name.append(( f"nameId: {x.nconst}" ,f"primary person: {name_entry.primaryName}"  ,f"category: {x.category}"))
            except Names.DoesNotExist:
        # Handle the case where no corresponding entry in Names exists
                name_entry = None
                principal_id_and_name.append((x.nconst, x.category, None))

# Now, principal_id_and_name contains tuples of (nconst, category, primaryName) for each matching entry

    except Principals.DoesNotExist:
        principal = None
    
    if title.img_url_asset == None :
        full_url = None
    else:
        baseurl = title.img_url_asset
        width = "w220_and_h330_face"
        full_url = baseurl.replace("{width_variable}", width)
    
    context = {
        'title': title,
        'image_url': full_url,
        'rating':rating 
    }

    titleObject = {
        # 'title':title,
        'titleID':title.tconst,
        'primaryTitle':title.primaryTitle,
        'type':title.titleType,
        'originalTitle': title.originalTitle,
        'titlePoster': full_url,
        'startYear': title.startYear,
        'endYear':title.endYear,
        'genres': title.genres.split(","),
        'titleAkas':akas_titles,
        'principals': principal_id_and_name,
        'rating':rating,
        'rating_object':rating_object
        # 'averageRating': rating.averageRating,
        # 'numVotes':rating.numVotes
    }

    # if request.method == 'GET':
    #return JsonResponse(titleObject)
    # else:
    return HttpResponse(template.render(titleObject,request))
  except Movies.DoesNotExist:
        return JsonResponse({'error': 'Movie not found'}, status=404)
  
def title_details_json(request, tconst):
  try:  
    title = Movies.objects.get(tconst=tconst)
    
    try:
        rating = Ratings.objects.get(tconst=tconst)
        rating_object = (f"Average Rating: {rating.averageRating}",f"Number of Votes: {rating.numVotes}" )
    except Ratings.DoesNotExist:
        rating = None
        rating_object = None

    try:
        akas = Akas.objects.filter(titleId=tconst)
        akas_titles = [(f"title: {entry.title}", f"region: {entry.region}") for entry in akas]

    except Akas.DoesNotExist:
        akas = None
        akas_titles = None
    
    try:
        # Assuming you've already fetched 'principal' as you've shown:
        principal = Principals.objects.filter(tconst=tconst)

# For each principal, fetch the corresponding person from the Names table and create tuples
        principal_id_and_name = []
        for x in principal:
            try:
                name_entry = Names.objects.get(nconst=x.nconst)
                principal_id_and_name.append(( f"nameId: {x.nconst}" ,f"primary person: {name_entry.primaryName}"  ,f"category: {x.category}"))
            except Names.DoesNotExist:
        # Handle the case where no corresponding entry in Names exists
                name_entry = None
                principal_id_and_name.append((x.nconst, x.category, None))

# Now, principal_id_and_name contains tuples of (nconst, category, primaryName) for each matching entry

    except Principals.DoesNotExist:
        principal = None
    
    if title.img_url_asset == None :
        full_url = None
    else:
        baseurl = title.img_url_asset
        width = "w220_and_h330_face"
        full_url = baseurl.replace("{width_variable}", width)
    
    context = {
        'title': title,
        'image_url': full_url,
        'rating':rating 
    }

    titleObject = {
        'titleID':title.tconst,
        'primaryTitle':title.primaryTitle,
        'type':title.titleType,
        'originalTitle': title.originalTitle,
        'titlePoster': full_url,
        'startYear': title.startYear,
        'endYear':title.endYear,
        'genres': title.genres.split(","),
        'titleAkas':akas_titles,
        'principals': principal_id_and_name,
        'rating_object':rating_object
        # 'averageRating': rating.averageRating,
        # 'numVotes':rating.numVotes
    }


    return JsonResponse(titleObject)
  except Movies.DoesNotExist:
        return JsonResponse({'error': 'Movie not found'}, status=404)

from django.template.loader import render_to_string






def upload(request):
    template = loader.get_template('upload.html')
    return HttpResponse(template.render())


# @csrf_exempt  # Disable CSRF token for simplicity, consider CSRF protection for production
@require_http_methods(["GET","POST"])
def upload_title_basics(request):
    success_count = 0
    error_count = 0
    form = UploadFileForm()
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')
    
                for row in reader:
                    tconst = row['tconst']
                    titleType = row['titleType']
                    primaryTitle = row['primaryTitle']
                    originalTitle = row['originalTitle']
                    isAdult = row['isAdult']
                    startYear = row['startYear'] if row['startYear'] != '\\N' else None
                    endYear = row['endYear'] if row['endYear'] != '\\N' else None
                    runtimeMinutes = row['runtimeMinutes'] if row['runtimeMinutes'] != '\\N' else None
                    genres = row['genres'] if row['genres'] != '\\N' else None
                    img_url_asset = row.get('img_url_asset', '\\N')  # Use get to handle missing 'img_url_asset'
        
            
                    created = Movies.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'titleType': titleType,
                            'primaryTitle': primaryTitle,
                            'originalTitle': originalTitle,
                            'isAdult': isAdult,
                            'startYear': int(startYear) if startYear else None,
                            'endYear': int(endYear) if endYear else None,
                            'runtimeMinutes': int(runtimeMinutes) if runtimeMinutes else None,
                            'genres': genres,
                            'img_url_asset': img_url_asset if img_url_asset != '\\N' else None,
                            }
                    )
                    if created:
                        success_count += 1
                    else:
                        success_count += 1  # Αυτό μπορεί να αλλάξει αν θέλετε να κρατάτε διαφορετικό σκορ για updates
            except ValidationError as e:
                    error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)
    return render(request, 'upload_title_basics.html', {'form': form})

def upload_names(request):
    success_count=0
    error_count=0

    form = UploadFileForm()
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        
        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')
    
                for row in reader:
                    nconst = row['nconst']
                    primaryName = row['primaryName']
                    birthYear = row['birthYear'] if row['birthYear'] != '\\N' else None
                    deathYear = row['deathYear'] if row['deathYear'] != '\\N' else None
                    primaryProfession = row['primaryProfession'] if row['primaryProfession'] != '\\N' else None
                    knownForTitles = row['knownForTitles'] if row['knownForTitles'] != '\\N' else None
                    img_url_asset = row.get('img_url_asset', '\\N')  # Use get to handle missing 'img_url_asset'
        
                    created = Names.objects.update_or_create(
                        nconst=nconst,
                        defaults={
                            'primaryName': primaryName,
                            'birthYear': birthYear,
                            'deathYear': deathYear,
                            'primaryProfession': primaryProfession,
                            'knownForTitles': knownForTitles,
                            'img_url_asset': img_url_asset if img_url_asset != '\\N' else None,
                        }
                    )
                    if created:
                        success_count += 1
                    else:
                        success_count += 1  # Αυτό μπορεί να αλλάξει αν θέλετε να κρατάτε διαφορετικό σκορ για updates
            except ValidationError as e:
                    error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)
    return render(request, 'upload_name_basics.html', {'form': form})

def upload_akas(request):
    success_count = 0
    error_count = 0

    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')

                for row in reader:
                    # Parse data from the CSV row
                    titleId = row['titleId']
                    ordering = row['ordering']
                    title = row['title']
                    region = row['region'] if row['region'] !='\\N' else None
                    language = row['language'] if row['language'] !='\\N' else None
                    types = row['types'] if row['types'] !='\\N' else None
                    attributes = row['attributes'] if row['attributes'] !='\\N' else None
                    isOriginalTitle = row['isOriginalTitle']

                    # Create or update Akas instance
                    created = Akas.objects.update_or_create(
                        titleId=titleId,
                        ordering= ordering,
                        defaults={
                            
                            'title': title,
                            'region': region,
                            'language': language,
                            'types': types,
                            'attributes': attributes,
                            'isOriginalTitle': isOriginalTitle,
                        }
                    )
                    if created:
                        success_count += 1
                    else:
                        error_count += 1
            except ValidationError:
                error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)
    return render(request, 'upload_akas.html', {'form': form})

def upload_principals(request):
    success_count = 0
    error_count = 0

    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')

                for row in reader:
                    # Parse data from the CSV row
                    tconst = row['tconst']
                    ordering = row['ordering']
                    nconst = row['nconst']
                    category = row['category']
                    job = row.get('job', '\\N')
                    characters = row.get('characters', '\\N')
                    img_url_asset = row.get('img_url_asset', '\\N')

                    # Create or update Principals instance
                    created = Principals.objects.update_or_create(
                        tconst=tconst,
                        nconst=nconst,
                        defaults={
                            'ordering': ordering,
                            'category': category,
                            'job': job,
                            'characters': characters,
                            'img_url_asset': img_url_asset if img_url_asset != '\\N' else None,
                        }
                    )
                    if created:
                        success_count += 1
                    else:
                        error_count += 1
            except ValidationError:
                error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)

    return render(request, 'upload_principals.html', {'form': form})

def upload_crews(request):
    success_count = 0
    error_count = 0

    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')

                for row in reader:
                    # Parse data from the CSV row
                    tconst = row['tconst']
                    directors = row.get('directors', '\\N')
                    writers = row.get('writers', '\\N')

                    # Create or update Crews instance
                    created = Crews.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'directors': directors,
                            'writers': writers,
                        }
                    )
                    if created:
                        success_count += 1
                    else:
                        error_count += 1
            except ValidationError:
                error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)

    return render(request, 'upload_crews.html', {'form': form})

def upload_episodes(request):
    success_count = 0
    error_count = 0

    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')

                for row in reader:
                    # Parse data from the CSV row
                    tconst = row['tconst']
                    parentTconst = row['parentTconst']
                    seasonNumber = row.get('seasonNumber', '\\N')
                    episodeNumber = row.get('episodeNumber', '\\N')

                    # Create or update Episode instance
                    created = Episode.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'parentTconst': parentTconst,
                            'seasonNumber': seasonNumber,
                            'episodeNumber': episodeNumber,
                        }
                    )
                    if created:
                        success_count += 1
                    else:
                        error_count += 1
            except ValidationError:
                error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)

    return render(request, 'upload_episodes.html', {'form': form})

def upload_ratings(request):
    success_count = 0
    error_count = 0

    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and 'file' in request.FILES:
            file = request.FILES['file']
            try:
                reader = csv.DictReader(file.read().decode('utf-8').splitlines(), delimiter='\t')

                for row in reader:
                    # Parse data from the CSV row
                    tconst = row['tconst']
                    averageRating = row['averageRating']
                    numVotes = row['numVotes']

                    # Create or update Ratings instance
                    created = Ratings.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'averageRating': averageRating,
                            'numVotes': numVotes,
                        }
                    )
                    if created:
                        success_count += 1
                    else:
                        error_count += 1
            except ValidationError:
                error_count += 1

            message = f"File uploaded and processed successfully. Created/Updated: {success_count}, Errors: {error_count}."
            return HttpResponse(message)

    return render(request, 'upload_ratings.html', {'form': form})
def healthcheck(request):
    db_conn = connections['default']
    try:
        db_conn.cursor()
        # Εδώ μπορείτε να προσθέσετε οποιοδήποτε άλλο test θεωρείτε απαραίτητο
        # για να επιβεβαιώσετε τη συνδεσιμότητα με τη βάση δεδομένων ή με ένα API.
        connection_string = "Server= http://127.0.0.1:9876/ntuaflix_api; Database=django.db.backends.sqlite3; User Id=myUsername;Password=myPassword;"
        return JsonResponse({"status": "OK", "dataconnection": connection_string})
    except OperationalError:
        connection_string = "Server= http://127.0.0.1:9876/ntuaflix_api; Database=django.db.backends.sqlite3; User Id=myUsername;Password=myPassword;"
        return JsonResponse({"status": "failed", "dataconnection": connection_string})

# /////////////////////////////// TITLE Names ///////////////////////////////////////

# def ProcessTitleNamesTSV(request, file, reset = False):
#     reader = csv.reader(file, delimiter='\t')

#     ignore_first_line = True
#     for row_number, row in enumerate(reader, start=1):
#         if ignore_first_line:
#             ignore_first_line = False
#             continue
        
#         tconst, titleType, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres, img_url_asset = row
        
#         startYear = None if startYear == '\\N' else startYear
#         endYear = None if endYear == '\\N' else endYear
#         runtimeMinutes = None if runtimeMinutes == '\\N' else runtimeMinutes
#         isAdult = None if isAdult == '\\N' else isAdult
#         genres = None if genres == '\\N' else genres
#         img_url_asset = None if img_url_asset == '\\N' else img_url_asset
        
#         # Use get_or_create to insert a new element
#         # into the table if not already existed
#         try:
#             title_obj, created = Names.objects.get_or_create(
#                 tconst=tconst,
#                 defaults={
#                     'titleType': titleType,
#                     'primaryTitle': primaryTitle,
#                     'originalTitle': originalTitle,
#                     'isAdult': isAdult,
#                     'startYear': startYear,
#                     'endYear': endYear,
#                     'runtimeMinutes': runtimeMinutes,
#                     'genres': genres,
#                     'img_url_asset': img_url_asset,
#                 }
#             )

#             if created:
#                 print(f"Created new record for tconst: {tconst}")
#                 # if reset == False:
#                 #     UploadTitleObject(request, Names.objects.filter(tconst=tconst))
#             else:
#                 print(f"Record for tconst {tconst} already exists, skipping.")

#         except Names.MultipleObjectsReturned:
#             print(f"Multiple records found for tconst: {tconst}, skipping.")

#         print(f"Processed row number: {row_number-1}")
#     return row_number-1

# def UploadTitleNames(request):
#     if request.method == 'POST':
#         superuser_token = User.objects.filter(is_superuser=True).values_list('auth_token', flat=True).first()
#         token = request.META.get('HTTP_AUTHORIZATION')
#         print(superuser_token)
#         print(token)

#         # Check if the authenticated user is a superuser
#         if token == superuser_token:
#             form = BasicForm(request.POST, request.FILES)
#             if form.is_valid():
#                 file = form.cleaned_data['tsv_file']
#                 decoded_file = file.read().decode('utf-8').splitlines()
#                 rows = ProcessTitleNamesTSV(request, decoded_file)
#                 return JsonResponse({'status': 'success', 'processed_rows': rows})
#             else:
#                 return JsonResponse({'status': 'error', 'message': 'Form is not valid'}, status=400)
#         else:
#             return JsonResponse({'detail': 'Permission denied. You don\'t have administrator privileges.'}, status=403)
#     else:
#         form = BasicForm()
#         return render(request, 'upload.html', {'form': form})


# def ResetTitleNames(request):
#     Names.objects.all().delete()
#     specific_file_path = '..\\..\\Database\\Data\\truncated_title.Names.tsv'
#     with open(specific_file_path, 'r', encoding='utf-8') as file:
#         rows = ProcessTitleNamesTSV(request, file, True)
#     return JsonResponse({'status': 'success', 'processed_rows': rows})