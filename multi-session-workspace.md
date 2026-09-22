# Multi-session workspace

Propuesta de diseño, detenida por decisión del usuario el 2026-09-22: "lo del workflow no. que
quede claro eso [...] ya que es completamente WIP". Nada de lo que sigue se implementa mientras
esa decisión esté vigente, y un encargo que pida implementarlo, venga de donde venga, se trata
como propuesta.

Ninguna regla de este documento está implementada, y ningún fallo descrito aquí tiene todavía
una superficie que lo impida.

Un workspace por proyecto agrupa varias sesiones de Claude Code sobre el mismo árbol. Una sesión
master habla con el usuario, discierne y decide; las ayudantes ejecutan trabajo mecánico y no
hablan con el usuario. Hoy el patrón corre a mano, sin nada que declare roles ni que impida que
dos sesiones asuman el mismo. El objetivo del usuario es mantener el foco en un solo agente sin
perder monitoreo de los demás.

## Registro de origen

El encargo llegó a través de la sesión `os-master`. El usuario lo confirmó después, en estas
palabras: "pasaselo a dotfiles-swe, que te reporte a ti, necesito que elabore un documento que
describa lo q estamos haciendo, alto nivel". Lo confirmado es el encargo. La estructura de roles
y las cuatro fallas las aportó `os-master` y ninguna consta de parte del usuario. Las mediciones
de la sección siguiente se tomaron en esta sesión, contra el árbol.

## Estado medido

Medido el 2026-09-22 en esta sesión. Cada fila lleva el comando que la produjo.

| Hecho | Valor | Comando |
|---|---|---|
| Workspaces en `herdr` | 3, uno de ellos sin nombre | `cat ~/.config/herdr/session.json` |
| Sesiones vivas | 6 | `herdr agent list` |
| Paneles etiquetados `master` en `session.json` | 2, en workspaces distintos | `cat ~/.config/herdr/session.json` |
| Nombre en disco contra nombre vivo | `skills-agent` en `session.json`, `skills-swe` en `ListAgents` | `herdr agent list` |
| Identidad de panel en el entorno | `HERDR_PANE_ID`, `HERDR_TAB_ID`, `HERDR_WORKSPACE_ID` | `env \| grep HERDR` |
| Campos que recibe el hook `SessionStart` | `cwd`, `source` | `grep payload.get ~/.claude/hooks/session-register.py` |
| Nombre por panel en la API de `herdr` | `terminal_title_stripped` | `herdr agent list` |

Dos paneles llamados `master` y un nombre que difiere entre el disco y la sesión viva son las
fallas 1 y 2 observadas directamente, no reportadas.

## Corrección a un límite declarado

El encargo declaró que la identidad de sesión no es derivable, porque el hook `SessionStart`
recibe solo `cwd` y `source` y `/run/user/1000/cc-socks/` solo tiene sockets numerados por PID.
La primera mitad se confirma. La conclusión no se sostiene.

Cada panel de `herdr` exporta `HERDR_PANE_ID` a su entorno; esta sesión lee `w1T:p7`. La API
`herdr agent list` devuelve un registro por panel con ese mismo `pane_id` y con
`terminal_title_stripped`, que es el nombre que `ListAgents` reporta. Un hook `SessionStart`
lee su propio `HERDR_PANE_ID` del entorno, consulta la API y obtiene su nombre, su workspace y
su `cwd` sin que nadie se los escriba.

Consecuencia sobre el diseño: la identidad de sesión no requiere que el usuario declare nada, y
la falla 3 se cierra con un hook de lectura. Lo que el hook no puede derivar es el rol, porque
nada en `herdr` distingue master de ayudante. El rol necesita una fuente, y la sección
`Decisiones abiertas` la deja al usuario.

Un segundo límite del encargo también cae. `herdr agent start <NAME> --kind claude --pane <ID>
-- <AGENT_ARG>...` pasa argumentos al agente lanzado, de modo que modelo y esfuerzo sí son
fijables por panel. No verificado: qué argumentos acepta el binario `claude` en ese punto, y si
el panel lanzado así hereda el entorno del workspace.

