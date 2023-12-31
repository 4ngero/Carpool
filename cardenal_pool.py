#importación del framework
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

from flask_mysqldb import MySQL

#Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename 
import os

### customize>>>
#inicialización del APP
app= Flask(__name__,  template_folder='Templates')
#conexion
#app.config['MYSQL_HOST']='localhost' #Tuyo Comentar antes de subir
app.config['MYSQL_USER']='web-carpool' #De la esuela descomentar
#app.config['MYSQL_USER']='root' #Tuyo Comentar antes de subir
app.config['MYSQL_PASSWORD']='wS314762UU' #De la esuela descomentar
#app.config['MYSQL_PASSWORD']='' #Tuyo Comentar antes de subir
app.config['MYSQL_DB']='carpool'
app.secret_key= 'mysecretkey'
mysql= MySQL(app)
### <<<customize

@app.route('/')
def index():
    if not session.get("Matricula"):
            return redirect("/login")
    return redirect("/logout")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        VMatricula = request.form['txtMatricula']
        VPassword = request.form['txtPassword']
        
        # Realizar la consulta para obtener el rol del usuario
        CC = mysql.connection.cursor()
        CC.execute("SELECT id_rol FROM vw_inscripciones WHERE matricula = %s AND clave_ingreso = %s", (VMatricula, VPassword))
        Vid_rol = CC.fetchone()

        if Vid_rol:
            session["Matricula"] = VMatricula
            session["Rol"] = Vid_rol[0]

            if session["Rol"] == 1:  # Rol de conductor
                # Verificar si el conductor existe
                CC.execute("SELECT id_conductor FROM Conductor WHERE matricula = %s", (VMatricula,))
                Vid = CC.fetchone()

                if not Vid:  # Si no existe, insertar el conductor
                    CC.execute("INSERT INTO Conductor (matricula) VALUES (%s)", (VMatricula,))
                    mysql.connection.commit()

                    CC.execute("SELECT id_conductor FROM Conductor WHERE matricula = %s", (VMatricula,))
                    Vid = CC.fetchone()

                session["Conductor"] = Vid[0]
                return redirect("/conductor")

            elif session["Rol"] == 2:  # Rol de pasajero
                # Verificar si el pasajero existe
                CC.execute("SELECT id_pasajero FROM Pasajero WHERE matricula = %s", (VMatricula,))
                Vid = CC.fetchone()

                if not Vid:  # Si no existe, insertar el pasajero
                    CC.execute("INSERT INTO Pasajero (matricula) VALUES (%s)", (VMatricula,))
                    mysql.connection.commit()

                    CC.execute("SELECT id_pasajero FROM Pasajero WHERE matricula = %s", (VMatricula,))
                    Vid = CC.fetchone()

                session["Pasajero"] = Vid[0]
                return redirect("/pasajero")

            elif session["Rol"] == 3:  # Rol de administrador
                return redirect("/admin")

        else:
            flash('Usuario y/o contraseña equivocados, vuelva a intentarlo')
            return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()  # Limpiar todas las variables de sesión
    return redirect("/login")


#home de conductor
@app.route('/conductor')
def conductor():
    if not session.get("Matricula"):
            return redirect("/login")
    CC=mysql.connection.cursor()
    CC.execute("select * from Conductor where id_conductor='"+str(session["Conductor"])+"';")
    Vid=CC.fetchone()
    if Vid[2]==0:
        return redirect("/conductor/perfil")
    else:
        CC.execute("select * from Ruta where id_conductor=%s",(session["Conductor"],))
        rutas=CC.fetchall()
        CC.execute("select id_ruta from Ruta where id_conductor=%s",(session["Conductor"],))
        Vnone=str(CC.fetchone())
        CC.execute("select punto_referencia,descripcion,hora,p.id_ruta from Paradas as p inner join Ruta as r on p.id_ruta=r.id_ruta where r.id_conductor=%s",(session["Conductor"],))
        paradas=CC.fetchall()
        CC.execute("select id_pasajero from Ruta as ruta inner join Relacion_ruta as relacion_ruta on ruta.id_ruta=relacion_ruta.id_ruta where id_conductor=%s",(session["Conductor"],))
        aux=CC.fetchall()  
        id_pasajeros=[]
        for a in aux:
            id_pasajeros.append(int(a[0]))
        CC.execute("select matricula from Pasajero where id_pasajero in (%s)",(str(id_pasajeros),))
        aux=CC.fetchall()
        matriculas=[]
        for a in aux:
            id_pasajeros.append(int(a[0]))
        CC.execute("select * from vw_inscripciones where matricula in (%s)",(str(matriculas),))
        pasajeros=CC.fetchall()
        CC.execute("SELECT comentario FROM Administrador WHERE id_conductor = %s", (session["Matricula"],))
        comentarios_admin = CC.fetchall()

        return render_template('HomeConductor.html',rutas=rutas,Vnone=Vnone,paradas=paradas,pasajeros=pasajeros,comentarios_admin=comentarios_admin)

