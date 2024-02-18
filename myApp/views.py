from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.template import loader 
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import csv, json, re
from .forms import UploadFileForm
from django.core.exceptions import ValidationError
from .forms import *
from .models import *
from django.db import connections
from django.db.utils import OperationalError
from django.db.models import F, FloatField
from django.db.models.functions import Cast
import os
from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib import messages
import requests
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.shortcuts import render, redirect




def home(request):
    if 'user' in request.session:
        current_user = request.session['user']
        top_rated = None

            # If averageRating is still a CharField, convert it to float for ordering
        top_ratings = Ratings.objects.annotate(
            numeric_rating=Cast('averageRating', FloatField())
        ).order_by('-numeric_rating')[:10]

        # Assuming Movies and Ratings share the same 'tconst' for identification
        movies = Movies.objects.filter(tconst__in=[rating.tconst for rating in top_ratings])
        titles = []

        for movie in movies:
            titles.append((movie.tconst,movie.primaryTitle))

        liked_movies_tconsts = Liked.objects.filter(username=current_user).values_list('tconst', flat=True)
        liked_movies = Movies.objects.filter(tconst__in=liked_movies_tconsts)
        genres = set()
        for movie in liked_movies:
            genres.update(movie.genres.split(','))

        top_movies_per_genre = {}

        for genre in genres:
            # Filter movies that contain the genre and are liked by the user
            genre_movies_tconsts = Movies.objects.filter(
                genres__contains=genre,
            ).values_list('tconst', flat=True)



            # Get top 3 rated movies in this genre
            top_rated = Ratings.objects.filter(
                tconst__in=genre_movies_tconsts
            ).annotate(
                numeric_rating=Cast('averageRating', FloatField())
            ).order_by('-numeric_rating')[:3]
                
            top_movies_per_genre[genre] = Movies.objects.filter(tconst__in=[rating.tconst for rating in top_rated])
        
        # Assuming 'current_user' holds the username of the logged-in user
        watchlist_tconsts = Watchlist.objects.filter(username=current_user).values_list('tconst', flat=True)
        watchlist_movies = Movies.objects.filter(tconst__in=watchlist_tconsts)


        context = {
            'titles': titles,
            'current_user': current_user,
            'top_movies_per_genre': top_movies_per_genre,
            'top_rated': top_rated,
            'watchlist_movies': watchlist_movies,
        }
        return render(request, 'home.html', context)
    else:
        message = 'Please enter a valid Username or Password.'
        context = {
        'message' : message,
        }
        return render(request,'login.html', context)

def login(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        pwd = request.POST.get('password')

        check_user = authenticate(username=uname, password=pwd)
        if check_user:
            request.session['user'] = uname

            # Create a JWT token
            payload = {
                'username': uname,
            }
            jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            
            
            # URL to send the POST request to
            url = 'http://127.0.0.1:9876/ntuaflix_api/application/x-www-form-urlencoded'
            
            # Headers for the POST request
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Content-Type': 'application/json',
            }
            
            # Data for the POST request (if any), as a dictionary
            data = {
                'token': jwt_token
            }
            
            # Send the POST request
            try:
                response = requests.post(url, headers=headers, json=data)
                # Handle the response if needed
                print(response.text)  # For debugging
            except Exception as e:
                # Handle any exceptions, such as connection errors
                print(e)  # For debugging
            
            return redirect('home')
        else:
            message = 'Please enter a valid Username or Password.'
            context = {
                'message': message,
            }
            return render(request, 'login.html', context)

    return render(request, 'login.html')

def logout(request):
    # Check if the request method is POST
    if request.method == 'POST':
        # End the user session
        request.session.flush()
        # Optionally, you can redirect the user to a login page or a home page after logging out
        return redirect('login')  # Assuming 'login' is the name of your login view's URL

    # If the request method is not POST, render the logout confirmation page
    template = loader.get_template('logout.html')
    return HttpResponse(template.render({}, request))

def bygenre(request):
    if 'user' in request.session:
        current_user = request.session['user']

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