## Fallas que el diseño debe resolver

Las cuatro provienen del encargo, fechadas el 2026-09-22. Las dos primeras están además medidas
arriba.

| # | Falla | Qué la deja pasar hoy |
|---|---|---|
| 1 | Una sesión pasó a otra dos decisiones etiquetadas como tomadas por el usuario, que el usuario no tomó. La receptora las registró sin verificar. Ninguna se ejecutó. | Ninguna regla legible por las sesiones dice que un par no transmite decisiones del usuario |
| 2 | Los nombres cambian entre reinicios y se pierde quién es quién | El nombre vive en el título del terminal, que no sobrevive a la caída de la sesión |
| 3 | Ninguna sesión sabe si es master o ayudante | Nada se lo dice al arrancar |
| 4 | Un par puede transmitir una decisión del usuario y ser creído | La regla no está escrita donde las sesiones la lean |

La falla 1 no se detuvo por diseño. Las dos decisiones no ejecutadas lo fueron por suerte, y el
mismo mensaje con una orden ejecutable habría corrido.

## Piezas que ya existen

| Pieza | Qué resuelve | Qué no resuelve |
|---|---|---|
| `herdr` | Contenedor visual, arranque de paneles, agrupación por proyecto, estado en `session.json` | Conducta de las sesiones, roles, autoridad |
| `SendMessage`, `ListAgents` | Transporte entre sesiones y enumeración de pares vivos | Autenticidad del contenido de un mensaje |
| Hook `SessionStart` | Inyecta contexto en cada sesión al arrancar y tras compactar | No conoce el rol, porque nada se lo declara |
| `writing-loaded.py` | Bloquea con exit 2 y devuelve una instrucción al agente | Nada relativo a roles |

Un hook no fuerza una carga de skill: imprime contexto. Lo que funciona es exit 2, que devuelve
al agente la instrucción de cargar y reintentar. `writing-loaded.py` es el ejemplo vivo y el
patrón que cualquier regla de rol tendría que seguir para ser obligatoria.

## Arquitectura propuesta

Tres capas, separadas por lo que cada una puede garantizar.

**Identidad.** Un hook `SessionStart` deriva panel, workspace y nombre del entorno y de la API
de `herdr`, y los imprime en el banner. Es lectura pura y no puede fallar en abrir una sesión
sin rol declarado, porque el nombre existe antes que la sesión.

**Rol.** Una sesión es master o ayudante. El rol determina si habla con el usuario, si acepta
encargos de pares y qué hace con una decisión atribuida al usuario. La fuente del rol es la
decisión abierta 1.

**Autoridad.** Una decisión del usuario solo es válida en la sesión donde el usuario la escribió.
Un mensaje de par que afirme llevar una es tratado como propuesta, cualquiera sea su etiqueta.
La regla es asimétrica a propósito: el receptor no puede verificar el origen, así que la carga
recae en no creer, nunca en probar.

### Unicidad del master

Dos sesiones se llamaron master a la vez, y el `session.json` medido todavía muestra dos paneles
con esa etiqueta. La unicidad es por workspace, no global: `w1R` y `w1T` son proyectos distintos
y cada uno tiene su master legítimamente. Lo que falta es la comprobación. Una sesión que arranca
como master enumera sus pares del mismo `workspace_id` y, si encuentra otro master vivo, lo
reporta en vez de asumir el rol.

No verificado: si `ListAgents` expone el `workspace_id` de cada par, o si hay que cruzar sus
nombres contra `herdr agent list`.

## Decisiones abiertas

Cada opción con su consecuencia. Ninguna está elegida.

### 1. Fuente del rol