#perfil de conductor
@app.route('/conductor/perfil')
def perfilconductor():
    if not session.get("Matricula"):
            return redirect("/login")
    CC=mysql.connection.cursor()
    CC.execute("select matricula, nombre_completo, cuatrimestre, nombre_carrera, sexo, correo_electronico, fecha_nacimiento, nss from vw_inscripciones where matricula='"+session["Matricula"]+"';")
    datos_personales=CC.fetchone()
    temp=[]
    for i in datos_personales[1].split():
        temp.append(i)
    if len(temp)==3:
        nombre=temp[0]
        del temp[0]
    else:
        nombre=[]
        nombre.append(temp[0])
        del temp[0]
        nombre.append(temp[0])
        del temp[0]
    CC.execute("select placa,modelo,marca,color,lugares_disponibles from Relacion_autos as ra inner join Autos as a on ra.id_auto=a.id_auto where id_conductor=%s",(session["Conductor"],))
    autos=CC.fetchall()
    CC.execute("select telefono from Conductor where id_conductor=%s",(session["Conductor"],))
    tel=CC.fetchone()
    telefono=tel[0]
    
    CC.execute("SELECT matricula FROM vw_inscripciones WHERE matricula = " + str(session["Matricula"]) + ";")
    
    matriculaUtil = CC.fetchone() #Obtención de matricula en sesión

    
    CC.execute("SELECT autos.placa FROM vw_inscripciones " + 
            "INNER JOIN Conductor as conductor ON vw_inscripciones.matricula = conductor.matricula " +
            "INNER JOIN Relacion_autos as relacion_autos ON conductor.id_conductor = relacion_autos.id_conductor " +
            "INNER JOIN Autos as autos ON relacion_autos.id_auto = autos.id_auto " +
            "WHERE vw_inscripciones.matricula = %s;", (session["Matricula"],))
    
    placaUtils = CC.fetchall()#Obtención de placas de auto en sesión
    if len(placaUtils) == 0: #Si no existe un placa registradas
        placaUtils = "sinPlacas"
        placa1 = "sinPlaca1"
        placa2 = "sinPlaca2"
        INELink = "sinINE"
        UPQLink = "sinUPQ"
        polizaLink1 = "sinPoliza1"
        polizaLink2 = "sinPoiza2"
        placas_limpias = "sinPlacas_limpias"
        circulacionLink1 = "sinCirculacion1"
        circulacionLink2 = "sinCirculacion2"
        fotoVehiculoLink1 = "sinFotoVehiculo1"
        fotoVehiculoLink2 = "sinFotoVehiculo2"
        fotoPersonal = "sinFotoPersonal"
        añadirAuto = 0
        
    else:
        placas_limpias = []

        for tupla in placaUtils:
            if tupla is not None and len(tupla) > 0:
                placa = tupla[0]  # Accedemos al primer elemento de la tupla (la placa)
                placa_limpia = placa.replace("'", '').replace('"', '').replace('(', '').replace(')', '').replace(',', '')
                placas_limpias.append(placa_limpia)
    
    #FORMULACION DE CAMPOS DE VEHICULOS
        #Posición sobre las matrículas y las placas
        matricula = matriculaUtil[0]
        if len(placas_limpias) == 1:
            placa1 = placas_limpias[0]
            #Existentes
            INELink = "/static/archivos/" + str(matricula) + "_Credencial_INE.pdf"
            UPQLink = "/static/archivos/" + str(matricula) + "_Credencial_UPQ.pdf"
            polizaLink1 = "/static/archivos/" + str(matricula) + "_" + str(placa1) + "_Poliza.pdf"
            circulacionLink1 = "/static/archivos/" + str(matricula) + "_" + str(placa1) + "_Tarjeta_Circulacion.pdf"
            fotoVehiculoLink1 = "/static/archivos/" + str(matricula) + "_" + str(placa1) + "_Foto_Vehiculo.jpg"
            #Inexistentes
            placa2 = "sinPlaca2"
            polizaLink2 = "prueba"
            circulacionLink2 = "prueba"
            fotoVehiculoLink2 = "prueba"
            #FORMULACION DE FOTO PERSONAL
            fotoPersonal = "/static/archivos/" + str(matricula) + "_Foto_Personal.jpg"
            añadirAuto = 1
        
        if len(placas_limpias) == 2:
            placa1 = placas_limpias[0]
            placa2 = placas_limpias[1]
            
            INELink = "/static/archivos/" + str(matricula) + "_Credencial_INE.pdf"
            UPQLink = "/static/archivos/" + str(matricula) + "_Credencial_UPQ.pdf"
            polizaLink1 = "/static/archivos/" + str(matricula) + "_" + str(placa1) + "_Poliza.pdf"
            polizaLink2 = "/static/archivos/" + str(matricula) + "_" + str(placa2) + "_Poliza.pdf"
            circulacionLink1 = "/static/archivos/" + str(matricula) + "_" + str(placa1) + "_Tarjeta_Circulacion.pdf"
            circulacionLink2 = "/static/archivos/" + str(matricula) + "_" + str(placa2) + "_Tarjeta_Circulacion.pdf"
            fotoVehiculoLink1 = "/static/archivos/" + str(matricula) + "_" + str(placa1) + "_Foto_Vehiculo.jpg"
            fotoVehiculoLink2 = "/static/archivos/" + str(matricula) + "_" + str(placa2) + "_Foto_Vehiculo.jpg"
            #FORMULACION DE FOTO PERSONAL
            fotoPersonal = "/static/archivos/" + str(matricula) + "_Foto_Personal.jpg"
            añadirAuto = 2
            
    

    return render_template('Perfil_Conductor.html', fotoPersonal=fotoPersonal, INELink=INELink, UPQLink=UPQLink, poliza1=polizaLink1, poliza2=polizaLink2, datos=datos_personales, 
                           nombre=nombre,apellidos=temp,autos=autos,telefono=telefono, placa1=placa1, placa2=placa2, circulacion1=circulacionLink1, circulacion2=circulacionLink2,
                           fotoVehiculo1=fotoVehiculoLink1, fotoVehiculo2=fotoVehiculoLink2, añadirAuto=añadirAuto)

