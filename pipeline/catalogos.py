"""Catálogos y jerarquías conceptuales usados para integrar las fuentes.

Resuelven conflictos de nombres entre fuentes: el SNIIM llama al producto
"Limón c/semilla # 5 - Primera" y el observatorio lo llama "limón".
"""

# Producto del SNIIM -> (insumo, tipo, canasta)   jerarquía: producto -> tipo -> canasta
PRODUCTOS_SNIIM = {
    "Limón c/semilla # 5 - Primera": ("limon", "fruta", "taquera"),
    "Aguacate Hass - Primera": ("aguacate", "fruta", "taquera"),
    "Tomate Saladette - Primera": ("tomate_saladette", "verdura", "taquera"),
    "Tomate Verde - Primera": ("tomate_verde", "verdura", "taquera"),
    "Cebolla Bola - Primera": ("cebolla", "verdura", "taquera"),
    "Chile Serrano - Primera": ("chile_serrano", "chile", "taquera"),
    "Chile Jalapeño - Primera": ("chile_jalapeno", "chile", "taquera"),
    "Papa Alpha - Primera": ("papa", "verdura", "taquera"),
}

# Mercado destino del SNIIM -> municipio (clave INEGI) del modelo de datos
MERCADOS_SNIIM = {
    "Colima: Centros de distribución de Colima": ("Colima", "06002"),
}

# Municipios del estado de Colima (clave INEGI: estado 06 + municipio 3 dígitos)
MUNICIPIOS = {
    "001": "Armería",
    "002": "Colima",
    "003": "Comala",
    "004": "Coquimatlán",
    "005": "Cuauhtémoc",
    "006": "Ixtlahuacán",
    "007": "Manzanillo",
    "008": "Minatitlán",
    "009": "Tecomán",
    "010": "Villa de Álvarez",
}

# Clase SCIAN del DENUE -> tipo de negocio del observatorio
TIPO_NEGOCIO = {
    "722514": "taqueria",
    "722515": "cafeteria",
    "722513": "antojitos",
    "722511": "restaurante_carta",
    "722512": "mariscos",
    "722517": "comida_rapida",
    "722516": "autoservicio",
    "722518": "otros_para_llevar",
    "722519": "otros_alimentos",
    "722320": "eventos",
    "722330": "unidades_moviles",
    "722310": "comedor_empresas",
    "722411": "centro_nocturno",
    "722412": "bar_cantina",
}

# Estrato (personas ocupadas) del DENUE -> tamaño (discretización por rangos del INEGI)
TAMANO = {
    "0 a 5 personas": "micro",
    "6 a 10 personas": "micro",
    "11 a 30 personas": "pequeno",
    "31 a 50 personas": "pequeno",
    "51 a 100 personas": "mediano",
    "101 a 250 personas": "mediano",
    "251 y más personas": "grande",
}

# Rango geográfico del estado de Colima (parte continental)
LATITUD = (18.6, 19.6)
LONGITUD = (-104.8, -103.4)

# Precio plausible por kilogramo en mercado mayorista (pesos)
PRECIO_KG = (1.0, 300.0)
