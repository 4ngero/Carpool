#importación del framework
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL

#Para subir archivo tipo foto al servidor
from werkzeug.utils import secure_filename 
import os

#inicialización del APP
app= Flask(__name__)
#conexion
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='cz757002'
app.config['MYSQL_DB']='carpool'
app.secret_key= 'mysecretkey'
mysql= MySQL(app)

@app.route('/')
def index():
    if not session.get("Matricula"):
            return redirect("/login")
    return redirect("/logout")

#iniciar sesion
@app.route("/login", methods=["POST", "GET"])
def login():
    CC=mysql.connection.cursor()
    if request.method == "POST":
        VMatricula=request.form['txtMatricula']
        VPassword=request.form['txtPassword']
        VTipo=request.form['txtTipo']
        CC.execute("select Matricula from vw_inscripciones where matricula='"+VMatricula+"' and clave_ingreso='"+VPassword+"';")
        Vid=CC.fetchone()
        Vnone=str(Vid)
        if Vnone=='None':
            flash('Usuario y/o contraseña equivocados, vuelva a intentarlo')
            return redirect("/login")
        else:
            session["Matricula"] = request.form.get("txtMatricula")
            #rol de conductor
            if VTipo=="1":
                session["Rol"]=1
                CC.execute("select id_conductor from conductor where matricula='"+session["Matricula"]+"';")
                Vid=CC.fetchone()
                Vnone=str(Vid)
                if Vnone=='None':
                    CC.execute("insert into conductor(matricula) values (%s);",(session["Matricula"],))
                    mysql.connection.commit()
                    CC.execute("select id_conductor from conductor where matricula='"+session["Matricula"]+"';")
                    Vid=CC.fetchone()
                    session["Conductor"]=Vid[0]
                else:
                    CC.execute("select id_conductor from conductor where matricula='"+session["Matricula"]+"';")
                    Vid=CC.fetchone()
                    session["Conductor"]=Vid[0]
                return redirect("/conductor")
            #rol de pasajero
            if VTipo=="2":
                CC.execute("select id_pasajero from pasajero where matricula='"+session["Matricula"]+"';")
                Vid=CC.fetchone()
                Vnone=str(Vid)
                if Vnone=='None':
                    CC.execute("insert into pasajero(matricula) values (%s);",(session["Matricula"],))
                    mysql.connection.commit()
                    CC.execute("select id_pasajero from pasajero where matricula='"+session["Matricula"]+"';")
                    Vid=CC.fetchone()
                    session["Pasajero"]=Vid[0]
                else:
                    CC.execute("select id_pasajero from pasajero where matricula='"+session["Matricula"]+"';")
                    Vid=CC.fetchone()
                    session["Pasajero"]=Vid[0]
                return redirect("/pasajero")
            #rol de administrador
            if VTipo=="3":
                session["Rol"]=3
                return redirect("/admin")
    return render_template("login.html")

#cerrar sesion
@app.route("/logout")
def logout():
    session["Matricula"] = None
    session["Conductor"] = None
    session["Pasajero"] = None
    session["Admin"] = None
    session["Rol"] = None
    return redirect("/login")

#home de conductor
@app.route('/conductor')
def conductor():
    if not session.get("Matricula"):
            return redirect("/login")
    CC=mysql.connection.cursor()
    CC.execute("select * from conductor where id_conductor='"+str(session["Conductor"])+"';")
    Vid=CC.fetchone()
    if Vid[2]==0:
        return redirect("/conductor/perfil")
    else:
        CC.execute("select * from Ruta where id_conductor=%s",(session["Conductor"],))
        rutas=CC.fetchall()
        CC.execute("select id_ruta from Ruta where id_conductor=%s",(session["Conductor"],))
        Vnone=str(CC.fetchone())
        CC.execute("select punto_referencia,descripcion,hora,p.id_ruta from paradas as p inner join ruta as r on p.id_ruta=r.id_ruta where r.id_conductor=%s",(session["Conductor"],))
        paradas=CC.fetchall()
        CC.execute("select id_pasajero from ruta inner join relacion_ruta on ruta.id_ruta=relacion_ruta.id_ruta where id_conductor=%s",(session["Conductor"],))
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
        return render_template('HomeConductor.html',rutas=rutas,Vnone=Vnone,paradas=paradas,pasajeros=pasajeros)

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
    CC.execute("select placa,modelo,marca,color,lugares_disponibles from relacion_autos as ra inner join autos as a on ra.id_auto=a.id_auto where id_conductor=%s",(session["Conductor"],))
    autos=CC.fetchall()
    CC.execute("select telefono from conductor where id_conductor=%s",(session["Conductor"],))
    tel=CC.fetchone()
    telefono=tel[0]
    return render_template('Perfil2.html',datos=datos_personales,nombre=nombre,apellidos=temp,autos=autos,telefono=telefono)

