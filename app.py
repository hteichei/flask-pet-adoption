from flask import Flask, render_template, redirect, url_for, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField
from wtforms.validators import InputRequired, Optional, AnyOf, URL, NumberRange
import requests
import os

DB = "postgresql://localhost/pets"

app = Flask(__name__)
app.config['SECRET_KEY'] = "abc123"
toolbar = DebugToolbarExtension(app)

app.config['SQLALCHEMY_DATABASE_URI'] = DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
db = SQLAlchemy(app)


class Pet(db.Model):
    __tablename__ = 'pets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    species = db.Column(db.Text, nullable=False)
    photo_url = db.Column(db.Text)
    age = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    available = db.Column(db.Boolean, nullable=False, default=True)


db.create_all()


class addPetForm(FlaskForm):

    name = StringField("Pet Name:")
    # Can use a radiofield instead of stringfield to reduce confusion
    species = StringField(
        "Pet Species:",
        validators=[
            AnyOf(
                values=['Dog', 'Cat', 'Porcupine', 'dog', 'cat', 'porcupine'],
                message='Species must be dog, cat, or porcupine',
                values_formatter=None)
        ])
    photo_url = StringField(
        "Pet Photo URL:",
        validators=[URL(require_tld=True, message='Invalid URL')])
    age = FloatField(
        "Age:",
        validators=[
            NumberRange(min=0, max=30, message='Age must be between 0 and 30')
        ])
    notes = StringField("Notes on Pet:")


class diplayAndEditForm(FlaskForm):

    photo_url = StringField(
        "Pet Photo URL",
        validators=[URL(require_tld=True, message='Invalid URL')])
    notes = StringField("Notes on Pet")
    available = BooleanField("Available for adoption?")


@app.route('/', methods=['GET'])
def display_pets():
    pet_list = Pet.query.all()
    return render_template('index.html', pet_list=pet_list)


@app.route('/add/random', methods=['GET'])
def add_random_pet():
    """Add random pet to the index.html page using PetFinder API"""

    api_key = os.environ['API_KEY']
    r = requests.get(
        f'http://api.petfinder.com/pet.getRandom?key={api_key}&format=json&output=basic'
    )

    age = r.json()['petfinder']['pet']['age']['$t']
    name = r.json()['petfinder']['pet']['name']['$t']
    species = r.json()['petfinder']['pet']['animal']['$t']
    photo_url = r.json()['petfinder']['pet']['media']['photos']['photo'][0][
        '$t']
    available = True

    new_pet = Pet(
        age=10,
        name=name,
        species=species,
        photo_url=photo_url,
        available=available)
    db.session.add(new_pet)
    db.session.commit()
    return redirect(url_for('display_pets'))


@app.route('/add', methods=['GET', 'POST'])
def add_pet():
    """Shows form to add a new pet to the index.html page.  Requires valid inputs."""

    form = addPetForm()

    if form.validate_on_submit():
        name = form.data['name']
        species = form.data['species']
        photo_url = form.data['photo_url']
        age = form.data['age']
        notes = form.data['notes']
        new_pet = Pet(
            name=name,
            species=species,
            photo_url=photo_url,
            age=age,
            notes=notes)
        db.session.add(new_pet)
        db.session.commit()
        return redirect(url_for('display_pets'))

    else:
        return render_template("add_pet_form.html", form=form)


@app.route('/<int:pet_id>', methods=['GET', 'POST'])
def show_pet(pet_id):
    """Shows speicific info on individual pets.  Shows form for editing existing pet info."""

    found_pet = Pet.query.get_or_404(pet_id)

    form = diplayAndEditForm(obj=found_pet)

    if form.validate_on_submit():
        found_pet.photo_url = form.data['photo_url']
        found_pet.notes = form.data['notes']
        found_pet.available = form.data['available']

        db.session.commit()
        return redirect(url_for('display_pets'))
    else:
        return render_template(
            'display_edit_form.html',
            pet_id=pet_id,
            form=form,
            found_pet=found_pet)


@app.route('/api/pets/<int:pet_id>', methods=['GET'])
def get_pet_data(pet_id):
"""Allows people to find pet info using the route above"""

    found_pet = Pet.query.get(pet_id)
    return jsonify({
        'name': found_pet.name,
        'age': found_pet.age,
        'species': found_pet.species,
        'notes': found_pet.notes,
        'photo_url': found_pet.photo_url,
        'available': found_pet.available
    })