#insertar telefono
@app.route('/actualizar_telefonoc', methods=['POST'])
def actualizar_telefonoc():
    VTelefono=request.form['txtTelefono']
    CC= mysql.connection.cursor()
    CC.execute("update Conductor set telefono=%s where id_conductor=%s",(VTelefono,session["Conductor"],))
    mysql.connection.commit()
    return redirect("/conductor/perfil")

#insertar foto personal conductor
@app.route('/actualizar_foto_conductor', methods=['POST'])
def actualizar_fotoC():
    if request.method == "POST":
        CC= mysql.connection.cursor()
        CC.execute("select matricula from vw_inscripciones where matricula = " + str(session["Matricula"]) + ";")
        matriculaUtil = CC.fetchone()

        if matriculaUtil is not None:
            matriculaUtil = matriculaUtil[0].replace("'", '').replace('"', '').replace('(', '').replace(')', '').replace(',', '')
            
        foto_personal = request.files['fotoPersonal']
        if foto_personal:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(foto_personal.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) +"_Foto_Personal" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            foto_personal.save(upload_path)
            
    return redirect('/conductor/perfil')

#insertar foto personal pasajero
@app.route('/actualizar_foto_pasajero', methods=['POST'])
def actualizar_fotoP():
    if request.method == "POST":
        CC= mysql.connection.cursor()
        CC.execute("select matricula from vw_inscripciones where matricula = " + str(session["Matricula"]) + ";")
        matriculaUtil = CC.fetchone()

        if matriculaUtil is not None:
            matriculaUtil = matriculaUtil[0].replace("'", '').replace('"', '').replace('(', '').replace(')', '').replace(',', '')
            
        foto_personal = request.files['fotoPersonal']
        if foto_personal:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(foto_personal.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) +"_Foto_Personal" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            foto_personal.save(upload_path)
            
    return redirect('/pasajero')


