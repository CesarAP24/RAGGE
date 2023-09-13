# RAGGE
Register And Grade Gestor

## Description
RAGGE (Register and Grade Gestor) es un gestor de notas y cursos para el uso estudiantil. Este se conforma de tres REST APIs y un front-end.


# RAGGE APIs:

- Manejo de Usuarios 	("ragge/api-users")
	El manejo de usuarios se encarga de otorgar permisos y nombres a los profesores, directores y alumnos. De forma que se mantienen abiertos a la información que les pertenece.
	
- Manejo de Notas	("ragge/api-grades")
	El manejo de notas es independiente del de usuarios, ya que solo registra notas de ciertos alumnos.

- Manejo de Cursos	("ragge/api-cursos")
	El manejo de cursos está definido para la creación, suspención y/o eliminación de cursos. Solo profesores pueden crear los cursos, por lo que necesitan una autenticación.
	
# RAGGE Front-end:

//por definir