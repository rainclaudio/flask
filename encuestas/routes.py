from crypt import methods
from fileinput import filename
from textwrap import indent
from turtle import title
from flask import render_template, url_for, flash, redirect, request, jsonify
from datetime import datetime
from encuestas import app,db, bcrypt

from encuestas.forms import CrearEncuestaForm, CrearItemForm, CrearPreguntaForm, RegistrationForm, LoginForm, EnviarRespuestaForm, updatePerfil
from encuestas.models import Encuesta, Item, User, Post, Pregunta, Respuesta
from flask_login import login_user, current_user, logout_user, login_required
import secrets
from PIL import Image
import os
import random

@app.route("/")
@app.route("/home")
def home():

    encuestas = Encuesta.query.filter_by(estado = "publicada")
    return render_template('home.html', encuestas = encuestas)



@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route("/responder_encuesta/<int:encuesta_id>", methods=['GET', 'POST'])
def responder_encuesta(encuesta_id):
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    preguntas = Pregunta.query.filter_by(encuesta_id = encuesta_id)
    
    selected_preguntas_id = []
    for pregunta in preguntas:
        selected_preguntas_id.append(pregunta.id)
        
    items = Item.query.filter(Item.pregunta_id.in_(selected_preguntas_id))
    
    respuesta_form = EnviarRespuestaForm()

    if respuesta_form.validate_on_submit():
        todas_respondidas = True
        for pregunta in preguntas:
            if str(type(request.form.get(f'{pregunta.id}'))) == "<class 'NoneType'>":
                todas_respondidas = False
                flash("¡Aun existen preguntas sin responder!", 'danger')
                break

        if todas_respondidas:
            for pregunta in preguntas:
                item_id_seleccionado = request.form.get(f'{pregunta.id}')
                respuesta = Respuesta(item_id = item_id_seleccionado, pregunta_id = pregunta.id, id_usuario = current_user.username , id_encuesta =encuesta_id)
                db.session.add(respuesta)
            db.session.commit()
            flash("¡Felicidades! Has respondido la encuesta " + str(encuesta.title), 'success')
            return redirect('/')
            
    return render_template('responder_encuesta.html', 
        title = 'Responder Encuesta',
        encuesta = encuesta,
        preguntas = preguntas,
        items = items,
        respuesta_form = respuesta_form,
    )


# ELIMINAR 
@app.route("/crear_encuesta", methods=['GET', 'POST'])
@login_required
def crear_encuesta():
    encuesta = Encuesta(title = 'Encuesta sin Título',description = "", user_id = current_user.username)
    db.session.add(encuesta)
    db.session.commit()
    flash(f'Encuesta creada!', 'success ')
    return redirect(url_for('editar_encuesta',encuesta_id = encuesta.id))


@app.route("/encuesta/<int:encuesta_id>", methods=['GET', 'POST'])
def encuesta(encuesta_id):
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    preguntas = Pregunta.query.filter_by(encuesta_id = encuesta_id)

    id_preguntas = []
    for preg in preguntas:
        id_preguntas.append(preg.id)

    items = Item.query.filter(Item.pregunta_id.in_(id_preguntas))

    boton_editar = False
    boton_respuestas = False
    if current_user.is_authenticated:
        print("user is auth")
        encuestas_propias = Encuesta.query.filter_by(user_id = current_user.username)
        for encuestas in encuestas_propias:
            if encuestas.id == encuesta_id:
                boton_respuestas = True
                boton_editar = True
                break

    return render_template('encuesta.html', 
        title= 'Encuesta',
        encuesta = encuesta,
        preguntas = preguntas,
        items = items,
        boton_editar = boton_editar,
        boton_respuestas = boton_respuestas
    )



@app.route("/editar_encuesta/<int:encuesta_id>", methods=['GET', 'POST'])
def editar_encuesta(encuesta_id):
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    preguntas = Pregunta.query.filter_by(encuesta_id = encuesta_id)
    print('numero de la encuesta: ' + str(encuesta_id) )
    id_preguntas = []
    for preg in preguntas:
        id_preguntas.append(preg.id)
    print(id_preguntas)
    items = Item.query.filter(Item.pregunta_id.in_(id_preguntas))
    items_preguntas = []
    counter = 0
    for item in items:
        print(item.description)

    for preg in preguntas:
        for item in items:
            if preg.id == item.pregunta_id:
                counter+= 1
        items_preguntas.append(counter)
        counter = 0

    print(items_preguntas)

    total_pregs = len(id_preguntas)
    bool_items = 1

    if len(items_preguntas) == 0:
        bool_items = 0

    for n in items_preguntas:
        if n <= 1:
            bool_items = 0

    encuesta_form = CrearEncuestaForm()
    pregunta_form = CrearPreguntaForm()
    return render_template('editar_encuesta.html', 
        title= 'Editar Encuesta',
        encuesta = encuesta,
        preguntas = preguntas,
        items = items,
        encuesta_form = encuesta_form,
        pregunta_form = pregunta_form,
        total_pregs = total_pregs,
        bool_items = bool_items
    )
        