#insertar auto
@app.route('/ingresar_auto', methods=['POST'])
def ingresar_auto():
    if request.method == 'POST':
        VMarca=request.form['txtMarca']
        VModelo=request.form['txtModelo']
        VColor=request.form['txtColor']
        VCapacidad=request.form['txtCapacidad']
        VPlaca=request.form['txtPlaca']
        
        CC= mysql.connection.cursor()
        CC.execute("insert into Autos(placa,modelo,marca,color,lugares_disponibles) values (%s,%s,%s,%s,%s);",(VPlaca,VModelo,VMarca,VColor,VCapacidad))
        
        CC.execute("select id_auto FROM Autos WHERE placa=%s",(str(VPlaca),))
        autoid=CC.fetchone()
        
        CC.execute("insert into Relacion_autos(id_conductor,id_auto) values(%s,%s);",(session["Conductor"],autoid[0],))
        CC.execute("update Conductor set primer_ingreso_flag=1")
        mysql.connection.commit()

        CC.execute("select matricula from vw_inscripciones where matricula = " + str(session["Matricula"]) + ";")
        matriculaUtil = CC.fetchone()

        if matriculaUtil is not None:
            matriculaUtil = matriculaUtil[0].replace("'", '').replace('"', '').replace('(', '').replace(')', '').replace(',', '')

        tarjeta_circula = request.files['tarjeta_circula']
        credencial_UPQ = request.files['credencial_UPQ']
        credencial_INE = request.files['credencial_INE']
        poliza = request.files['poliza']
        fotoVehiculo = request.files['fotoVehiculo']
        
        if tarjeta_circula:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(tarjeta_circula.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) +"_"+ str(VPlaca) + "_Tarjeta_Circulacion" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            tarjeta_circula.save(upload_path)
            
        if credencial_UPQ:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(credencial_UPQ.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) + "_Credencial_UPQ" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            credencial_UPQ.save(upload_path)
        
        if credencial_INE:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(credencial_INE.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) + "_Credencial_INE" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            credencial_INE.save(upload_path)
            
        if poliza:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(poliza.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) +"_"+ str(VPlaca) + "_Poliza" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            poliza.save(upload_path)
        
        if fotoVehiculo:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(fotoVehiculo.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) +"_"+ str(VPlaca) + "_Foto_Vehiculo" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            fotoVehiculo.save(upload_path)
        
    return redirect('/conductor/perfil')

#cambio de contraseña conductor
@app.route('/cambiar_contraseña', methods=['POST'])
def cambiar_contraseña():
    if request.method == 'POST':
        Vpassword=request.form['txtPassword']
        Vpasscon=request.form['txtConfirmPassword']
        if Vpassword==Vpasscon:
            CC= mysql.connection.cursor()
            CC.execute("update vw_inscripciones set clave_ingreso=%s where matricula=%s;",(str(Vpassword),str(session["Matricula"])))
            mysql.connection.commit()
    return redirect('/conductor/perfil')

#registrar ruta
@app.route('/registrar_ruta', methods=['POST'])
def registro_ruta():
    if request.method == 'POST':
        Vruta=request.form['txtRuta']
        Vturno=request.form['txtTurno']
        CC= mysql.connection.cursor()
        CC.execute("insert into Ruta(nombre_ruta,id_conductor,tipo_ruta) values (%s,%s,%s)",(Vruta,session["Conductor"],Vturno))
        CC.execute("select id_ruta from Ruta where nombre_ruta=%s and id_conductor=%s and tipo_ruta=%s",(Vruta,session["Conductor"],Vturno))
        id_ruta=CC.fetchone()
        id=id_ruta[0]
        mysql.connection.commit()
    return redirect(url_for('registrar_parada',id=id))

#registrar paradas
@app.route('/conductor/ruta/<id>')
def registrar_parada(id):
    if not session.get("Matricula"):
        return redirect("/login")
    CC= mysql.connection.cursor()
    CC.execute("select nombre_ruta, descripcion_completa from Ruta where id_ruta=%s",(id,))
    desc=CC.fetchone()
    id2=id
    CC.execute("select punto_referencia, descripcion, hora from Paradas where id_ruta=%s",(id,))
    paradas=CC.fetchall()
    return render_template('RegistroRuta.html',desc=desc,id=id2,paradas=paradas)

