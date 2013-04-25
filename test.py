import shutil
import os
from mutagen.mp3 import EasyMP3 as MP3
from flask import Flask
from flask.ext.testing import TestCase
import unittest
from models import db
from manage import populate_db

class MyTest(TestCase):

    def create_app(self):
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'xxx'  # XXX fix this
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TagTest(MyTest):

    def setUp(self):
        super(TagTest, self).setUp()

        test_src = "test/sinewave.mp3"

        for letter in ['a','b','c']:
            filename = "test/" + letter + ".mp3"
            shutil.copyfile(test_src, filename)
            song_tag = MP3(filename)
            song_tag['title'] = u"Song " + letter.upper()
            song_tag['artist'] = u"Artist " + letter.upper()
            song_tag.save()

    def test_tags(self):
        populate_db('test', False)

    def tearDown(self):
        for letter in ['a','b','c']:
            os.remove("test/" + letter + ".mp3")
        super(TagTest, self).tearDown()


if __name__ == '__main__':
    unittest.main()