###########################################
# Probando Javascript con flask


# CRUD ENCUESTA
@app.route('/update_pregunta_test',methods=['POST'])
def update_pregunta_test():
    # obtener la data que se ha recibido
    dataGet = request.get_json(force=True)
    pregunta = Pregunta.query.get_or_404(dataGet['pregunta_id'])
    pregunta.title = dataGet['description']
    db.session.commit()
    # Respuesta
    reply = {"status":"success","id": pregunta.id, "description" : pregunta.title}
    return jsonify(reply)


@app.route('/add_item_test',methods=['POST'])
def add_item_test():
    # obtener la data que se ha recibido
    dataGet = request.get_json(force=True)
    pregunta_id = dataGet['pregunta_id']   
    print(dataGet['pregunta_id'])

    # creación del ITEM
    item = Item(description = dataGet['description'], pregunta_id = pregunta_id)
    db.session.add(item)
    db.session.commit()

    # Respuesta
    reply = {"status":"success","id": item.id, "description" : item.description}
    return jsonify(reply)
    
@app.route('/add_pregunta_test',methods=['POST'])
def add_pregunta_test():
    # obtener la data que se ha recibido
    dataGet = request.get_json(force=True)
    encuesta_id = dataGet['encuesta_id']   
    print(dataGet['encuesta_id'])

    # creación del ITEM
    pregunta = Pregunta(title = dataGet['description'], encuesta_id = encuesta_id)
    db.session.add(pregunta)
    db.session.commit()

    # Respuesta
    reply = {"status":"success","id": pregunta.id, "description" : pregunta.title}
    return jsonify(reply)


@app.route('/update_item_test',methods=['POST'])
def update_item_test():
    # obtener la data que se ha recibido
    dataGet = request.get_json(force=True)
    item = Item.query.get_or_404(dataGet['item_id'])
    item.description = dataGet['description']
    db.session.commit()
    # Respuesta
    reply = {"status":"success","id": item.id, "description" : item.description}
    return jsonify(reply)
@app.route('/delete_pregunta_test', methods=['POST'])
def delete_pregunta():

    # obtener data recibida  
    dataGet = request.get_json(force=True)
    pregunta_id = dataGet['pregunta_id']
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    # Creación de datos 
    print("ahora borro la pregunta")
    id_items = []
    items_of_preg = Item.query.filter_by(pregunta_id = pregunta_id)
    for item in items_of_preg:
        id_items.append(item.id)
    print(id_items)
    db.session.delete(pregunta)
    db.session.commit()
    # respuesta
    reply = {"status": "deleted successfully"}
   
    return jsonify(reply)
 
@app.route('/delete_item_test', methods= ['POST'])
def delete_item():

    # obtener data recibida  
    dataGet = request.get_json(force=True)
    item_id = dataGet['item_id']
    item = Item.query.get_or_404(item_id)
    # Creación de datos 
    db.session.delete(item)
    db.session.commit()
    # respuesta
    reply = {"status": "deleted successfully"}
   
    return jsonify(reply)

@app.route('/update_title_test',methods=['POST'])
def update_title_test():
    # obtener la data que se ha recibido
    dataGet = request.get_json(force=True)
    encuesta = Encuesta.query.get_or_404(dataGet['encuesta_id'])
    encuesta.title = dataGet['description']
    db.session.commit()
    # Respuesta
    reply = {"status":"success","id": encuesta.id, "description" : encuesta.title}
    return jsonify(reply)

@app.route('/update_description_test',methods=['POST'])
def update_description_test():
    # obtener la data que se ha recibido
    dataGet = request.get_json(force=True)
    encuesta = Encuesta.query.get_or_404(dataGet['encuesta_id'])
    encuesta.description = dataGet['description']
    db.session.commit()
    # Respuesta
    reply = {"status":"success","id": encuesta.id, "description" : encuesta.description}
    return jsonify(reply)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/survey_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    # i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/save_image_test", methods=['GET', 'POST'])