#añadir paradas
@app.route('/cargarparada/<id>', methods=['POST'])
def cargarparada(id):
    VReferencia=request.form['txtreferencia']
    VDescripcion=request.form['txtdescripcion']
    VHora=request.form['txthora']
    VDesGral=request.form['txtdesgral']
    CC= mysql.connection.cursor()
    CC.execute("insert into Paradas(punto_referencia,descripcion,hora,id_ruta) values (%s,%s,%s,%s)",(VReferencia,VDescripcion,VHora,id,))
    CC.execute("update Ruta set descripcion_completa=%s where id_ruta=%s",(VDesGral,id,))
    mysql.connection.commit()
    id2=id
    return redirect(url_for('registrar_parada',id=id2))


@app.route('/eliminarRuta/<id>')
def delete_route(id):
    try:
        CC= mysql.connection.cursor()
        CC.execute('DELETE FROM Paradas WHERE id_ruta=%s', (id,))
        mysql.connection.commit()
        flash('Ruta eliminada de manera correcta')
        return redirect(url_for('registrar_parada', id=id))
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Hubo un error al eliminar la ruta.')
        return redirect(url_for('registrar_parada', id=id))
    

@app.route('/eliminarRutaCompleta/<int:id>')
def delete_ruta(id):
    try:
        CC = mysql.connection.cursor()
        CC.execute('DELETE FROM Paradas WHERE id_ruta = %s', (id,))
        CC.execute('DELETE FROM Ruta WHERE id_ruta = %s', (id,))
        mysql.connection.commit()
        
        return redirect(url_for('conductor', id=id))
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Hubo un error al eliminar la ruta')
        return redirect(url_for('conductor', id=id))


""" 
@app.route('/eliminarAuto/<int:id>', methods=['POST'])
def eliminar_auto(id):
    try:
        CC = mysql.connection.cursor()
        CC.execute('DELETE FROM Autos WHERE id_auto=%s', (id,))
        mysql.connection.commit()
        flash('Auto eliminado de manera correcta', 'success')  
        return redirect(url_for('/conductor/perfil'))
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Hubo un error al eliminar la Ruta y las paradas asociadas.', 'error')  
        return redirect(url_for('conductor'))  
     """

#pagina principal pasajero 
@app.route('/pasajero')
def pasajero():
    CC=mysql.connection.cursor()
    CC.execute("select * from Relacion_ruta where id_pasajero='"+str(session["Pasajero"])+"';")
    Vid=CC.fetchall()
    Vnone=str(Vid)
    print(Vnone)
    if Vnone=='None':
        return redirect("/pasajero/ruta")
    else:
        CC.execute("select telefono from Pasajero where id_pasajero=%s",(session["Pasajero"],))
        telefono=CC.fetchone()
        #listado de conductores
        CC.execute("select id_ruta from Relacion_ruta where id_pasajero=%s",(session["Pasajero"],))
        aux=CC.fetchall()
        id_rutas=[]
        for a in aux:
            id_rutas.append(a[0])
        CC.execute("select id_conductor from Ruta where id_ruta in (%s)",(str(id_rutas),))
        id_conductores=CC.fetchall()
        aux=CC.fetchall()
        id_rutas=[]
        for a in aux:
            id_rutas.append(a[0])
        CC.execute("select matricula from Conductor where id_conductor in (%s)",(str(id_conductores),))
        aux=CC.fetchall()
        matriculas=[]
        for a in aux:
            matriculas.append(a[0])
        CC.execute("select * from vw_inscripciones where matricula in (%s)",(str(matriculas),))
        datos_personales2=CC.fetchall()
        CC.execute("select punto_referencia,descripcion,hora,p.id_ruta from Paradas as p inner join Ruta as r on p.id_ruta=r.id_ruta where r.id_conductor in (%s)",(str(id_conductores),))
        paradas=CC.fetchall()
        CC.execute("select matricula, nombre_completo, cuatrimestre, nombre_carrera, sexo, correo_electronico, fecha_nacimiento, nss from vw_inscripciones where matricula='"+session["Matricula"]+"';")
        datos_personales=CC.fetchone()
        CC.execute("select * from Ruta where id_ruta in (%s)",(str(id_rutas),))
        rutas=CC.fetchall()
        temp=[]
        for i in datos_personales[1].split():
            temp.append(i)
        if len(temp)==3:
            nombre=temp[0]
            del temp[0]
        else:
            nombre=[]
            nombre.append(temp[0])
            del temp[0]
            nombre.append(temp[0])
            del temp[0]
        CC.execute("select placa,modelo,marca,color,lugares_disponibles,id_conductor from Relacion_autos as ra inner join Autos as a on ra.id_auto=a.id_auto where id_conductor in (%s)",(str(id_conductores),))
        autos=CC.fetchall()  
        CC.execute("select * from vw_inscripciones where matricula in (%s)",(str(matriculas),))
        pasajeros=CC.fetchall()
        CC.execute("SELECT comentario FROM Administrador WHERE id_pasajero = %s", (session["Matricula"],))
        comentarios_admin1 = CC.fetchall()  
        return render_template('HomePasajero.html',Vnone=Vnone,paradas=paradas,nombre=nombre,apellidos=temp,datos=datos_personales,telefono=telefono,datos2=datos_personales2,autos=autos,rutas=rutas,pasajeros=pasajeros,comentarios_admin1=comentarios_admin1)

