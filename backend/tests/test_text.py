from app.utils.text import chunk_text, content_hash, normalize_text


def test_normaliza_espacios_y_saltos():
    assert normalize_text("  Art.  1\r\n\r\n\r\nTexto  ") == "Art. 1\n\nTexto"


def test_huella_ignora_formato():
    assert content_hash("Ley 1\n\nTexto") == content_hash("Ley   1 Texto")


def test_huella_detecta_cambios_reales():
    assert content_hash("Ley 1 texto original") != content_hash("Ley 1 texto reformado")


def test_fragmenta_con_solapamiento():
    texto = " ".join(f"palabra{i}" for i in range(2000))
    chunks = chunk_text(texto, size=500, overlap=100)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    # el solapamiento mantiene continuidad: el inicio del segundo fragmento
    # aparece también al final del primero
    assert chunks[1].split(" ")[0] in chunks[0]


def test_fragmentacion_vacia():
    assert chunk_text("   ") == []


def test_parametros_invalidos():
    for size, overlap in ((0, 0), (100, 100), (100, -1)):
        try:
            chunk_text("texto", size=size, overlap=overlap)
        except ValueError:
            continue
        raise AssertionError(f"debía rechazar size={size} overlap={overlap}")