def bygenre_json(request):
     # Get parameters from request
    qgenre = request.GET.get('qgenre')
    minrating = request.GET.get('minrating')
    yrFrom = request.GET.get('yrFrom')
    yrTo = request.GET.get('yrTo')

    if yrFrom and yrTo:
        try:
            yrFrom = int(yrFrom)
            yrTo = int(yrTo)
            if yrTo < yrFrom:
                # If yrTo is less than yrFrom, return a 400 Bad Request response
                return JsonResponse({'error': 'yrTo must not be less than yrFrom'}, status=400)
        except ValueError:
            # In case yrFrom or yrTo are not valid integers
            return JsonResponse({'error': 'Invalid year format'}, status=400)

    # Start with all movies ordered by title
    titles = Movies.objects.all().order_by('primaryTitle')

    # Filter by genre, year range, and join with Ratings if minrating is provided
    if qgenre:
        titles = titles.filter(genres__icontains=qgenre)
    if yrFrom and yrTo:
        titles = titles.filter(startYear__gte=yrFrom, startYear__lte=yrTo)
    elif yrFrom:
        titles = titles.filter(startYear__gte=yrFrom)
    elif yrTo:
        titles = titles.filter(startYear__lte=yrTo)
    if minrating:
        titles = titles.filter(tconst__in=Ratings.objects.filter(averageRating__gte=minrating).values_list('tconst', flat=True))

    data_format = request.GET.get('format', 'json').lower()

    titles_list = []
    for title in titles:
        try:
            rating = Ratings.objects.get(tconst=title.tconst)
            rating_object = {
                "Average Rating": rating.averageRating,
                "Number of Votes": rating.numVotes
            }
        except Ratings.DoesNotExist:
            rating_object = None

        akas_titles = list(Akas.objects.filter(titleId=title.tconst).values('title', 'region'))
        principals = Principals.objects.filter(tconst=title.tconst)
        principal_id_and_name = [{
            "nameId": principal.nconst,
            "primaryName": Names.objects.get(nconst=principal.nconst).primaryName if Names.objects.filter(nconst=principal.nconst).exists() else None,
            "category": principal.category
        } for principal in principals]

        full_url = None  # Replace with logic to construct full URL if available

        titleObject = {
            'title': title.primaryTitle,
            'titleID': title.tconst,
            'primaryTitle': title.primaryTitle,
            'type': title.titleType,
            'originalTitle': title.originalTitle,
            'titlePoster': full_url,  # Assume logic to define or replace this
            'startYear': title.startYear,
            'endYear': title.endYear,
            'genres': title.genres.split(",") if title.genres else [],
            'titleAkas': akas_titles,
            'principals': principal_id_and_name,
            'rating_object': rating_object
        }
        titles_list.append(titleObject)
    
    # If the CSV format is requested, create a CSV response
    if data_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="movies.csv"'
        writer = csv.writer(response)

        # Write the header
        writer.writerow(['title', 'titleID', 'primaryTitle', 'type', 'originalTitle',
                         'startYear', 'endYear', 'genres', 'titleAkas', 'principals', 'averageRating', 'numVotes'])

        # Write the data rows
        for title in titles_list:
            writer.writerow([title['title'],
                             title['titleID'],
                             title['primaryTitle'],
                             title['type'],
                             title['originalTitle'],
                             title['startYear'],
                             title['endYear'],
                             ';'.join(title['genres']),
                             ';'.join([aka['title'] for aka in title['titleAkas']]),
                             ';'.join([f"{principal['nameId']} - {principal['primaryName']} - {principal['category']}"
                                       for principal in title['principals']]),
                             title['rating_object']['Average Rating'] if title['rating_object'] else '',
                             title['rating_object']['Number of Votes'] if title['rating_object'] else ''])
        return response


    if not titles_list:
        return JsonResponse({'movies': titles_list}, status=204) 
    return JsonResponse({'movies': titles_list}, status=200)

def names(request):
    if 'user' in request.session:
        current_user = request.session['user']

        names = Names.objects.all().order_by('primaryName').values() 
        template = loader.get_template('names.html')
        context = {
            'names': names
        }
        return HttpResponse(template.render(context, request))

def search_names(request):
    if 'user' in request.session:
        current_user = request.session['user']

        name_query = request.GET.get('query', '')

        if name_query:
            names = Names.objects.filter(primaryName__icontains=name_query)
        else:
            names = Names.objects.none()  # Return an empty queryset if no query
        return render(request, 'search_names.html', {'names': names})