#registrar ruta pasajero    
@app.route('/pasajero/ruta')
def reservar_ruta():
    if not session.get("Matricula"):
        return redirect("/login")
    CC= mysql.connection.cursor()
    CC.execute("select r.nombre_ruta, r.tipo_ruta, i.nombre_completo, i.matricula, c.telefono, r.id_ruta from Conductor as c inner join Ruta as r on c.id_conductor=r.id_conductor inner join vw_inscripciones as i on i.matricula=c.matricula where primer_ingreso_flag=1")
    conductores=CC.fetchall()
    CC.execute("select * from paradas")
    paradas=CC.fetchall()
    return render_template('Rutas.html',conductores=conductores,paradas=paradas)

@app.route('/reserva_ruta/<id>')
def reserva_ruta(id):
    if not session.get("Matricula"):
        return redirect("/login")
    CC= mysql.connection.cursor()
    CC.execute("insert into Relacion_ruta(id_ruta,id_pasajero) values (%s,%s)",(id,session["Pasajero"],))
    mysql.connection.commit()
    return redirect("/pasajero")

#actualizar_telefono
@app.route('/actualizar_telefono', methods=['POST'])
def actualizar_telefono():
    VTelefono=request.form['txtTelefono']
    CC= mysql.connection.cursor()
    CC.execute("update Pasajero set telefono=%s where id_pasajero=%s",(VTelefono,session["Pasajero"],))
    mysql.connection.commit()
    return redirect("/pasajero")

#solicitudes
@app.route('/conductor/solicitudes')
def solicitudes():
    CC= mysql.connection.cursor()
    CC.execute("select pasajero.id_pasajero,nombre_ruta,tipo_ruta,i.matricula,nombre_completo,sexo from Ruta inner join Relacion_ruta as rr on ruta.id_ruta=rr.id_ruta inner join pasajero on rr.id_pasajero=pasajero.id_pasajero inner join vw_inscripciones as i on pasajero.matricula=i.matricula where ruta.id_conductor=%s",(session["Conductor"],))
    solicitudes=CC.fetchall()
    return render_template('Solicitudes.html',solicitudes=solicitudes)


@app.route('/SolicitudesAceptadas')
def solicitudesAceptadas():
    # Se tiene que redirigir a la vista de solicitudes aceptadas
    return redirect(url_for('info_pasajero'))


@app.route('/conductor/accion_solicitud', methods=['POST'])
def accion_solicitud():
    solicitud_id = request.form.get('solicitud_id')
    accion = request.form.get('accion')

    CC = mysql.connection.cursor()

    if accion == 'aceptar':
        CC.execute("UPDATE Relacion_ruta SET aprobacion = 1, estado = 'Aceptado' WHERE id_pasajero = %s", (solicitud_id,))
        mysql.connection.commit()

    # Obtén el ID del conductor que inició sesión
    id_conductor = session.get("Conductor")
    print("ID del conductor en la sesión:", id_conductor)

    # Verifica que el ID del conductor esté presente en la sesión
    if id_conductor is not None:
        # Selecciona solo las solicitudes aprobadas para ese conductor
        CC.execute("SELECT i.nombre_completo, i.matricula, i.nombre_carrera, i.sexo FROM vw_inscripciones i "
                   "INNER JOIN Pasajero as p ON i.matricula = p.matricula "
                   "INNER JOIN Relacion_ruta as rr ON p.id_pasajero = rr.id_pasajero "
                   "INNER JOIN Ruta as r ON r.id_ruta = rr.id_ruta "
                   "WHERE rr.aprobacion = 1 AND r.id_conductor = %s", (id_conductor,))
        pasajeros_data = CC.fetchall()

        return render_template('info_pasajero.html', pasajeros=pasajeros_data, id_conductor=id_conductor)
    
