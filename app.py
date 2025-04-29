import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF
import os
import json
import datetime
import re

title = "BaguiAI - Asistente de Redacción IA"
st.set_page_config(page_title=title, layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cargar_usuarios():
    with open("usuarios.json", "r") as f:
        return json.load(f)
    
def guardar_usuarios(usuarios):
    with open("usuarios.json", "w") as f:
        json.dump(usuarios, f, indent=2)

def login():
    st.title("🔐 Iniciar sesión")
    usuarios = cargar_usuarios()
    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario in usuarios and usuarios[usuario] == password:
            st.session_state.usuario = usuario
            st.session_state.autenticado = True
        else:
            st.error("Usuario o contraseña incorrectos")

# Inyectar estilos CSS para landing y responsividad
st.markdown("""<style>
body { margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.landing-wrapper { max-width: 800px; margin: 0 auto; text-align: center; }
.hero { padding: 80px 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.hero h1 { font-size: 64px; margin-bottom: 16px; }
.hero p.subtitle-hero { font-size: 24px; font-weight: bold; margin-top: 8px; }
.stButton { display: flex !important; justify-content: center !important; }
.stButton > button { background-color: #ff7f50 !important; color: white !important; padding: 16px 32px !important; font-size: 20px !important; border-radius: 8px !important; transition: background-color 0.3s ease !important; }
.stButton > button:hover { background-color: #ff6347 !important; }
.cards { display: flex; flex-direction: row; justify-content: center; gap: 24px; padding: 40px 20px; }
.card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 220px; }
.card h3 { font-size: 18px; color: #333; margin-bottom: 12px; }
.card p { font-size: 14px; color: #555; margin: 0; }
footer { text-align: center; padding: 16px; color: #888; font-size: 14px; border-top: 1px solid #eee; }
footer a { margin: 0 12px; color: #764ba2; text-decoration: none; transition: color 0.3s; }
footer a:hover { color: #667eea; }
@media (max-width: 768px) {
  .cards { flex-direction: column; align-items: center; }
  .card { width: 90% !important; }
}
</style>""", unsafe_allow_html=True)

# Landing Page
if not st.session_state.get("accedido", False):
    st.markdown("<div class='landing-wrapper'>", unsafe_allow_html=True)
    # Hero section with centered title and subtitle inside gradient block
    st.markdown("<h1 style='text-align: center; margin-top: 40px;'>Bagui Copilot</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-top: 10px; margin-bottom: 30px; font-weight: bold;'>El mejor asistente para periodistas</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # Call to action button
    if st.button("Acceder", key="landing_acceder"):
        st.session_state.accedido = True
    st.markdown("<br>", unsafe_allow_html=True)
    # Features cards horizontal
    cards_html = """
    <div class='cards'>
      <div class='card'><h3>🎤 Transcripción</h3><p>Transcribe tus audios automáticamente.</p></div>
      <div class='card'><h3>✍️ Redacción</h3><p>Genera artículos con un solo clic.</p></div>
      <div class='card'><h3>🛠️ Personalización</h3><p>Adapta el estilo a tu voz única.</p></div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)
    # Footer links
    st.markdown("<footer>", unsafe_allow_html=True)
    st.markdown("<a href='#'>Ayuda</a> | <a href='#'>Acerca de</a> | <a href='#'>Términos & Privacidad</a>", unsafe_allow_html=True)
    st.markdown("</footer>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    login()
    st.stop()

usuario_actual = st.session_state.usuario

# Sidebar Navigation
st.sidebar.success(f"Sesión iniciada como: {usuario_actual}")

def transcribir_audio(audio_file):
    transcripcion = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcripcion.text

def cargar_estilo_predefinido():
    ruta = f"usuarios/{usuario_actual}/estilo_predefinido.txt"
    if not os.path.exists(ruta):
        return ""
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()

def remover_emojis(texto):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', texto)

def guardar_en_historial(texto, nombre):
    ruta = f"usuarios/{usuario_actual}/historial"
    os.makedirs(ruta, exist_ok=True)
    with open(os.path.join(ruta, nombre), "w", encoding="utf-8") as f:
        f.write(remover_emojis(texto))

def generar_articulo(transcripcion, muestras, tono, longitud, proposito, titulo):
    ruta_estilo = f"usuarios/{usuario_actual}/estilo_reforzado.json"
    ejemplos = []
    if os.path.exists(ruta_estilo):
        with open(ruta_estilo, "r", encoding="utf-8") as f:
            data = json.load(f)
            ejemplos = data[-2:]

    prompt = f"""
Eres un periodista profesional. A continuación tienes múltiples artículos de muestra, cada uno delimitado por líneas con “=== Muestra N ===”. Estudia estos ejemplos para reproducir su estilo y estructura:

{estilo_base}

--- Instrucciones ---
Título sugerido: {titulo}
Transcripción: "{transcripcion}"
Tono: {tono}
Longitud: {longitud}
Propósito: {proposito}

--- Artículo ---

"""
    respuesta = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return respuesta.choices[0].message.content

def generar_pdf(texto):
    texto = remover_emojis(texto)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Datos del encabezado
    autor = st.session_state.get("usuario", "Reportero IA")
    fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")

    # Encabezado superior
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"{autor}", ln=0, align="L")
    pdf.cell(0, 10, f"{fecha_actual}", ln=1, align="R")
    pdf.ln(5)

    # Título grande centrado
    pdf.set_font("Arial", "B", size=14)
    lineas = texto.split("\n")
    if lineas and lineas[0].startswith("#"):
        titulo = lineas[0].replace("#", "").strip()
        pdf.cell(0, 10, titulo, ln=True, align="C")
        pdf.ln(10)
        contenido = "\n".join(lineas[1:])
    else:
        contenido = texto

    # Cuerpo del artículo justificado
    pdf.set_font("Arial", size=12)
    for linea in contenido.split("\n"):
        pdf.multi_cell(0, 8, linea, align="J")

    return pdf.output(dest='S').encode('latin-1')

if "show_profile_menu" not in st.session_state:
    st.session_state.show_profile_menu = False

# Opciones principales como botones
if st.sidebar.button("📰 Generar artículo"):
    st.session_state.seccion = "📰 Generar artículo"
    st.session_state.show_profile_menu = False
if st.sidebar.button("👤 Perfil"):
    st.session_state.show_profile_menu = True

# Submenú de perfil
if st.session_state.show_profile_menu:
    with st.sidebar:
        st.markdown("---")
        if st.button("Historial"):
            st.session_state.seccion = "👤 Historial"
        if st.button("Editar estilo"):
            st.session_state.seccion = "👤 Editar estilo"
        if st.button("Datos de la cuenta"):
            st.session_state.seccion = "👤 Datos de la cuenta"

# Por defecto, si no hay sección seleccionada, mostrar Generar artículo
if "seccion" not in st.session_state:
    st.session_state.seccion = "📰 Generar artículo"

seccion = st.session_state.seccion

if seccion == "📰 Generar artículo":
    st.title("🧠 Asistente de Redacción con IA")
    st.write("Sube una nota de voz y genera automáticamente un artículo periodístico en tu estilo.")

    st.markdown("### 🎧 Sube tu archivo de audio")
    archivo_audio = st.file_uploader("🎤 Sube tu nota de voz (.m4a, .mp3, .wav)", type=["m4a", "mp3", "wav"])

    if archivo_audio:
        if "transcripcion" not in st.session_state:
            with st.spinner("🧾 Transcribiendo audio..."):
                transcripcion = transcribir_audio(archivo_audio)
                st.session_state["transcripcion"] = transcripcion

            with st.spinner("🏷️ Generando títulos sugeridos..."):
                estilo_base = cargar_estilo_predefinido()
                pattern = re.compile(r'^Título:\s*(.*)', flags=re.MULTILINE)
                titulos_ejemplo = pattern.findall(estilo_base)
                ejemplos_formateados = "\n".join(f"{t}" for t in titulos_ejemplo[:5])

                prompt_titulos = f"""
                    A continuación ejemplos de títulos de muestra:
                
                    {ejemplos_formateados}

                    Ahora, genera 5 títulos siguiendo este estilo para el siguiente texto:

                    {transcripcion}"""
                    
                respuesta_titulos = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_titulos}],
                    temperature=0.7
                )

                titulos = [t.strip() for t in respuesta_titulos.choices[0].message.content.split("\n") if t.strip()]
                st.session_state["titulos"] = titulos

        transcripcion = st.session_state["transcripcion"]
        titulos = st.session_state.get("titulos", [])
        estilo_base = cargar_estilo_predefinido()

        st.subheader("📝 Transcripción")
        st.write(transcripcion)

        st.subheader("🏷️ Selecciona un título y el estilo")
        titulo_sel = st.selectbox("Título", titulos)

        tono = st.selectbox("🗣️ Tono del artículo", ["Neutral", "Analítico", "Atractivo", "Emocional"])
        longitud_opcion = st.selectbox("📏 Longitud", ["Corta (100–300 palabras)", "Media (300–500 palabras)", "Larga (500–700 palabras)"])
        longitud = longitud_opcion.split()[0]
        proposito = st.selectbox("🎯 Propósito", ["Informar", "Educar", "Entretener", "Persuadir"])

        if st.button("✍️ Generar artículo"):
            with st.spinner("🛠️ Generando artículo..."):
                articulo = generar_articulo(transcripcion, estilo_base, tono, longitud, proposito, titulo_sel)
                st.session_state["articulo"] = articulo
                st.session_state["original"] = articulo
                st.session_state["fecha"] = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
                guardar_en_historial(articulo, f"{st.session_state['fecha']}.txt")
        
                if "articulo" in st.session_state:
                    pdf_bytes = generar_pdf(articulo)
                    st.download_button("📥 Descargar como PDF", data=pdf_bytes, file_name="articulo_generado.pdf", mime="application/pdf")

    if "articulo" in st.session_state:
        st.subheader("📄 Artículo Actual")
        titulo_vis = st.session_state.get('titulo', '')

        if titulo_vis:
            st.markdown(f"### {titulo_vis}", unsafe_allow_html=True)
        # Mostrar contenido completo
        st.markdown(st.session_state.articulo)

        pdf_bytes = generar_pdf(st.session_state["articulo"])
        st.download_button(
            "📥 Descargar PDF",
            data=pdf_bytes,
            file_name=f"{st.session_state.get('titulo','articulo')}.pdf",
            mime="application/pdf"
        )

        st.subheader("🔁 Reescribir artículo con un prompt personalizado")
        prompt_personalizado = st.text_area("Escribe aquí tu indicación para modificar el artículo: ")

        if st.button("🔄 Reescribir artículo"):
            with st.spinner("🧠 Reescribiendo..."):
                articulo = st.session_state.get("articulo", "")
                fecha = st.session_state.get("fecha", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
            
                prompt_reescritura = f"""
        Este es un artículo periodístico generado usando el estilo del periodista. Realiza las modificaciones siguientes: "{prompt_personalizado}"

        --- Artículo Original ---
        {articulo}

        --- Artículo Modificado ---
        """
                respuesta_nueva = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_reescritura}],
                    temperature=0.7
                )
                
                nuevo_articulo = respuesta_nueva.choices[0].message.content

                st.session_state["articulo_modificado"] = nuevo_articulo

                nuevo_pdf = generar_pdf(nuevo_articulo)
                st.download_button(
                    "📥 Descargar versión modificada",
                    data= nuevo_pdf,
                    file_name="articulo_modificado.pdf",
                    mime="application/pdf"
                )

if "articulo_modificado" in st.session_state:
    st.success("📝 Se ha generado una nueva versión modificada del artículo.")
    st.subheader("Vista previa de la nueva versión:")
    st.write(st.session_state["articulo_modificado"])

    if st.button("🔃 Aplicar cambios al artículo actual"):
        st.session_state["articulo"] = st.session_state["articulo_modificado"]
        del st.session_state["articulo_modificado"]
        st.success("✅ Cambios aplicados exitosamente.")

    if "original" in st.session_state and st.button("↩️ Restaurar versión original"):
        st.session_state["articulo"] = st.session_state["original"]
        st.success("✅ Artículo original restaurado.")

elif seccion == "👤 Historial":
    st.title("📚 Historial de Artículos")
    ruta_historial = f"usuarios/{usuario_actual}/historial"
    if not os.path.exists(ruta_historial):
        st.info("Aún no has generado ningún artículo.")
    else:
        archivos = sorted(os.listdir(ruta_historial), reverse=True)
        for archivo in archivos:
            with open(os.path.join(ruta_historial, archivo), "r", encoding="utf-8") as f:
                contenido = f.read()
            with st.expander(f"🗂 {archivo}"):
                st.write(contenido)

elif seccion == "👤 Editar estilo":
    st.title("✏️ Editor de Estilo de Redacción")
    ruta_muestras = f"usuarios/{usuario_actual}/muestras"
    os.makedirs(ruta_muestras, exist_ok=True)
    archivos = os.listdir(ruta_muestras)
    seleccion = st.selectbox("Selecciona un archivo para editar o crear uno nuevo", ["Nuevo..."] + archivos)
    if seleccion == "Nuevo...":
        nuevo_nombre = st.text_input("Nombre del nuevo archivo (ej: estilo1.txt)")
        if nuevo_nombre and not nuevo_nombre.endswith(".txt"):
            nuevo_nombre += ".txt"
        contenido_actual = ""
    else:
        nuevo_nombre = seleccion
        with open(os.path.join(ruta_muestras, seleccion), "r", encoding="utf-8") as f:
            contenido_actual = f.read()
    contenido_editado = st.text_area("Contenido del estilo", value=contenido_actual, height=300)
    if st.button("💾 Guardar"):
        with open(os.path.join(ruta_muestras, nuevo_nombre), "w", encoding="utf-8") as f:
            f.write(contenido_editado)
        st.success("Archivo guardado correctamente.")
    if seleccion != "Nuevo..." and st.button("🗑 Eliminar archivo"):
        os.remove(os.path.join(ruta_muestras, seleccion))
        st.warning("Archivo eliminado. Recarga la página para actualizar.")

elif seccion == "👤 Datos de la cuenta":
    st.title("👤 Datos de la cuenta")
    st.write("Aquí puedes actualizar tu contraseña.")
    usuarios = cargar_usuarios()
    contraseña_actual = st.text_input("Contraseña actual", type="password")
    nueva_contraseña = st.text_input("Nueva contraseña", type="password")
    if st.button("Guardar cambios"):
        if usuarios.get(usuario_actual) != contraseña_actual:
            st.error("Contraseña actual incorrecta")
        else:
            if nueva_contraseña:
                usuarios[st.session_state.usuario] = nueva_contraseña
                st.success("Contraseña actualizada")
            guardar_usuarios(usuarios)
            st.success("Datos de la cuenta actualizados con éxito.")