def search_names_json(request):
    name_query = request.GET.get('query', '')
    data_format = request.GET.get('format', 'json').lower()

    if re.search(r'\d', name_query):  # This regex looks for any digit in the query
        return JsonResponse({'error': 'Name must not contain numbers'}, status=400)

    if name_query:
        names = Names.objects.filter(primaryName__icontains=name_query)
    else:
        names = Names.objects.none()  # Return an empty queryset if no query
    
    names_list = []
    for person in names:
        person = Names.objects.get(nconst=person.nconst)
        try:
            personTitles = Principals.objects.filter(nconst=person.nconst)
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

        nameObject = {
            'person': person.primaryName,  # Use primaryName for the 'person' field
            'nameID': person.nconst,
            'name': person.primaryName,
            'namePoster': full_url,
            'birthYr': person.birthYear,
            'deathYr': person.deathYear,
            'profession': person.primaryProfession.split(",") if person.primaryProfession else [],
            'nameTitles': nameTitles,
        }
        names_list.append(nameObject)
    
    
    
    if not names_list:
        return JsonResponse({'names': names_list}, status=204) 
    return JsonResponse({'names': names_list}, status=200)

def name_details(request, nconst):
  if 'user' in request.session:
    current_user = request.session['user']
        
    person = Names.objects.get(nconst=nconst)
    template2 = loader.get_template('my_custom_filters.py')

    try:
            personTitles = Principals.objects.filter(nconst=nconst)
            nameTitles = []
            for x in personTitles:
                movie = Movies.objects.get(tconst=x.tconst)  # Get the corresponding movie
                nameTitles.append((movie.tconst,movie.primaryTitle))
                for title in nameTitles:
                    print(title[0])
                print(nameTitles)  # Append title as string
    except Movies.DoesNotExist:
            nameTitles = []

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
        'profession':person.primaryProfession.split(","),
        'nameTitles':nameTitles
        }
    return HttpResponse(template.render(nameObject, request))

def name_details_json(request, nconst):
  person = Names.objects.get(nconst=nconst)

  if not person:
    return JsonResponse({'person': nameObject}, status=204)

  try:
      personTitles = Principals.objects.filter(nconst=nconst)
      nameTitles = [{f"titleID": x.tconst, f"category": x.category} for x in personTitles]
  except personTitles.DoesNotExist:
      personTitles = None
      nameTitles = None


  if person.img_url_asset == None :
    full_url = None
  else:
    baseurl = person.img_url_asset
    width = "w220_and_h330_face"
    full_url = baseurl.replace("{width_variable}", width)
  
  nameObject = {
    'nameID':person.nconst,
    'name':person.primaryName,
    'namePoster': full_url,
    'birthYr':person.birthYear,
    'deathYr':person.deathYear,
    'profession':person.primaryProfession.split(","),
    'nameTitles':nameTitles
    }

  data_format = request.GET.get('format', 'json').lower()

  if data_format == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{person.primaryName}_details.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name ID', 'Name', 'Poster URL', 'Birth Year', 'Death Year', 'Profession', 'Known For Titles'])

        professions = '; '.join(nameObject['profession'])
        known_for_titles = '; '.join([f"{title['titleID']} ({title['category']})" for title in nameObject['nameTitles']])
        writer.writerow([nameObject['nameID'], nameObject['name'], nameObject['namePoster'], nameObject['birthYr'], nameObject['deathYr'], professions, known_for_titles])

        return response

  return JsonResponse(nameObject, safe=False, json_dumps_params={'ensure_ascii': False})

def titles(request):
    if 'user' in request.session:
        current_user = request.session['user']

        titles = Movies.objects.all().order_by('primaryTitle').values() 
        template = loader.get_template('titles.html')
        context = {
            'titles': titles
        }
        return HttpResponse(template.render(context, request))


def search_titles(request):
    if 'user' in request.session:
        current_user = request.session['user']

        title_query = request.GET.get('query', '')
        if title_query:
            movies = Movies.objects.filter(primaryTitle__icontains=title_query)
        else:
            movies = Movies.objects.none()  # Return an empty queryset if no query
        return render(request, 'search_titles.html', {'movies': movies})

