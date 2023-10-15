create database carpool;
use carpool;
DROP TABLE IF EXISTS `vw_inscripciones`;
/*!50001 DROP VIEW IF EXISTS `vw_inscripciones`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `vw_inscripciones` (
 `id` tinyint NOT NULL,
  `matricula` varchar(15) NOT NULL PRIMARY KEY,
  `nombre_completo` varchar(100) NOT NULL,
  `cuatrimestre` tinyint NOT NULL,
  `nombre_carrera` varchar(50) NOT NULL,
  `sexo` varchar(10) NOT NULL,
  `correo_electronico` varchar(50) NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `nss` varchar(20) NOT NULL,
  `clave_ingreso` varchar(16) NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

create table Conductor(
id_conductor int not null primary key auto_increment,
matricula varchar(15),
primer_ingreso_flag tinyint default 0,
telefono varchar(10),
foto mediumblob,
INE mediumblob,
CredencialUPQ mediumblob
);

create table Autos(
id_auto int not null primary key auto_increment,
placa varchar(200),
modelo varchar(200),
marca varchar(200),
color varchar(200),
poliza varchar(200),
fecha_vencimiento date,
lugares_disponibles int,
Tarjeta_circulacion mediumblob,
capacidad int,
espacios_disponibles int,
estatus tinyint default 0
);

create table Relacion_autos(
id int not null primary key auto_increment,
id_conductor int,
id_auto int,
foreign key (id_conductor) references Conductor(id_conductor) on delete cascade on update cascade,
foreign key (id_auto) references Autos(id_auto) on delete cascade on update cascade
);

create table Ruta(
id_ruta int not null primary key auto_increment,
nombre_ruta varchar(100),
id_conductor int,
tipo_ruta varchar(15),
descripcion_completa text,
foreign key (id_conductor) references Conductor(id_conductor) on delete cascade on update cascade
);

create table Paradas(
id_parada int not null primary key auto_increment,
punto_referencia text not null,
descripcion text,
hora time,
id_ruta int,
foreign key (id_ruta) references Ruta(id_ruta) on delete cascade on update cascade
);

create table Pasajero(
id_pasajero int not null primary key auto_increment,
matricula varchar(15),
telefono varchar(10)
);

create table Relacion_ruta(
id int not null primary key auto_increment,
id_ruta int,
id_pasajero int,
aprovacion tinyint default 0,
foreign key (id_ruta) references Ruta(id_ruta) on delete cascade on update cascade,
foreign key (id_pasajero) references Pasajero(id_pasajero) on delete cascade on update cascade
);

create table Administrador(
id varchar(15),
password binary
);

insert into vw_inscripciones (id, matricula, nombre_completo, cuatrimestre, nombre_carrera, sexo, correo_electronico, fecha_nacimiento, nss,clave_ingreso) 
	values 	(1,'121039302','Luis Guillermo Custodio Serrano',7,'Sistemas Computacionales','Hombre','121039302@upq.edu.mx','1995-01-04','96109537918','123456');
insert into vw_inscripciones (id, matricula, nombre_completo, cuatrimestre, nombre_carrera, sexo, correo_electronico, fecha_nacimiento, nss,clave_ingreso) 
	values 	(2,'121037815','Angel Cristian Juárez Martínez',7,'Sistemas Computacionales','Hombre','121037815@upq.edu.mx','1999-11-14','95687512364','cz7575'),
			(3,'121039875','Edieneth Garduño Calderon',4,'Negocios Internacionales','Mujer','121039875@upq.edu.mx','2001-04-22','96109556789','delunoalocho8'),
			(4,'121014865','Eleana Martínez Salazar',1,'Mecatrónica','Mujer','121014865@upq.edu.mx','2000-12-12','961092531475','13972846');