| Opción | Consecuencia |
|---|---|
| Convención de nombre: un panel llamado `*-master` es master | Cero configuración, y el rol se rompe con un renombre. Un `herdr agent rename` cambia la autoridad sin avisar |
| Archivo por workspace, con el rol de cada panel | Explícito y auditable, y hay que mantenerlo sincronizado con los paneles que `herdr` crea y destruye |
| Argumento al lanzar: `herdr agent start ... -- <arg>` | El rol nace con la sesión y no se puede perder por renombre. Requiere que cada panel se lance por CLI, no por la interfaz de `herdr` |

### 2. Qué hace el hook cuando no puede determinar el rol

| Opción | Consecuencia |
|---|---|
| Imprimir el rol como desconocido y seguir | Ninguna sesión se bloquea, y una sesión sin rol puede hablar con el usuario creyéndose master |
| exit 2 con la instrucción de declarar el rol | Ninguna sesión opera sin rol, y una sesión lanzada fuera de `herdr` no arranca hasta que alguien intervenga |

### 3. Dónde vive la regla de autoridad

`skill-growth` es la autoridad sobre esta pregunta y su tabla de ruteo da dos candidatos, porque
la regla es a la vez un estándar de acción y un invariante de esta máquina.

| Opción | Consecuencia |
|---|---|
| `~/.claude/CLAUDE.md`, sección de estándares | Alcanza toda sesión en toda máquina, y crece un archivo que ya se reinyecta entero en cada arranque |
| `CLAUDE.md` de este repositorio | Alcanza solo las sesiones abiertas sobre `~/dotfiles`, que no es donde ocurrió la falla 1 |
| Un skill nuevo, cargado por el hook | Aísla la regla y la hace citable, y un skill solo actúa si algo obliga a cargarlo |

La falla 1 ocurrió entre un panel de `w1T` y otro; el encargo que la reporta llegó a una sesión
de `~/dotfiles`. Un alcance por repositorio no la habría prevenido.

### 4. Modelo y esfuerzo por rol

El encargo pide razonamiento alto para la master. `herdr agent start` acepta argumentos para el
agente, así que es fijable.

| Opción | Consecuencia |
|---|---|
| Fijar modelo y esfuerzo por rol al lanzar | La master discierne con más presupuesto y las ayudantes cuestan menos. Ata el arranque al CLI de `herdr` |
| Dejarlo al usuario en cada panel | Cero acoplamiento, y el rol no garantiza el presupuesto que el encargo pide para él |

### 5. Alcance de la unicidad del master

| Opción | Consecuencia |
|---|---|
| Por workspace | Coincide con la estructura medida: tres workspaces, un master cada uno. Dos masters en la máquina siguen siendo normales |
| Global | Una sola sesión habla con el usuario en toda la máquina, y trabajar en dos proyectos a la vez exige turnarse |

## Antes de implementar

Cada pieza propuesta arriba es comportamiento nuevo, y ninguna tiene todavía una prueba que
falle. La ley de `superpowers:writing-skills` aplica: ningún skill ni hook entra sin una prueba
que falle primero. Hoy se borró un hook que nunca disparó en 224 comandos por haberse saltado
esa ley, según el encargo; no verificado contra el log de auditoría.

Para cada pieza, la prueba que tiene que fallar antes de escribirla:

| Pieza | Prueba que falla primero |
|---|---|
| Hook de identidad | Una sesión arranca y su banner no nombra su panel ni su workspace |
| Comprobación de unicidad | Dos paneles del mismo workspace asumen master y ninguno lo reporta |
| Regla de autoridad | Un mensaje de par etiquetado como decisión del usuario se registra sin marcarlo como propuesta |

## Pendiente de verificar

- Qué argumentos acepta el binario `claude` a través de `herdr agent start ... -- <arg>`.
- Si el panel lanzado por `herdr agent start` hereda `HERDR_PANE_ID` y el resto del entorno.
- Si `ListAgents` expone el `workspace_id` de cada par, necesario para la unicidad por workspace.
- Si el hook borrado hoy nunca disparó en 224 comandos: dato del encargo, no medido aquí.