def search_titles_json(request):
    title_query = request.GET.get('query', '')
    if title_query:
        movies = Movies.objects.filter(primaryTitle__icontains=title_query)
        print(movies)
    else:
        movies = Movies.objects.none()  # Return an empty queryset if no query
    
    titles_list = []
    for title in movies:  
            title = Movies.objects.get(tconst=title.tconst)
            template = loader.get_template('title_details.html')
            
            try:
                rating = Ratings.objects.get(tconst=title.tconst)
                rating_object = (f"Average Rating: {rating.averageRating}",f"Number of Votes: {rating.numVotes}" )
            except Ratings.DoesNotExist:
                rating = None
                rating_object = None

            try:
                akas = Akas.objects.filter(titleId=title.tconst)
                akas_titles = [(f"title: {entry.title}", f"region: {entry.region}") for entry in akas]

            except Akas.DoesNotExist:
                akas = None
                akas_titles = None
            
            try:
                # Assuming you've already fetched 'principal' as you've shown:
                principal = Principals.objects.filter(tconst=title.tconst)

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
    

            titleObject = {
                'title': title.primaryTitle,  # Use primaryTitle for the 'title' field
                'titleID': title.tconst,
                'primaryTitle': title.primaryTitle,
                'type': title.titleType,
                'originalTitle': title.originalTitle,  # This is the original title part
                'titlePoster': full_url,
                'startYear': title.startYear,
                'endYear': title.endYear,
                'genres': title.genres.split(",") if title.genres else [],
                'titleAkas': akas_titles,
                'principals': principal_id_and_name,
                # 'rating': rating,
                'rating_object': rating_object
            }
            titles_list.append(titleObject)
    return JsonResponse({'movies': titles_list})
@csrf_exempt
def title_details(request, tconst):
  if 'user' in request.session:
    current_user = request.session['user']

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
            akas_titles = [(entry.title,entry.region,entry.titleId) for entry in akas]

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
                    principal_id_and_name.append((name_entry.primaryName,x.category,x.nconst))
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
            'title':title,
            'titleID':title.tconst,
            'primaryTitle':title.primaryTitle,
            'type':title.titleType,
            'originalTitle': title.originalTitle,
            'titlePoster': full_url,
            'startYear': title.startYear,
            'endYear':title.endYear,
            'genres': title.genres,
            'titleAkas':akas_titles,
            'principals': principal_id_and_name,
            'rating':rating,
            'rating_object':rating_object,
            'current_user': current_user,
            # 'averageRating': rating.averageRating,
            # 'numVotes':rating.numVotes
        }
        
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'like':
                tconst = title.tconst
                username = current_user
                
                if Disliked.objects.filter(username=current_user, tconst=title.tconst).exists():
                    Disliked.objects.filter(username=current_user, tconst=title.tconst).delete()
                    print("Dislike removed.")

                if not Liked.objects.filter(username=current_user, tconst=title.tconst).exists():
                    like = Liked.objects.create(username=username, tconst=tconst)
                    messages.success(request, f"Movie liked: {title.primaryTitle}")
                else:
                    messages.success(request, f"Movie already liked: {title.primaryTitle}")
            if action == 'dislike':
                tconst = title.tconst
                username = current_user

                if Liked.objects.filter(username=current_user, tconst=title.tconst).exists():
                    Liked.objects.filter(username=current_user, tconst=title.tconst).delete()
                    print("Like removed.")

                if not Disliked.objects.filter(username=current_user, tconst=title.tconst).exists():
                    dislike = Disliked.objects.create(username=username, tconst=tconst)
                    messages.success(request, f"Movie disliked: {title.primaryTitle}")
                else:
                    messages.success(request, f"Movie already disliked: {title.primaryTitle}")
                # Redirect back to the same page to refresh and show the updated state
                return redirect(request.path)
            if action == 'remove':
                tconst = title.tconst
                username = current_user

                if Liked.objects.filter(username=current_user, tconst=title.tconst).exists():
                    Liked.objects.filter(username=current_user, tconst=title.tconst).delete()
                    messages.success(request, f"Movie like remove: {title.primaryTitle}")
                
                elif Disliked.objects.filter(username=current_user, tconst=title.tconst).exists():
                    Disliked.objects.filter(username=current_user, tconst=title.tconst).delete()
                    messages.success(request, f"Movie dislike remove: {title.primaryTitle}")
            if action == 'watchlist_add':
                tconst= title.tconst
                username =current_user

                if not Watchlist.objects.filter(username=current_user, tconst=title.tconst).exists():
                     Watchlist.objects.create(username=username, tconst=tconst)
                     messages.success(request, f"Movie was added to watchlist: {title.primaryTitle}")

            if action == 'watchlist_remove':
                tconst= title.tconst
                username =current_user


                if Watchlist.objects.filter(username=current_user, tconst=title.tconst).exists():
                   Watchlist.objects.filter(username=current_user, tconst=title.tconst).delete()
                   messages.success(request, f"Movie was removed from watchlist: {title.primaryTitle}")
                   
        return HttpResponse(template.render(titleObject,request))
    except Movies.DoesNotExist:
            return JsonResponse({'error': 'Movie not found'}, status=404)
  