@app.route('/sol_aceptada', methods=['GET'])
def sol_aceptada():
    CC = mysql.connection.cursor()

    # Supongo que hay una sesión de pasajero almacenada en la sesión.
    id_pasajero = session.get("Pasajero")

    # Obtener el ID de la ruta solicitada por el pasajero
    CC.execute("SELECT id_ruta FROM Relacion_ruta WHERE id_pasajero = %s", (id_pasajero,))
    id_ruta_pasajero = CC.fetchone()

    # Obtener información del conductor asociado a la ruta
    CC.execute("SELECT i.nombre_completo, c.matricula, i.nombre_carrera, i.sexo, c.telefono "
               "FROM Conductor as c "
               "INNER JOIN vw_inscripciones as i ON c.matricula = i.matricula "
               "INNER JOIN Ruta as r ON c.id_conductor = r.id_conductor "
               "WHERE r.id_ruta = %s", (id_ruta_pasajero,))
    datos_conductor = CC.fetchall()

    # Obtener información del auto asociado a la ruta
    CC.execute("SELECT a.marca, a.modelo, a.placa FROM Autos as a "
               "INNER JOIN Relacion_autos as ra ON a.id_auto = ra.id_auto "
               "INNER JOIN Ruta as r ON ra.id_conductor = r.id_conductor "
               "WHERE r.id_ruta = %s", (id_ruta_pasajero,))
    datos_auto = CC.fetchall()

    return render_template('SolAceptadaPasajero.html', conductor=datos_conductor, auto=datos_auto, id_ruta=id_ruta_pasajero)

@app.route("/AdminPasajeros")
def rutas():
    CC = mysql.connection.cursor()
    CC.execute("SELECT nombre_completo, matricula, correo_electronico, sexo, nombre_carrera FROM vw_inscripciones WHERE id_rol = 2")  # Selecciona los pasajeros
    pasajeros = CC.fetchall()  
    comentarios_por_pasajero = {}
    for pasajero in pasajeros:  # Iterar sobre los conductores para obtener los comentarios del administrador para cada uno
        CC.execute("SELECT id, comentario FROM Administrador WHERE id_pasajero = %s", (pasajero[1],))
        comentarios_admin1 = CC.fetchall()
        comentarios_por_pasajero[pasajero[1]] = comentarios_admin1

    return render_template('AdminPasajeros.html', pasajeros=pasajeros,comentarios_por_pasajero=comentarios_por_pasajero)

@app.route('/enviar_comentarioPasajero', methods=['POST'])
def enviar_comentarioPasajero():
    if request.method == 'POST':
        pasajero_id = request.form['pasajero_id']
        comentario = request.form['message-text']
        
        # Aquí debes insertar el comentario en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO Administrador (comentario, id_pasajero) VALUES (%s, %s)", (comentario, pasajero_id))
        mysql.connection.commit()
        cursor.close()

        # Redirige a la página desde donde se envió el comentario
        return redirect(request.referrer)

@app.route('/eliminar_comentarioPasajero', methods=['POST'])
def eliminar_comentarioPasajero():
    if request.method == 'POST':
        comentario_id = request.form.get('comentario_id')
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM Administrador WHERE id = %s", (comentario_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect('/AdminPasajeros')


#Traer los nombres de los conductores que ya realizaron un registro de la ruta
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    CC= mysql.connection.cursor()
    CC.execute("select r.nombre_ruta, r.tipo_ruta, i.nombre_completo, i.matricula, c.telefono, r.id_ruta from Conductor as c inner join Ruta as r on c.id_conductor=r.id_conductor inner join vw_inscripciones as i on i.matricula=c.matricula where primer_ingreso_flag=1")
    conductores=CC.fetchall()
    CC.execute("select * from Paradas")
    paradas=CC.fetchall()
    CC.execute("select r.nombre_ruta, r.tipo_ruta, i.nombre_completo, i.matricula,i.nombre_carrera,i.sexo,i.correo_electronico, c.telefono, r.id_ruta from Conductor as c inner join Ruta as r on c.id_conductor=r.id_conductor inner join vw_inscripciones as i on i.matricula=c.matricula where primer_ingreso_flag=1")
    conductores1=CC.fetchall()
    comentarios_por_conductor = {}
    for conductor in conductores:  # Iterar sobre los conductores para obtener los comentarios del administrador para cada uno
        CC.execute("SELECT id,comentario FROM Administrador WHERE id_conductor = %s", (conductor[3],))
        comentarios_admin = CC.fetchall()
        comentarios_por_conductor[conductor[3]] = comentarios_admin

    return render_template('Administrador.html', conductores=conductores, paradas=paradas, conductores1=conductores1, comentarios_por_conductor=comentarios_por_conductor)