def save_image():
   picture = request.files['static_file']
   id_enc = request.form['static_id']
   print(request.form['static_id'])
   encuesta = Encuesta.query.get_or_404(id_enc)
   if picture:
        picture_file = save_picture(picture)
        encuesta.image_file = picture_file
   print(encuesta.image_file)
   db.session.commit()
   flash('La imagen ha sido subida!', 'success')
   return jsonify({ "jajas": "jajas"})
# FIN experimentación javascript con flask
###########################################

# Eliminar
@app.route("/editar_encuesta/<int:encuesta_id>/añadir_pregunta", methods=['GET', 'POST'])
def add_pregunta(encuesta_id):
    pregunta_form = CrearPreguntaForm()
    if pregunta_form.validate_on_submit():
        pregunta = Pregunta(title = pregunta_form.title.data, encuesta_id = encuesta_id)
        db.session.add(pregunta)
        db.session.commit()
        flash(f'Pregunta {pregunta_form.title.data} añadida! {encuesta_id}', 'success')
        return redirect( url_for('editar_encuesta', encuesta_id=encuesta_id))
    return render_template(
        'añadir_pregunta.html', 
        title= 'Añadir Encuesta',
        pregunta_form = pregunta_form
    )
# Eliminar
@app.route("/editar_encuesta/<int:encuesta_id>/añadir_pregunta/<int:pregunta_id>", methods=['GET', 'POST'])
def add_item(encuesta_id,pregunta_id):
    item_form = CrearItemForm()
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    if item_form.validate_on_submit():
        item = Item(description = item_form.description.data, pregunta_id = pregunta_id)
        db.session.add(item)
        db.session.commit()
        flash(f'Item {item_form.description.data} añadida! {pregunta_id}', 'success')
        return redirect( url_for('editar_encuesta', encuesta_id=encuesta_id))
    return render_template(
        'añadir_item.html', 
        title= 'Añadir Item',
        pregunta = pregunta,
        item_form = item_form
    )

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hash_pass = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username =form.username.data, name =form.name.data, email=form.email.data, password =  hash_pass, tipo=form.tipo.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Creaste tu cuenta, bienvenid@ {form.name.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('No puedes entrar, vuelve a checkear la contraseña o usuario.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/post/<int:encuesta_id>/cerrar", methods=['POST'])
def cerrar_encuesta(encuesta_id):
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    encuesta.estado = "cerrada"
    db.session.commit()
    flash('Your post #' + str(encuesta_id) + ' has been closed!', 'success')
    return redirect(url_for('home'))


@app.route("/post/<int:encuesta_id>/<int:total_pregs>/<int:bool_items>/publicar", methods=['POST'])
def publicar_encuesta(encuesta_id,total_pregs,bool_items):
    if total_pregs == 0:
        flash('Para publicar encuesta se necesita minimo una pregunta', 'danger')
        return redirect( url_for('editar_encuesta', encuesta_id=encuesta_id))
    if bool_items == 0:
        flash('Para publicar encuesta se necesita minimo dos items por pregunta', 'danger')
        return redirect( url_for('editar_encuesta', encuesta_id=encuesta_id))
    else:
        encuesta = Encuesta.query.get_or_404(encuesta_id)
        encuesta.estado = "publicada"
        db.session.commit()
        flash('Your post #' + str(encuesta_id) + ' has been posted!', 'success')
        return redirect(url_for('home'))

def guardarfoto(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)
    
    prev_picture = os.path.join(app.root_path, 'static/profile_pics', current_user.image_file)
    if os.path.exists(prev_picture) and os.path.basename(prev_picture) != 'default.jpg':
        os.remove(prev_picture)

    return picture_fn

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():

    form = updatePerfil()
    respuesta = Respuesta.query.filter_by(id_usuario = current_user.username)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = guardarfoto(form.picture.data)
            current_user.image_file = picture_file
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.visible_inf = form.visible.data

        db.session.commit()
        flash('Tus datos han sido actualizados', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
         
    
    lista_query= []
    encuest = {}
    for i in respuesta:
        datet =  i.date
        encuest[i.date.strftime("%d/%m/%Y %H:%M:%S")] = i.id_encuesta
        encRESP = Encuesta.query.filter_by(id = i.id_encuesta )
        #print(encRESP)}
    for i in encuest:
        print(encuest[i])
        lista_query.append(Encuesta.query.filter_by(id = encuest[i]  ))
    if len(lista_query) ==0:
        lista_query = 0
   
    
    
    encPUBLIC = Encuesta.query.filter_by(user_id = current_user.username,estado = "publicada" )
    encCREATE = Encuesta.query.filter_by(user_id = current_user.username,estado = "creada" )
    encCLOSED = Encuesta.query.filter_by(user_id = current_user.username,estado = "cerrada" )
    TOTAL=len(encuest)
    TOTALC=0
    
  
    tipo = False 
    perfil_usuario =  'profile_encuestado.html'
   
    if current_user.tipo == '1':
        tipo = True
        perfil_usuario =  'profile_encuestador.html'
        for i in encPUBLIC:
            TOTAL=TOTAL+1
        for i in encCREATE:
            TOTAL=TOTAL+1
        for i in encCLOSED:
            TOTALC=TOTALC+1
        
    image_file = url_for('static', filename= 'profile_pics/' + current_user.image_file)
    
   
    return render_template(perfil_usuario, title='Profile', image_file=image_file , encPUBLIC = encPUBLIC, form = form, encCREATE=encCREATE, encCLOSED=encCLOSED, TOTAL =TOTAL+TOTALC, TOTALC  =  TOTALC, tipo=tipo, lista_query=lista_query)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


#VER RESULTADOS
@app.route("/resultados_encuesta/<int:encuesta_id>", methods=['GET', 'POST'])
@login_required
def resultados_encuesta(encuesta_id):
    
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    preguntas = Pregunta.query.filter_by(encuesta_id = encuesta_id)
    
    map_preg_a_array_cant_resp_item = {}
    map_preg_a_array_percent_resp_item = {}
    map_preg_a_array_str = {}
    id_preguntas = []

    for preg in preguntas:
        id_preguntas.append(preg.id)
        map_preg_a_array_cant_resp_item[preg.id] = []
        map_preg_a_array_percent_resp_item[preg.id] = []
        map_preg_a_array_str[preg.id] = []
    
    items = Item.query.filter(Item.pregunta_id.in_(id_preguntas))

    colores = [
        'rgb(191, 161, 148)',
        'rgb(248, 207, 155)',
        'rgb(222, 90, 90)',
        'rgb(236, 151, 109)',
        'rgb(253, 197, 150)',
        'rgb(253, 234, 204)',
        'rgb(123, 126, 175)',
        'rgb(74, 75, 123)',
        'rgb(240, 185, 197)',
        'rgb(196, 143, 193)',
        'rgb(110, 112, 172)',
        'rgb(159, 166, 209)',
        'rgb(253, 224, 202)',
        'rgb(2, 138, 155)',
    ]

    item_a_color = {}

    for preg in preguntas:
        index = 0
        for item in items:
            if item.pregunta_id == preg.id:
                map_preg_a_array_cant_resp_item[preg.id].append(len(Respuesta.query.filter_by(item_id = item.id).all()))
                map_preg_a_array_percent_resp_item[preg.id].append(len(Respuesta.query.filter_by(item_id = item.id).all()))
                map_preg_a_array_str[preg.id].append(item.description)
                item_a_color[item.id] = colores[index % len(colores)]
                index += 1

    map_respuestas_y_total = {}

    for item in items:
        temp = Respuesta.query.filter_by(item_id = item.id).all()
        temp_tot = Respuesta.query.filter_by(pregunta_id = item.pregunta_id).all()
        map_respuestas_y_total[item.id] = [len(temp), len(temp_tot)]
    
    for preg in preguntas:
        for i in range(len(map_preg_a_array_percent_resp_item[preg.id])):
            if map_respuestas_y_total[item.id][1] != 0:
                map_preg_a_array_percent_resp_item[preg.id][i] = round(map_preg_a_array_percent_resp_item[preg.id][i] * 100 / map_respuestas_y_total[item.id][1], 1)
            else:
                map_preg_a_array_percent_resp_item[preg.id][i] = 0

    return render_template('resultado_encuesta.html', 
        title= 'Resultados Encuesta',
        encuesta = encuesta,
        preguntas = preguntas,
        items = items,
        map_respuestas_y_total = map_respuestas_y_total,
        map_preg_resp = map_preg_a_array_cant_resp_item,
        map_preg_perc = map_preg_a_array_percent_resp_item,
        map_preg_str = map_preg_a_array_str,
        item_a_color = item_a_color,
        colores = colores,
    )