def title_details_json(request, tconst):
  try:  
    title = Movies.objects.get(tconst=tconst)
    
    
    genre_list=title.genres.split(",")
    formatted_genres = [f"genreTitle: {genre.strip()}" for genre in genre_list]

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
        'type':title.titleType,
        'originalTitle': title.originalTitle,
        'titlePoster': full_url,
        'startYear': title.startYear,
        'endYear':title.endYear,
        'genres': formatted_genres,
        'titleAkas':akas_titles,
        'principals': principal_id_and_name,
        'rating_object':rating_object
        # 'averageRating': rating.averageRating,
        # 'numVotes':rating.numVotes
    }


    return JsonResponse(titleObject)
  except Movies.DoesNotExist:
        return JsonResponse({'error': 'Movie not found'}, status=404)

def upload(request):
    if 'user' in request.session:
        # Assuming 'user' session key holds the username
        username = request.session['user']
        try:
            user = User.objects.get(username=username)
            is_superuser = user.is_superuser
        except User.DoesNotExist:
            # Handle the case where the user does not exist if necessary
            is_superuser = False

        context = {'is_superuser': is_superuser}
        return render(request, 'upload.html', context)
    else:
        # Redirect to login or another appropriate page if the user is not in session
        return redirect('/login/')  # Adjust the redirect URL as needed

@require_http_methods(["GET","POST"])
def upload_title_basics(request):
    if 'user' in request.session:
        current_user = request.session['user']

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
    if 'user' in request.session:
        current_user = request.session['user']

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
    if 'user' in request.session:
        current_user = request.session['user']

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
    if 'user' in request.session:
        current_user = request.session['user']

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
    if 'user' in request.session:
        current_user = request.session['user']

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
    if 'user' in request.session:
        current_user = request.session['user']
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
    if 'user' in request.session:
        current_user = request.session['user']

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
    if 'user' in request.session:
        current_user = request.session['user']

        db_conn = connections['default']
        try:
            db_conn.cursor()
            # Additional checks can be added here
            connection_string = "Server=http://127.0.0.1:9876/ntuaflix_api; Database=django.db.backends.sqlite3; User Id=myUsername;Password=myPassword;"
            return render(request, 'healthcheck.html', {"status": "OK", "dataconnection": connection_string})
        except OperationalError:
            connection_string = "Server=http://127.0.0.1:9876/ntuaflix_api; Database=django.db.backends.sqlite3; User Id=myUsername;Password=myPassword;"
            return render(request, 'healthcheck.html', {"status": "Failed", "dataconnection": connection_string})

def healthcheck_json(request):
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

