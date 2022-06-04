#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate

from sqlalchemy import and_, func
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
db.init_app(app)
app.config.from_object('config')
moment = Moment(app)
migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  try:
    cities = Venue.query.distinct(Venue.city, Venue.state).all();
    data=[]
    for city in cities:
      city_info = {
        'city':city.city,
        'state':city.state
      }
      venues = Venue.query.filter_by(city=city.city, state=city.state)
      venue_list = []
      for venue in venues:
        upcoming_show = Show.query.filter(Show.start_time > datetime.today(), Show.venue_id==venue.id).count()
        venue_list.append({
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': upcoming_show
        })
      city_info['venues'] = venue_list
      data.append(city_info)
  except Exception as err:
    print('Error!!! ' + str(err))
  finally:
    return render_template('pages/venues.html', areas=data)
  

  # TODO: replace with real venues data.
  #status: done and reviewed
  


  # Previous venues page code with comments before review:

  # #declare the data variable as an empty list
  # data =[]
  # # use SQLAlchemy to query the Venue model to get a distinct list of venues
  # cities = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  # #use a for loop to iterate through the venues
  # for city in cities:
  #   cityinfo = dict(city)
  #   #further query for further filtering
  #   venues = db.session.query(Venue.id,Venue.name).filter(
  #     and_(
  #       Venue.city == city.city,
  #       Venue.state == city.state
  #     )
  #   ).all()
  #   cityinfo['venues'] = [{
  #     'id' : v.id,
  #     'name' : v.name,
  #     'num_upcoming_shows' : Show.query.filter(Show.venue_id == v.id).count()
  #   } for v in venues]
  #   #append query results to the empty list variable
  #   data.append(cityinfo)
  # #return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # status: done
  #get the search term and query the Venue model, filter results like the search term
  search_term = request.form.get('search_term', '')
  results = Venue.query.filter(func.lower(Venue.name).like(f'%{search_term.lower()}%')).all()
  #count the results like the search term and append the names like the search term
  response = {
    "count": len(results),
    "data": [{
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": Show.query.filter(Show.start_time > datetime.now(), Show.venue_id == result.id).count()
    } for result in results]
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # TODO: replace with real venue data from the venues table, using venue_id
  #status: Done
  # query the venue table using the venue id
  venue_data = Venue.query.filter_by(id=venue_id).first()
  # use SQLAlchemy ORM to query, join and filter the upcoming shows as > than current datetime.today
  upcoming_show = db.session.query(Show.start_time, Artist.id, Artist.name, Artist.image_link).join(Venue, Artist).filter(Show.start_time > datetime.today(),Show.venue_id==venue_data.id).all()
  # use SQLAlchemy ORM to query,join and filter the past shows as < the datetime.today
  past_show = db.session.query(Show.start_time, Artist.id, Artist.name, Artist.image_link).join(Venue, Artist).filter(Show.start_time < datetime.today(),Show.venue_id==venue_data.id).all()
  # iterate through the upcoming shows and append the matching rows of the queried columns
  upcoming_shows = []
  for start_time, artist_id, artist_name, image_link in upcoming_show:
    upcoming_shows.append(
      {
        "artist_id": artist_id,
        "artist_name": artist_name,
        "artist_image_link": image_link,
        "start_time": format_datetime(str(start_time))
      }
    )
  # iterate through the past shows and append the matching rows of the queried columns
  past_shows = []
  for start_time, artist_id, artist_name, image_link in past_show:
    past_shows.append(
      {
        "artist_id": artist_id,
        "artist_name": artist_name,
        "artist_image_link": image_link,
        "start_time": format_datetime(str(start_time))
      }
    )
  #assign data and get the past/upcoming shows count using len
  data={
    "id":venue_data.id,
    "name":venue_data.name,
    "genres": venue_data.genres.split(","),
    "address":venue_data.address,
    "city":venue_data.city,
    "state":venue_data.state,
    "phone":venue_data.phone,
    "website":venue_data.website,
    "facebook_link":venue_data.facebook_link,
    "seeking_talent":venue_data.seeking_talent,
    "seeking_description": venue_data.seeking_description,
    "image_link":venue_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_show),
    "upcoming_shows_count": len(upcoming_show),
  }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  status: done

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  #status: done
  try:
    # request data from the Venue Form
    form =VenueForm(request.form)
    # as suggested in the classroom, handle the data coming from Flask-WTF using e.g: venue=Venue(name=form.name.data)
    venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      phone = form.phone.data,
      genres = ','.join(form.genres.data),
      facebook_link = form.facebook_link.data,
      image_link = form.image_link.data,
      website = form.website_link.data,
      seeking_talent = form.seeking_talent.data, 
      seeking_description = form.seeking_description.data
      
    )
    # if no errors, add and commit the received form values
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully listed!')

  except Exception as err:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed. ' + str(err))
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  #status: done
  try:
    # Query the venue id and delete records with the venue id
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' has been deleted!')
  except Exception as err:
    flash('Error! ' + venue.name + ' was not deleted' + str(err))
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  #return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  #status: done
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # status: done
  # #get the search term and query the Artist model, filter results like the search term and ensure case insensitive
  search_term = request.form.get('search_term', '')
  results = Artist.query.filter(func.lower(Artist.name).like(f'%{search_term.lower()}%')).all()
  #count the number of related searches and append the data like search term
  response = {
    "count": len(results),
    "data": [{
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": Show.query.filter(Show.start_time > datetime.now(), Show.artist_id == result.id).count()
    } for result in results]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  #Status: done

  #query the Artist model with the artist id
  artist_data = Artist.query.filter_by(id=artist_id).first()

  #filter past and upcoming shows using </> datetime
  upcoming_show = db.session.query(Show.start_time, Venue.id, Venue.name, Venue.image_link).join(Venue, Artist).filter(Show.start_time>=datetime.today(),Show.artist_id==artist_data.id).all()
  past_show = db.session.query(Show.start_time, Venue.id, Venue.name, Venue.image_link).join(Venue, Artist).filter(Show.start_time<datetime.today(),Show.artist_id==artist_data.id).all()
  
  #iterate through and append the required rows to their matching columns
  upcoming_shows = []
  for start_time, venue_id, venue_name, image_link in upcoming_show:
    upcoming_shows.append(
      {
        "venue_id": venue_id,
        "venue_name": venue_name,
        "venue_image_link": image_link,
        "start_time": format_datetime(str(start_time))
      }
    )

  past_shows = []
  for start_time, venue_id, venue_name, image_link in past_show:
    past_shows.append(
      {
        "venue_id": venue_id,
        "venue_name": venue_name,
        "venue_image_link": image_link,
        "start_time": format_datetime(str(start_time))
      }
    )
  #assign data and specify the past/upcoming show count using len
  data={
    "id": artist_id,
    "name":artist_data.name,
    "genres":artist_data.genres.split(","),
    "city":artist_data.city,
    "state":artist_data.state,
    "phone":artist_data.phone,
    "website":artist_data.website,
    "facebook_link":artist_data.facebook_link,
    "seeking_venue":artist_data.seeking_venue,
    "seeking_description":artist_data.seeking_description,
    "image_link":artist_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_show),
    "upcoming_shows_count": len(upcoming_show),
  }

  return render_template('pages/show_artist.html', artist=data)



