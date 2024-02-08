from django.http import HttpResponse, JsonResponse
from myApp.models import Movies, Ratings
from django.template.loader import render_to_string
from django.template import loader


def title_details(request, tconst):
    try:
        title = Movies.objects.get(tconst=tconst)
        rating_value = None
        template = loader.get_template('title_details.html')
        # Check if the rating with the particular tconst exists
        try:
            rating = Ratings.objects.get(tconst=tconst)
            rating_value = rating.averageRating
        except Ratings.DoesNotExist:
            pass  # If rating does not exist, rating_value will remain None
        
        if title.img_url_asset == "\\N" or not title.img_url_asset:
            image_url = "no image for this movie"
        else:
            baseurl = title.img_url_asset
            width = "w220_and_h330_face"
            image_url = baseurl.replace("{width_variable}", width)

            context = {
        'title': title,
        'image_url': image_url,
        'rating':rating 
    }    
        
        # Prepare the data to be returned as JSON
        titleObject = {
            'titleID':title.tconst,
            'originalTitle': title.primaryTitle,
            'titlePoster': image_url,
            'startYear': title.startYear,
            'endYear':title.endYear,
            'genres': title.genres.split(","),
            'rating': rating_value,
            'numVotes': rating.numVotes

        }

        html_content = render_to_string('title_details.html', titleObject) 
        if request.GET.get('format') == 'json':
          return JsonResponse(titleObject)
        else:       
          return HttpResponse(template.render(titleObject,request))
        
    except Movies.DoesNotExist:
        # Handle case where Movie with given tconst does not exist
        return JsonResponse({'error': 'Movie not found'}, status=404)