@require_http_methods(["GET"])
def reset_title_basics(request, file_path):
    success_count = 0
    error_count = 0
    
    # Handling file from a given file path (for automated reset and repopulation)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    # Extracting data from each row
                    tconst = row['tconst']
                    titleType = row['titleType']
                    primaryTitle = row['primaryTitle']
                    originalTitle = row['originalTitle']
                    isAdult = row['isAdult']
                    startYear = row['startYear'] if row['startYear'] != '\\N' else None
                    endYear = row['endYear'] if row['endYear'] != '\\N' else None
                    runtimeMinutes = row['runtimeMinutes'] if row['runtimeMinutes'] != '\\N' else None
                    genres = row['genres'] if row['genres'] != '\\N' else None
                    img_url_asset = row.get('img_url_asset', None)  # Assuming 'None' for missing img_url_asset
                    
                    # Creating or updating the Movies entry
                    Movies.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'titleType': titleType,
                            'primaryTitle': primaryTitle,
                            'originalTitle': originalTitle,
                            'isAdult': isAdult == '1',
                            'startYear': int(startYear) if startYear else None,
                            'endYear': int(endYear) if endYear else None,
                            'runtimeMinutes': int(runtimeMinutes) if runtimeMinutes else None,
                            'genres': genres,
                            'img_url_asset': img_url_asset,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")  # Optionally log the error

        message = f"Title Basics reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"
    
    return HttpResponse(message)

