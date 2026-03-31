# Arquitectura Técnica de GitHub-Mini

Este documento describe la arquitectura propuesta para GitHub-Mini. Está en fase de diseño y abierto a discusión por la comunidad.

## Visión general

GitHub-Mini es una aplicación web independiente que utiliza GitHub como único proveedor de identidad. Su núcleo es un motor de afinidad que conecta personas según intereses reales, y un sistema de debates que es el corazón de la comunidad.

[GitHub OAuth] -> [Frontend React] -> [API (Python/FastAPI)] -> [PostgreSQL]
                                    ->
                           [Motor de afinidad]
                                    ->
                     [GitHub API (lectura de repos, estrellas)]

## Stack tecnológico

| Capa | Tecnología | Justificación |
|------|------------|---------------|
| Frontend | React + TypeScript | Interfaz moderna, tipado seguro, ecosistema maduro. |
| Backend | Python + FastAPI | Rápido desarrollo, documentación automática, async nativo. |
| Base de datos | PostgreSQL + pgvector | Relacional, robusta, soporte para búsqueda por similitud vectorial. |
| Autenticación | OAuth con GitHub | Única identidad, coherente con la filosofía. |
| Cache / colas | Redis | Sesiones, rate limiting, tareas asíncronas (ej. actualizar perfiles). |
| Infraestructura | Docker + docker-compose (etapa inicial) | Portabilidad, despliegue replicable. |

## Autenticación (GitHub OAuth)

Flujo:
1. Usuario hace clic en "Entrar con GitHub".
2. Redirige a GitHub para autorizar la app.
3. GitHub devuelve un código que se canjea por un token.
4. El token se almacena encriptado en la base de datos.

Datos que guardamos:
- github_id
- github_username
- display_name
- avatar_url
- email (público)
- github_token (encriptado)

Registro:
La cuenta se crea en estado is_active = FALSE. Se activa solo después de que el usuario publique su primer debate.

## Perfil de usuario

Se construye a partir de:
- Datos básicos de GitHub.
- Repositorios públicos (lenguajes, tópicos, estrellas).
- Participación en debates dentro de GitHub-Mini.
- Afiliación universitaria (verificada aparte).

## Motor de afinidad (algoritmo de sugerencias)

Entrada: Vector de intereses del usuario (lenguajes, tópicos de repos, etiquetas de debates en que participó).

Proceso:
1. Extraer características: ["python", "space", "health-tech", "open-source"]
2. Calcular similitud con otros usuarios usando cosine similarity sobre vectores (pgvector).
3. Aplicar reglas de negocio:
   - Priorizar personas con participación reciente.
   - No sugerir al propio usuario.
   - Limitar a usuarios activos (que hayan publicado al menos un debate).

Salida: Lista de sugerencias con explicación en lenguaje natural:
"Te sugerimos a X porque ambos trabajan en energía renovable y marcaron estrella en proyectos similares."

Transparencia: El código del motor será público y el usuario podrá ver los factores que influyeron en cada sugerencia (se almacena en tabla suggestions).

## Sistema de debates

- Cada debate es un hilo público.
- Campos: título, cuerpo, etiquetas (extraídas automáticamente), estado (abierto/cerrado).
- El primer debate del usuario activa su cuenta (filtro de entrada).
- Las etiquetas de los debates alimentan el motor de afinidad.

## Integración con GitHub API

- Lectura: repositorios públicos, estrellas, topics, lenguajes.
- Frecuencia: actualización asíncrona (cada vez que el usuario ingresa o mediante webhooks en el futuro).
- Alcance: solo datos públicos, con consentimiento explícito.

## Esquema de base de datos (tablas principales)

```sql
-- Usuarios
users (
  id UUID PRIMARY KEY,
  github_id INT UNIQUE,
  github_username TEXT,
  display_name TEXT,
  avatar_url TEXT,
  email TEXT,
  github_token TEXT,
  is_active BOOLEAN DEFAULT FALSE,
  affiliation TEXT,
  created_at TIMESTAMP
);

-- Debates
debates (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title TEXT,
  body TEXT,
  tags TEXT[],
  status TEXT,
  created_at TIMESTAMP
);

-- Participación en debates
debate_participation (
  user_id UUID REFERENCES users(id),
  debate_id UUID REFERENCES debates(id),
  type TEXT,
  created_at TIMESTAMP
);

-- Historial de sugerencias
suggestions (
  user_id UUID REFERENCES users(id),
  suggested_user_id UUID REFERENCES users(id),
  score FLOAT,
  reasons JSONB,
  created_at TIMESTAMP


API endpoints (versión inicial)
Endpoint	Método	Descripción
/auth/github	GET	Inicia login con GitHub
/auth/callback	GET	Callback OAuth
/users/me	GET	Perfil del usuario autenticado
/debates	GET	Lista debates (públicos)
/debates	POST	Crear un nuevo debate (si es el primero, activa cuenta)
/debates/{id}	GET	Ver debate con comentarios
/suggestions	GET	Obtener sugerencias para el usuario autenticado
/affiliation/verify	POST	Verificar correo universitario (futuro)
/users/me/export	GET	Exportar todos los datos del usuario
Seguridad y privacidad
Tokens de GitHub: almacenados encriptados (AES-256). Se usan solo para leer datos públicos con consentimiento.

Datos de afinidad: vectores anonimizados para cálculo de similitud, pero vinculados al usuario para explicabilidad.

Exportación de datos: endpoint que devuelve JSON con todos los datos del usuario.

Auditoría: tabla suggestions guarda histórico de sugerencias para verificar ausencia de sesgos.

Despliegue inicial (MVP)
Backend: FastAPI en un VPS pequeño (DigitalOcean, Hetzner) con Docker.

Frontend: React estático servido por Nginx o Vercel.

Base de datos: PostgreSQL + pgvector en el mismo servidor (luego migrar a servicio gestionado).

Dominio: github-mini.org (si está disponible) o un subdominio.

Próximos pasos
Discutir este diseño en un debate abierto.

Elegir stack definitivo tras feedback.

Crear repositorios separados para frontend y backend (o mantener todo en uno).

Configurar entorno de desarrollo con Docker.

Implementar autenticación con GitHub OAuth.

Desarrollar MVP con debates y sugerencias básicas.

Este documento es vivo. Cualquier miembro de la comunidad puede proponer cambios mediante debate abierto.

text

);