@app.route('/enviar_comentario', methods=['POST'])
def enviar_comentario():
    if request.method == 'POST':
        conductor_id = request.form['conductor_id']
        comentario = request.form['message-text']
        
        # Aquí debes insertar el comentario en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO Administrador (comentario, id_conductor) VALUES (%s, %s)", (comentario, conductor_id))
        mysql.connection.commit()
        cursor.close()

        # Redirige a la página desde donde se envió el comentario
        return redirect(request.referrer)

@app.route('/eliminar_comentario', methods=['POST'])
def eliminar_comentario():
    if request.method == 'POST':
        comentario_id = request.form.get('comentario_id')
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM Administrador WHERE id = %s", (comentario_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect('/admin')

# Ruta para calificaciones de pasajeros
@app.route('/calificaciones/pasajero')
def calificaciones_pasajero():
    CC = mysql.connection.cursor()

     # Supongo que hay una sesión de pasajero almacenada en la sesión.
    id_pasajero = session.get("Pasajero")

    # Obtener el ID de la ruta solicitada por el pasajero
    CC.execute("SELECT id_ruta FROM Relacion_ruta WHERE id_pasajero = %s", (id_pasajero,))
    id_ruta_pasajero = CC.fetchone()

    # Obtener información del conductor asociado a la ruta
    CC.execute("SELECT i.nombre_completo, c.matricula, i.nombre_carrera, i.sexo, c.telefono, i.nss, i.correo_electronico "
               "FROM Conductor as c "
               "INNER JOIN vw_inscripciones as i ON c.matricula = i.matricula "
               "INNER JOIN Ruta as r ON c.id_conductor = r.id_conductor "
               "WHERE r.id_ruta = %s", (id_ruta_pasajero,))
    datos_conductor = CC.fetchall()

    return render_template('CalificacionPasajero.html', conductor=datos_conductor, id_ruta=id_ruta_pasajero)

# Ruta para calificaciones de conductores
@app.route('/calificaciones/conductor')
def calificaciones_conductor():
    solicitud_id = request.form.get('solicitud_id')
    accion = request.form.get('accion')
    CC = mysql.connection.cursor()

    if accion == 'aceptar':
        CC.execute("UPDATE Relacion_ruta SET aprobacion = 1, estado = 'Aceptado' WHERE id_pasajero = %s", (solicitud_id,))
        mysql.connection.commit()

    # Obtén el ID del conductor que inició sesión
    id_conductor = session.get("Conductor")
    print("ID del conductor en la sesión:", id_conductor)

    # Verifica que el ID del conductor esté presente en la sesión
    if id_conductor is not None:
        # Selecciona solo las solicitudes aprobadas para ese conductor
        CC.execute("SELECT i.nombre_completo, i.matricula, i.nombre_carrera, i.sexo, i.correo_electronico, p.telefono FROM vw_inscripciones as i "
                   "INNER JOIN Pasajero as p ON i.matricula = p.matricula "
                   "INNER JOIN Relacion_ruta as rr ON p.id_pasajero = rr.id_pasajero "
                   "INNER JOIN Ruta as r ON r.id_ruta = rr.id_ruta "
                   "WHERE rr.aprobacion = 1 AND r.id_conductor = %s", (id_conductor,))
        pasajeros = CC.fetchall()

  
        return render_template('CalificacionConductor.html', pasajeros=pasajeros, id_conductor=id_conductor)


@app.route('/enviar_comentarioFinal', methods=['POST'])
def enviar_comentario_final():
    if request.method == 'POST':
        conductor_id = request.form.get('conductor_id')
        comentario_final = request.form.get('message-text')

        
        # Aquí debes insertar el comentario en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO Administrador (comentario_final, id_conductor) VALUES (%s, %s)", (comentario_final, conductor_id))
        mysql.connection.commit()
        cursor.close()

        # Redirige a la página desde donde se envió el comentario
        return redirect(request.referrer)
    
                           
#ejecución del servidor en el puerto 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000, debug=True)      