@require_http_methods(["GET"])
def reset_name_basics(request, file_path):
    success_count = 0
    error_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    # Extracting data from each row
                    nconst = row['nconst']
                    primaryName = row['primaryName']
                    birthYear = row['birthYear'] if row['birthYear'] != '\\N' else None
                    deathYear = row['deathYear'] if row['deathYear'] != '\\N' else None
                    primaryProfession = row['primaryProfession'] if row['primaryProfession'] != '\\N' else None
                    knownForTitles = row['knownForTitles'] if row['knownForTitles'] != '\\N' else None
                    img_url_asset = row.get('img_url_asset', None)
                    
                    # Creating or updating the Names entry
                    Names.objects.update_or_create(
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
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")

        message = f"Name Basics reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"
    
    return HttpResponse(message)

@require_http_methods(["GET"])
def reset_title_crews(request, file_path):
    success_count = 0
    error_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    tconst = row['tconst']
                    directors = row['directors'] if row['directors'] != '\\N' else None
                    writers = row['writers'] if row['writers'] != '\\N' else None
                    
                    Crews.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'directors': directors,
                            'writers': writers,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")

        message = f"Crews reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"

    return HttpResponse(message)

@require_http_methods(["GET"])
def reset_title_episode(request, file_path):
    success_count = 0
    error_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    tconst = row['tconst']
                    parentTconst = row['parentTconst']
                    seasonNumber = row['seasonNumber'] if row['seasonNumber'] != '\\N' else None
                    episodeNumber = row['episodeNumber'] if row['episodeNumber'] != '\\N' else None

                    Episode.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'parentTconst': parentTconst,
                            'seasonNumber': seasonNumber,
                            'episodeNumber': episodeNumber,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")

        message = f"Episodes reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"

    return HttpResponse(message)

@require_http_methods(["GET"])
def reset_title_ratings(request, file_path):
    success_count = 0
    error_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    tconst = row['tconst']
                    averageRating = row['averageRating']
                    numVotes = row['numVotes']
                    
                    Ratings.objects.update_or_create(
                        tconst=tconst,
                        defaults={
                            'averageRating': averageRating,
                            'numVotes': numVotes,
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")

        message = f"Ratings reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"

    return HttpResponse(message)

@require_http_methods(["GET"])
def reset_title_akas(request, file_path):
    success_count = 0
    error_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    titleId = row['titleId']
                    ordering = row['ordering']
                    title = row['title']
                    region = row['region'] if row['region'] != '\\N' else None
                    language = row['language'] if row['language'] != '\\N' else None
                    types = row['types'] if row['types'] != '\\N' else None
                    attributes = row['attributes'] if row['attributes'] != '\\N' else None
                    isOriginalTitle = row['isOriginalTitle'] == '1'

                    # Creating or updating the Akas entry
                    Akas.objects.update_or_create(
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
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")

        message = f"Akas reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"
    
    return HttpResponse(message)

@require_http_methods(["GET"])
def reset_title_principals(request, file_path):
    success_count = 0
    error_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                try:
                    tconst = row['tconst']
                    ordering = row['ordering']
                    nconst = row['nconst']
                    category = row['category']
                    job = row['job'] if row['job'] != '\\N' else None
                    characters = row['characters'] if row['characters'] != '\\N' else None
                    img_url_asset = row.get('img_url_asset', None)

                    # Creating or updating the Principals entry
                    Principals.objects.update_or_create(
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
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {e}")

        message = f"Principals reset successfully. Created/Updated: {success_count}, Errors: {error_count}."
    except FileNotFoundError:
        message = "File not found."
    except Exception as e:
        message = f"Error processing file: {e}"
    
    return HttpResponse(message)

def resetall(request):
    if 'user' in request.session:
        current_user = request.session['user']

        # Delete data from Movies model
        Movies.objects.all().delete()
        movies_file_path = os.path.join(settings.BASE_DIR, 'truncated_title.basics.tsv')
        title_basics_response = reset_title_basics(request, file_path=movies_file_path)

        if isinstance(title_basics_response, HttpResponse):
            title_basics_message = title_basics_response.content.decode()
            print(title_basics_message)
        else:
            title_basics_message = "Unexpected response type."

        Names.objects.all().delete()
        names_file_path = os.path.join(settings.BASE_DIR, 'truncated_name.basics.tsv')
        name_basics_response = reset_name_basics(request, file_path=names_file_path)

        if isinstance(name_basics_response, HttpResponse):
            name_basics_message = name_basics_response.content.decode()
            print(name_basics_message)
        else:
            name_basics_message = "Unexpected response type."

        Crews.objects.all().delete()
        crews_file_path = os.path.join(settings.BASE_DIR, 'truncated_title.crew.tsv')
        title_crews_response = reset_title_crews(request, file_path=crews_file_path)

        if isinstance(title_crews_response, HttpResponse):
            title_crews_message = title_crews_response.content.decode()
            print(title_crews_message)
        else:
            title_crews_message = "Unexpected response type."
        
        Episode.objects.all().delete()
        episodes_file_path = os.path.join(settings.BASE_DIR, 'truncated_title.episode.tsv')
        title_episode_response = reset_title_episode(request, file_path=episodes_file_path)

        if isinstance(title_episode_response, HttpResponse):
            title_episode_message = title_episode_response.content.decode()
            print(title_episode_message)
        else:
            title_episode_message = "Unexpected response type."

        Ratings.objects.all().delete()
        ratings_file_path = os.path.join(settings.BASE_DIR, 'truncated_title.ratings.tsv')
        title_ratings_response = reset_title_ratings(request, file_path=ratings_file_path)

        if isinstance(title_ratings_response, HttpResponse):
            title_ratings_message = title_ratings_response.content.decode()
            print(title_ratings_message)
        else:
            title_ratings_message = "Unexpected response type."

        Akas.objects.all().delete()
        akas_file_path = os.path.join(settings.BASE_DIR, 'truncated_title.akas.tsv')
        title_akas_response = reset_title_akas(request, file_path=akas_file_path)

        if isinstance(title_akas_response, HttpResponse):
            title_akas_message = title_akas_response.content.decode()
            print(title_akas_message)
        else:
            title_akas_message = "Unexpected response type."
        
        Principals.objects.all().delete()
        principals_file_path = os.path.join(settings.BASE_DIR, 'truncated_title.principals.tsv')
        title_principals_response = reset_title_principals(request, file_path=principals_file_path)

        if isinstance(title_principals_response, HttpResponse):
            title_principals_message = title_principals_response.content.decode()
            print(title_principals_message)
        else:
            title_akas_message = "Unexpected response type."

            
            # Principals.objects.all().delete()
        return render(request, 'resetall.html', 
                    {'title_basics_message': title_basics_message,
                        'name_basics_message': name_basics_message,
                        'title_crews_message': title_crews_message,
                        'title_episode_message': title_episode_message,
                        'title_ratings_message': title_ratings_message,
                        "title_akas_message": title_akas_message,
                        "title_principals_message": title_principals_message
                        })

@csrf_exempt  # Disable CSRF token for this example. Use cautiously.
@require_http_methods(["POST"])  # Ensure that only POST requests are accepted.
def user_endpoint_view(request):
    try:
        # Parse the JSON data from request body
        data = json.loads(request.body)
        
        # Example: Process the data as needed
        username = data.get('username')
        password = data.get('password')
        # Add your logic here to handle the username and password or any other data
        
        return JsonResponse({'message': 'Data processed successfully', 'data': data})
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')
    except KeyError:
        # Handle missing keys if necessary
        return HttpResponseBadRequest('Missing required data')