#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  #retrieve data from the Artist model by querying with the artist id
  artist = Artist.query.get(artist_id)
  form.name.process_data(artist.name)
  form.genres.process_data(artist.genres)
  form.city.process_data(artist.city)
  form.state.process_data(artist.state)
  form.phone.process_data(artist.phone)
  form.website_link.process_data(artist.website)
  form.facebook_link.process_data(artist.facebook_link)
  form.seeking_venue.process_data(artist.seeking_venue)
  form.seeking_description.process_data(artist.seeking_description)
  form.image_link.process_data(artist.image_link)
  
  # TODO: populate form with fields from artist with ID <artist_id>
  #status: done
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  #status: done
  #update Artist form with new input
  form =ArtistForm(request.form) 
  try:
    artist = Artist.query.get(artist_id)
    artist.name = form.name.data
    artist.genres = ','.join(form.genres.data)
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website = form.website_link.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    # if successful add new data and commit session
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' updated successfully!')

  except Exception as err:
    db.session.rollback()
    flash('Error updating artist ' + artist.name + str(err))
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # query the Venue and filter using venue id to retrieve previous input data
  venue = Venue.query.filter_by(id=venue_id).first()
  form.name.data =venue.name
  form.genres.data = venue.genres
  form.address.data =venue.address
  form.city.data =venue.city
  form.state.data =venue.state
  form.phone.data =venue.phone
  form.website_link.data =venue.website
  form.facebook_link.data =venue.facebook_link
  form.seeking_talent.data =venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data =venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  #status: done
  # retrieve the new inputs from the form
  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.genres = ','.join(form.genres.data)
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    #add and commit new input
    db.session.add(venue)
    db.session.commit()
    flash('Venue updated successfully!')
  except Exception as err:
      db.session.rollback()
      flash('Error updating venue!' + str(err))
  finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  #status: done
  try:
    # create new data using form input, I requested form so I could use .joi() on the genres
    form = ArtistForm(request.form)
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      genres=','.join(form.genres.data),
      state=form.state.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      seeking_description=form.seeking_description.data,
      seeking_venue=form.seeking_venue.data,
      website=form.website_link.data,
      facebook_link=form.facebook_link.data
    )
    # add new data and commit session
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully listed!')
  
  except Exception as err:
    flash('Error adding ' + artist.name + str(err))
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  #return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):

  # query the artist id and delete all data related to said id
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' has been deleted successfully')
    
  except Exception as err:
    flash('Error!' + artist.name + ' was not deleted')
    db.session.rollback
  finally:
    db.session.close()
  
  return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #status: done
  #query the Shows table
  shows = Show.query.all()
  #use a for loop to append artist and venue datails by querying the venue and artist tables
  for show in shows:
    show = show.as_dict()
    show['venue_name'] = Venue.query.get(show['venue_id']).name
    show['artist_name'] = Artist.query.get(show['artist_id']).name
    show['artist_image_link'] = Artist.query.get(show['artist_id']).image_link
  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    #retrieve form data
    show = Show(
      artist_id=request.form.get('artist_id'),
      venue_id=request.form.get('venue_id'),
      start_time=request.form.get('start_time')
    )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as err:
    db.session.rollback()
    flash('An error occured. Show could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')
  # on successful db insert, flash success
  #flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  #return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
