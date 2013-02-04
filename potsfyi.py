#!/usr/bin/env python
import os
import re
from subprocess import Popen, PIPE
from flask import (Flask, request, render_template, jsonify, abort, redirect,
                   Response)
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from wsgi_utils import PipeWrapper


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracks.db'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 10
db = SQLAlchemy(app)

app.config.update(
    DEBUG=(True if os.environ.get('DEBUG') in ['1', 'True'] else False),
    PORT=int(os.environ.get('PORT', 5000)),
    DB_URI=(os.environ.get('DB_URI', 'sqlite:///tracks.db')),
    MUSIC_DIR=(os.environ.get('MUSIC_DIR', 'static/music')),
)


class Track(db.Model):
    ''' artist, track, filename, album '''
    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(200))
    title = db.Column(db.String(240))
    filename = db.Column(db.String(256))
    track_num = db.Column(db.Integer)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    album = db.relationship('Album',
        backref=db.backref('tracks', lazy='dynamic'))

    def __init__(self, artist, title, filename, album, track_num):
        self.artist = artist
        self.title = title
        self.album = album
        self.filename = filename
        self.track_num = track_num

    def __repr__(self):
        return u'<Track {0.artist} - {0.title}>'.format(self)

    @property
    def serialize(self):
        return {
            'artist': self.artist,
            'title': self.title,
            'album': self.album.serialize if self.album else '',
            'track': self.track_num,
            'filename': self.filename,
            'id': self.id
        }

    @hybrid_property
    def artist_title(self):
        return self.artist + " " + self.title


class Album(db.Model):
    ''' artist, title, date, label, cat# '''
    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(200))
    title = db.Column(db.String(240))
    # date format?
    date = db.Column(db.String(16))
    label = db.Column(db.String(240))
    cat_number = db.Column(db.String(32))
    cover_art = db.Column(db.String(256))  # filename of cover art, jpg/png

    def __init__(self, artist, title, date=None, label=None, cat_number=None,
                 cover_art=None):
        self.artist = artist
        self.title = title
        self.date = date
        self.label = label
        self.cat_number = cat_number
        self.cover_art = cover_art

    def __repr__(self):
        return (u'<Album {0.title} - ' +
            u'{0.artist} ({0.date})>').format(self)

    @property
    def serialize(self):
        return {
            'artist': self.artist,
            'title': self.title,
            'date': self.date,
            'label': self.label,
            'cat_number': self.cat_number,
            'cover_art': self.cover_art
        }


@app.route('/search')
def search_results():
    """ Perform a general search encompassing artist, track, albums. """
    search_term = request.args.get('q', '')

    # split search term into up to 10 tokens (anything further is ignored)
    tokens = filter(None, re.split('\s+', search_term))[:10]

    filters = [Track.title.contains(token) | Track.artist.contains(token)
               for token in tokens]
    tracks = Track.query.filter(*filters).limit(30).all()
    serialized_tracks = [t.serialize for t in tracks]

    # prefix all filenames with the music dir,
    # so the client-side app can find them
    for t in serialized_tracks:
        t['filename'] = os.path.join(app.config['MUSIC_DIR'], t['filename'])
        try:
            t['album']['cover_art'] = os.path.join(app.config['MUSIC_DIR'],
                                                   t['album']['cover_art'])
        except (KeyError, TypeError, AttributeError):
            pass

    return jsonify(objects=serialized_tracks)


@app.route('/song/<int:track_id>/<wanted_formats>')
def get_track(track_id, wanted_formats):
    """ Get a track.
    If `wanted_formats` (a comma-separated list) includes the file's actual
    format, a redirect is sent (so the static file can be handled as such).
    Otherwise, if `wanted_formats` includes ogg, it's transcoded on the fly.
    """

    TRANSCODABLE_FORMATS = ['mp3', 'ogg', 'flac', 'm4a', 'wav']
    wanted_formats = re.split(',', wanted_formats)

    track = Track.query.filter_by(id=track_id).first()
    if track is None:
        abort(404)

    actual_format = re.search('\.([^.]+)$', track.filename).group(1)
    if actual_format in wanted_formats:
        # No need to transcode. Just redirect to the static file.
        return redirect(os.path.join(app.config['MUSIC_DIR'], track.filename))

    if (actual_format not in TRANSCODABLE_FORMATS
            or 'ogg' not in wanted_formats):
        # Can't transcode this. We only go from TRANSCODABLE_FORMATS to ogg.
        abort(404)

    # Transcode to ogg.
    # Note that track.filename came out of the DB and is *not* user-specified
    # (through the web interface), so can be trusted.
    command = ['avconv', '-v', 'quiet',
               '-i', os.path.join(app.config['MUSIC_DIR'], track.filename),
               '-f', 'ogg', '-acodec', 'libvorbis', '-aq', '5', '-']
    pipe = Popen(command, stdout=PIPE)

    return Response(PipeWrapper(pipe),
                    mimetype='audio/ogg', direct_passthrough=True)


@app.route('/')
def front_page():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=app.config['PORT'])