#insertar telefono
@app.route('/actualizar_telefonoc', methods=['POST'])
def actualizar_telefonoc():
    VTelefono=request.form['txtTelefono']
    CC= mysql.connection.cursor()
    CC.execute("update conductor set telefono=%s where id_conductor=%s",(VTelefono,session["Conductor"],))
    mysql.connection.commit()
    return redirect("/conductor/perfil")

#insertar auto
@app.route('/ingresar_auto', methods=['POST'])
def ingresar_auto():
    if request.method == 'POST':
        VMarca=request.form['txtMarca']
        VModelo=request.form['txtModelo']
        VColor=request.form['txtColor']
        VCapacidad=request.form['txtCapacidad']
        VPlaca=request.form['txtPlaca']
        
        """ VTarjeta=request.files['imgTarjeta']
        VCredencial=request.files['imgCredencial']
        VINE=request.files['imgINE']
        VPoliza=request.files['imgPoliza'] """
        
        CC= mysql.connection.cursor()
        CC.execute("insert into autos(placa,modelo,marca,color,lugares_disponibles) values (%s,%s,%s,%s,%s);",(VPlaca,VModelo,VMarca,VColor,VCapacidad))
        
        """ CC.execute("update conductor set INE="+VINE+" where matricula='%s';",str(session["Matricula"]))
        CC.execute("update conductor set CredencialUPQ="+VCredencial+" where matricula=%s;",str(session["Matricula"])) """ 
        CC.execute("select id_auto FROM autos WHERE placa=%s",(str(VPlaca),))
        autoid=CC.fetchone()
        CC.execute("insert into relacion_autos(id_conductor,id_auto) values(%s,%s);",(session["Conductor"],autoid[0],))
        CC.execute("update conductor set primer_ingreso_flag=1")
        mysql.connection.commit()
        """
        CC.execute("SELECT matricula FROM vw_inscripciones where matricula = "+session["Matricula"]+";")
        
        matriculaUtil = CC.fetchone()
        matriculaUtil = CC.fetchone()[1].replace("'", '').replace('"', '').replace('(', '').replace(')', '').replace(',', '')
        print(matriculaUtil)
        """
        CC.execute("SELECT matricula FROM vw_inscripciones WHERE matricula = " + str(session["Matricula"]) + ";")
        matriculaUtil = CC.fetchone()

        if matriculaUtil is not None:
            matriculaUtil = matriculaUtil[0].replace("'", '').replace('"', '').replace('(', '').replace(')', '').replace(',', '')

        tarjeta_circula = request.files['tarjeta_circula']
        credencial_UPQ = request.files['credencial_UPQ']
        credencial_INE = request.files['credencial_INE']
        poliza = request.files['poliza']
        vehiclePhoto = request.files['vehiclePhoto']
        
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
        
        if vehiclePhoto:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(vehiclePhoto.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = str(matriculaUtil) +"_"+ str(VPlaca) + "_Vehiculo" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            vehiclePhoto.save(upload_path)
        
        
    return redirect('/conductor/perfil')
"""
#insertar documentos
@app.route('/insertar_documentos', methods=['POST', 'GET'])
def insertarDocumentos():
    if request.method == 'POST':
        CC=mysql.connection.cursor()
        CC.execute("SELECT * FROM vw_inscripciones where matricula = '"+session["Matricula"]+"';")
        
        matriculaUtil = CC.fetchall()
        tarjeta_circula = request.files['tarjeta_circula']
        credencial_UPQ = request.files['credencial_UPQ']
        credencial_INE = request.files['credencial_INE']
        poliza = request.files['poliza']
        
        if tarjeta_circula:
            basepath = os.path.dirname(__file__)
            filename = secure_filename(tarjeta_circula.filename)
            extension  = os.path.splitext(filename)[1]
            nombreFile = matriculaUtil + "tarjeta_circulacion" + extension
            
            upload_path = os.path.join(basepath, 'static/archivos', nombreFile)
            tarjeta_circula.save(upload_path)
"""
#Visualizar documentos del auto
@app.route('/documentos_auto')
def view_documento():
    CC = mysql.connection.cursor()
    CC.execute("SELECT matricula FROM vw_inscripciones WHERE matricula = " + str(session["Matricula"]) + ";")
    matriculaUtils = CC.fetchone()
    CC.execute("select placa from relacion_autos as ra inner join autos as a on ra.id_auto=a.id_auto where id_conductor=%s",(session["Conductor"],))
    placaUtils = CC.fetchone()
    return render_template("Perfil2.html", placaUtils=placaUtils, matriculaUtils=matriculaUtils)

           
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
    CC.execute("insert into paradas(punto_referencia,descripcion,hora,id_ruta) values (%s,%s,%s,%s)",(VReferencia,VDescripcion,VHora,id,))
    CC.execute("update Ruta set descripcion_completa=%s where id_ruta=%s",(VDesGral,id,))
    mysql.connection.commit()
    id2=id
    return redirect(url_for('registrar_parada',id=id2))

#pagina principal pasajero 
@app.route('/pasajero')
def pasajero():
    CC=mysql.connection.cursor()
    CC.execute("select * from relacion_ruta where id_pasajero='"+str(session["Pasajero"])+"';")
    Vid=CC.fetchall()
    Vnone=str(Vid)
    print(Vnone)
    if Vnone=='None':
        return redirect("/pasajero/ruta")
    else:
        CC.execute("select telefono from Pasajero where id_pasajero=%s",(session["Pasajero"],))
        telefono=CC.fetchone()
        #listado de conductores
        CC.execute("select id_ruta from relacion_ruta where id_pasajero=%s",(session["Pasajero"],))
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
        CC.execute("select matricula from conductor where id_conductor in (%s)",(str(id_conductores),))
        aux=CC.fetchall()
        matriculas=[]
        for a in aux:
            matriculas.append(a[0])
        CC.execute("select * from vw_inscripciones where matricula in (%s)",(str(matriculas),))
        datos_personales2=CC.fetchall()
        CC.execute("select punto_referencia,descripcion,hora,p.id_ruta from paradas as p inner join ruta as r on p.id_ruta=r.id_ruta where r.id_conductor in (%s)",(str(id_conductores),))
        paradas=CC.fetchall()
        CC.execute("select matricula, nombre_completo, cuatrimestre, nombre_carrera, sexo, correo_electronico, fecha_nacimiento, nss from vw_inscripciones where matricula='"+session["Matricula"]+"';")
        datos_personales=CC.fetchone()
        CC.execute("select * from ruta where id_ruta in (%s)",(str(id_rutas),))
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
        CC.execute("select placa,modelo,marca,color,lugares_disponibles,id_conductor from relacion_autos as ra inner join autos as a on ra.id_auto=a.id_auto where id_conductor in (%s)",(str(id_conductores),))
        autos=CC.fetchall()    
        return render_template('HomePasajero.html',Vnone=Vnone,paradas=paradas,nombre=nombre,apellidos=temp,datos=datos_personales,telefono=telefono,datos2=datos_personales2,autos=autos,rutas=rutas)

#registrar ruta pasajero    
@app.route('/pasajero/ruta')
def reservar_ruta():
    if not session.get("Matricula"):
        return redirect("/login")
    CC= mysql.connection.cursor()
    CC.execute("select r.nombre_ruta, r.tipo_ruta, i.nombre_completo, i.matricula, c.telefono, r.id_ruta from conductor as c inner join ruta as r on c.id_conductor=r.id_conductor inner join vw_inscripciones as i on i.matricula=c.matricula where primer_ingreso_flag=1")
    conductores=CC.fetchall()
    CC.execute("select * from paradas")
    paradas=CC.fetchall()
    return render_template('Rutas.html',conductores=conductores,paradas=paradas)

@app.route('/reserva_ruta/<id>')
def reserva_ruta(id):
    if not session.get("Matricula"):
        return redirect("/login")
    CC= mysql.connection.cursor()
    CC.execute("insert into relacion_ruta(id_ruta,id_pasajero) values (%s,%s)",(id,session["Pasajero"],))
    mysql.connection.commit()
    return redirect("/pasajero")

#actualizar_telefono
@app.route('/actualizar_telefono', methods=['POST'])
def actualizar_telefono():
    VTelefono=request.form['txtTelefono']
    CC= mysql.connection.cursor()
    CC.execute("update pasajero set telefono=%s where id_pasajero=%s",(VTelefono,session["Pasajero"],))
    mysql.connection.commit()
    return redirect("/pasajero")

#solicitudes
@app.route('/conductor/solicitudes')
def solicitudes():
    CC= mysql.connection.cursor()
    CC.execute("select pasajero.id_pasajero,nombre_ruta,tipo_ruta,i.matricula,nombre_completo,sexo from ruta inner join relacion_ruta as rr on ruta.id_ruta=rr.id_ruta inner join pasajero on rr.id_pasajero=pasajero.id_pasajero inner join vw_inscripciones as i on pasajero.matricula=i.matricula where ruta.id_conductor=%s",(session["Conductor"],))
    solicitudes=CC.fetchall()
    return render_template('Solicitudes.html',solicitudes=solicitudes)

@app.route('/solicitud/<id>')
def solicitud(id):
    CC= mysql.connection.cursor()
    CC.execute("update relacion_ruta set aprovacion=1 where id_pasajero=%s",(id,))
    mysql.connection.commit()
    return redirect("/conductor/solicitudes")

@app.route('/admin')
def admin():
    if not session.get("Matricula"):
            return redirect("/login")
    return render_template('Administrador.html')

#ejecución del servidor en el puerto 5000
if __name__ == '__main__':
    app.run(port=5000, debug=True)      